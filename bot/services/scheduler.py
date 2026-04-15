"""Шаг 17, 18, 20 — Планировщик: обратная связь, напоминания, дневной отчёт."""

import logging
from datetime import datetime, timedelta

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, func

from bot.config import config
from bot.db.engine import async_session
from bot.db.models import (
    Profile, ProfileStatus, VipStatus, Payment, PaymentStatus,
    Complaint, ComplaintStatus, Favorite, ContactRequest,
    Feedback, FeedbackResult, User,
)
from bot.texts import t
from bot.keyboards.inline import feedback_kb, reminder_kb

logger = logging.getLogger(__name__)


def setup_scheduled_jobs(scheduler: AsyncIOScheduler, bot: Bot):
    """Регистрация периодических задач."""
    # Дневной отчёт модератору в 20:00
    scheduler.add_job(
        daily_report,
        "cron",
        hour=20,
        minute=0,
        args=[bot],
        id="daily_report",
        replace_existing=True,
    )

    # Напоминание об обновлении анкеты (каждый день в 10:00)
    scheduler.add_job(
        send_30day_reminders,
        "cron",
        hour=10,
        minute=0,
        args=[bot],
        id="30day_reminders",
        replace_existing=True,
    )

    # Обратная связь через 14 дней (каждый день в 12:00)
    scheduler.add_job(
        send_14day_feedback,
        "cron",
        hour=12,
        minute=0,
        args=[bot],
        id="14day_feedback",
        replace_existing=True,
    )

    # Проверка VIP-статусов (каждый день в 00:00)
    scheduler.add_job(
        check_vip_expiry,
        "cron",
        hour=0,
        minute=0,
        args=[bot],
        id="vip_expiry",
        replace_existing=True,
    )

    logger.info("Запланировано: дневной отчёт, напоминания, обратная связь, VIP")


async def daily_report(bot: Bot):
    """Шаг 20 — Дневной отчёт модератору."""
    if not config.moderator_chat_id:
        return

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    async with async_session() as session:
        # Оплаты за сегодня
        result = await session.execute(
            select(func.count(Payment.id)).where(
                Payment.created_at >= today,
                Payment.status == PaymentStatus.CONFIRMED,
            )
        )
        payments_count = result.scalar() or 0

        result = await session.execute(
            select(func.sum(Payment.amount)).where(
                Payment.created_at >= today,
                Payment.status == PaymentStatus.CONFIRMED,
            )
        )
        payments_total_raw = result.scalar() or 0
        # amount хранится в тийинах — конвертируем в сум
        payments_total = f"{payments_total_raw // 100:,} сум" if payments_total_raw else "0"

        # Новые анкеты
        result = await session.execute(
            select(func.count(Profile.id)).where(Profile.created_at >= today)
        )
        new_profiles = result.scalar() or 0

        # Просмотры
        result = await session.execute(
            select(func.sum(Profile.views_count)).where(Profile.status == ProfileStatus.PUBLISHED)
        )
        total_views = result.scalar() or 0

        # Жалобы
        result = await session.execute(
            select(func.count(Complaint.id)).where(
                Complaint.created_at >= today,
                Complaint.status == ComplaintStatus.PENDING,
            )
        )
        complaints = result.scalar() or 0

        # Избранное
        result = await session.execute(
            select(func.count(Favorite.id)).where(Favorite.created_at >= today)
        )
        favorites = result.scalar() or 0

    date_str = today.strftime("%d.%m.%Y")
    report_text = t("daily_report", "ru",
        date=date_str,
        payments_count=payments_count,
        payments_total=payments_total,
        new_profiles=new_profiles,
        total_views=total_views,
        complaints=complaints,
        favorites=favorites,
    )

    try:
        await bot.send_message(config.moderator_chat_id, report_text)
    except Exception as e:
        logger.error(f"Ошибка отправки дневного отчёта: {e}")


async def send_30day_reminders(bot: Bot):
    """Шаг 18 — Напоминание через 30 дней."""
    threshold = datetime.now() - timedelta(days=30)

    async with async_session() as session:
        result = await session.execute(
            select(Profile).where(
                Profile.status == ProfileStatus.PUBLISHED,
                Profile.is_active == True,
                Profile.published_at <= threshold,
                (Profile.last_reminder_at == None) | (Profile.last_reminder_at <= threshold),
            )
        )
        profiles = result.scalars().all()

        for profile in profiles:
            # Определяем язык пользователя
            user_result = await session.execute(select(User).where(User.id == profile.user_id))
            user = user_result.scalar_one_or_none()
            lang = user.language.value if user and user.language else "ru"

            try:
                await bot.send_message(
                    profile.user_id,
                    t("reminder_30d", lang, display_id=profile.display_id or "—"),
                    reply_markup=reminder_kb(profile.id, lang),
                )
                profile.last_reminder_at = datetime.now()
            except Exception as e:
                logger.error(f"Ошибка отправки напоминания {profile.display_id}: {e}")

        await session.commit()


async def send_14day_feedback(bot: Bot):
    """Шаг 17 — Обратная связь через 14 дней после получения контакта."""
    threshold = datetime.now() - timedelta(days=14)

    async with async_session() as session:
        # Находим оплаченные контакты, по которым ещё нет обратной связи
        result = await session.execute(
            select(Payment).where(
                Payment.status == PaymentStatus.CONFIRMED,
                Payment.confirmed_at != None,
                Payment.confirmed_at <= threshold,
            )
        )
        payments = result.scalars().all()

        for payment in payments:
            # Проверяем, есть ли уже обратная связь
            fb_result = await session.execute(
                select(Feedback).where(
                    Feedback.user_id == payment.user_id,
                    Feedback.profile_id == payment.profile_id,
                )
            )
            existing = fb_result.scalar_one_or_none()
            if existing:
                continue

            profile = await session.get(Profile, payment.profile_id)
            if not profile:
                continue

            user_result = await session.execute(select(User).where(User.id == payment.user_id))
            user = user_result.scalar_one_or_none()
            lang = user.language.value if user and user.language else "ru"

            try:
                await bot.send_message(
                    payment.user_id,
                    t("feedback_ask", lang, display_id=profile.display_id or "—"),
                    reply_markup=feedback_kb(profile.id, lang),
                )
            except Exception as e:
                logger.error(f"Ошибка отправки запроса обратной связи: {e}")


async def check_vip_expiry(bot: Bot):
    """Проверка истечения VIP-статуса."""
    now = datetime.now()

    async with async_session() as session:
        result = await session.execute(
            select(Profile).where(
                Profile.vip_status == VipStatus.ACTIVE,
                Profile.vip_expires_at != None,
                Profile.vip_expires_at <= now,
            )
        )
        profiles = result.scalars().all()

        for profile in profiles:
            profile.vip_status = VipStatus.EXPIRED

            try:
                await bot.send_message(
                    profile.user_id,
                    f"⭐ VIP-статус анкеты {profile.display_id} истёк. "
                    f"Обновите через «Мои заявки» → «Перейти на VIP».",
                )
            except Exception:
                pass

        await session.commit()
