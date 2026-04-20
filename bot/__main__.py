import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeChat, MenuButtonCommands
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import config
from bot.db.engine import engine
from bot.db.models import Base
from bot.middlewares.db import DbSessionMiddleware
from bot.handlers import start, menu, questionnaire, questionnaire_ext, tariff, moderator, search, payment, meeting, feedback, complaint, fallback

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
        try:
            await conn.execute(text(
                "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS body_type VARCHAR(20)"
            ))
        except Exception:
            pass
        try:
            await conn.execute(text(
                "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS city_code VARCHAR(50)"
            ))
        except Exception:
            pass
        try:
            await conn.execute(text(
                "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS country VARCHAR(50)"
            ))
        except Exception:
            pass
        try:
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS seen_favorites_count INTEGER DEFAULT 0"
            ))
        except Exception:
            pass
        try:
            await conn.execute(text(
                "ALTER TABLE contact_requests ADD COLUMN IF NOT EXISTS display_id VARCHAR(20)"
            ))
        except Exception:
            pass
        # VIP: гарантируем, что колонки существуют на старых prod-инстансах
        try:
            await conn.execute(text(
                "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS vip_status VARCHAR(20) DEFAULT 'none'"
            ))
        except Exception:
            pass
        try:
            await conn.execute(text(
                "ALTER TABLE profiles ADD COLUMN IF NOT EXISTS vip_expires_at TIMESTAMP"
            ))
        except Exception:
            pass

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🗑 ONE-TIME MIGRATION — REMOVE IN FOLLOW-UP COMMIT
        # Retroactive PII cleanup for past DELETED profiles.
        # Mirrors _soft_delete_profile() in bot/handlers/menu.py.
        # Idempotent: WHERE clause skips rows already cleaned.
        # After logs confirm it ran (cleaned N → next restart shows 0),
        # delete this block and keep only the _soft_delete_profile path.
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        try:
            result = await conn.execute(text("""
                UPDATE profiles
                SET photo_file_id = NULL,
                    photo_type = 'none',
                    parent_phone = NULL,
                    parent_telegram = NULL,
                    candidate_telegram = NULL,
                    address = NULL,
                    location_lat = NULL,
                    location_lon = NULL,
                    location_link = NULL,
                    health_notes = NULL
                WHERE status = 'deleted'
                  AND (
                    photo_file_id IS NOT NULL OR
                    parent_phone IS NOT NULL OR
                    parent_telegram IS NOT NULL OR
                    candidate_telegram IS NOT NULL OR
                    address IS NOT NULL OR
                    location_lat IS NOT NULL OR
                    location_lon IS NOT NULL OR
                    location_link IS NOT NULL OR
                    health_notes IS NOT NULL OR
                    photo_type IS DISTINCT FROM 'none'
                  )
            """))
            cleaned = result.rowcount if result.rowcount is not None else -1
            if cleaned > 0:
                logger.info(f"[PII-cleanup] cleaned {cleaned} past DELETED profiles")
            elif cleaned == 0:
                logger.info("[PII-cleanup] nothing to clean (idempotent no-op)")
            else:
                logger.info("[PII-cleanup] executed (rowcount unavailable)")
        except Exception as e:
            logger.error(f"[PII-cleanup] skipped: {e}")
    logger.info("Database tables ensured")

    # Команды для обычных пользователей
    user_commands = [
        BotCommand(command="start", description="Главное меню / Bosh menyu"),
    ]
    await bot.set_my_commands(user_commands)

    # Команды для модераторов (расширенные)
    mod_commands = [
        BotCommand(command="start",    description="Главное меню"),
        BotCommand(command="ankety",   description="Анкеты на проверке"),
        BotCommand(command="requests", description="Активные запросы контакта"),
        BotCommand(command="vip",      description="VIP-заявки"),
        BotCommand(command="find",     description="Найти анкету по номеру"),
        BotCommand(command="stats",    description="Статистика"),
    ]
    from bot.config import get_all_moderator_ids
    for mod_id in get_all_moderator_ids():
        try:
            await bot.set_my_commands(mod_commands, scope=BotCommandScopeChat(chat_id=mod_id))
        except Exception as e:
            logger.warning(f"Не удалось установить команды модератору {mod_id}: {e}")

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

    # Логируем необработанные callback
    from aiogram.types import CallbackQuery as _CQ

    @dp.errors()
    async def on_error(event, exception):
        logger.error(f"Unhandled error: {exception}", exc_info=True)

    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(questionnaire.router)
    dp.include_router(questionnaire_ext.router)
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
