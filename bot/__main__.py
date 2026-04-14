import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import config
from bot.db.engine import engine
from bot.db.models import Base
from bot.middlewares.db import DbSessionMiddleware
from bot.handlers import start, menu, questionnaire, tariff, moderator, search, payment, meeting, feedback, complaint

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def on_startup(bot: Bot, scheduler: AsyncIOScheduler):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ensured")

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
