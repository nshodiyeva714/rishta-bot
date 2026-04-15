import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, MenuButtonCommands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import config
from bot.db.engine import engine
from bot.db.models import Base
from bot.middlewares.db import DbSessionMiddleware
from bot.handlers import start, menu, questionnaire, tariff, moderator, search, payment, meeting, feedback, complaint, fallback

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, scheduler: AsyncIOScheduler):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Миграция: добавить anketa_lang если нет
        from sqlalchemy import text
        try:
            await conn.execute(text(
                "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS anketa_lang VARCHAR(5) DEFAULT 'ru'"
            ))
        except Exception:
            pass  # Колонка уже существует или БД не поддерживает IF NOT EXISTS
    logger.info("Database tables ensured")

    # Устанавливаем команды бота (кнопка Меню в Telegram)
    await bot.set_my_commands([
        BotCommand(command="start", description="Главное меню / Bosh menyu"),
    ])
    await bot.set_chat_menu_button(menu_button=MenuButtonCommands())
    logger.info("Bot commands set")

    from bot.services.scheduler import setup_scheduled_jobs
    setup_scheduled_jobs(scheduler, bot)
    scheduler.start()
    logger.info("Scheduler started")


async def main():
    bot = Bot(token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(questionnaire.router)
    dp.include_router(tariff.router)
    dp.include_router(moderator.router)
    dp.include_router(search.router)
    dp.include_router(payment.router)
    dp.include_router(meeting.router)
    dp.include_router(feedback.router)
    dp.include_router(complaint.router)
    dp.include_router(fallback.router)  # Должен быть последним!

    scheduler = AsyncIOScheduler()
    await on_startup(bot, scheduler)

    logger.info("Bot starting polling...")
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
