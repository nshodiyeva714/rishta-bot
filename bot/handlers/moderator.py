"""Шаг 9 — Модератор: проверка анкет и оплат."""

from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Profile, ProfileStatus, Payment, PaymentStatus
from bot.texts import t
from bot.config import config

router = Router()


@router.callback_query(F.data.startswith("mod:publish:"))
async def mod_publish(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор публикует анкету."""
    if callback.from_user.id != config.moderator_chat_id:
        await callback.answer("⛔ Нет доступа")
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена")
        return

    profile.status = ProfileStatus.PUBLISHED
    profile.published_at = datetime.now()
    await session.commit()

    # Уведомляем пользователя
    try:
        lang = "ru"  # По умолчанию; можно достать из User
        from sqlalchemy import select
        from bot.db.models import User
        result = await session.execute(select(User).where(User.id == profile.user_id))
        user = result.scalar_one_or_none()
        if user and user.language:
            lang = user.language.value

        await bot.send_message(
            profile.user_id,
            t("mod_profile_published", lang, display_id=profile.display_id),
        )
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ ОПУБЛИКОВАНО",
    )
    await callback.answer("✅ Опубликовано")


@router.callback_query(F.data.startswith("mod:reject:"))
async def mod_reject(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор отклоняет анкету."""
    if callback.from_user.id != config.moderator_chat_id:
        await callback.answer("⛔ Нет доступа")
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена")
        return

    profile.status = ProfileStatus.REJECTED
    await session.commit()

    try:
        lang = "ru"
        from sqlalchemy import select
        from bot.db.models import User
        result = await session.execute(select(User).where(User.id == profile.user_id))
        user = result.scalar_one_or_none()
        if user and user.language:
            lang = user.language.value

        await bot.send_message(
            profile.user_id,
            t("mod_profile_rejected", lang, display_id=profile.display_id),
        )
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ ОТКЛОНЕНО",
    )
    await callback.answer("❌ Отклонено")


@router.callback_query(F.data.startswith("mod:reject_photo:"))
async def mod_reject_photo(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор отклоняет фото."""
    if callback.from_user.id != config.moderator_chat_id:
        await callback.answer("⛔ Нет доступа")
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена")
        return

    profile.photo_file_id = None
    from bot.db.models import PhotoType
    profile.photo_type = PhotoType.NONE
    await session.commit()

    try:
        await bot.send_message(
            profile.user_id,
            "📸 Модератор отклонил фото в анкете " + (profile.display_id or "") +
            ". Пожалуйста, загрузите другое фото через «Редактировать анкету».",
        )
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + "\n\n📸 ФОТО ОТКЛОНЕНО",
    )
    await callback.answer("📸 Фото отклонено")


# ── Подтверждение оплаты модератором ──
@router.callback_query(F.data.startswith("modpay:confirm:"))
async def mod_confirm_payment(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if callback.from_user.id != config.moderator_chat_id:
        await callback.answer("⛔ Нет доступа")
        return

    payment_id = int(callback.data.split(":")[2])
    payment = await session.get(Payment, payment_id)
    if not payment:
        await callback.answer("Оплата не найдена")
        return

    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_at = datetime.now()
    await session.commit()

    # Отправляем контакты пользователю
    profile = await session.get(Profile, payment.profile_id)
    if profile:
        from bot.handlers.payment import send_contact_details
        await send_contact_details(bot, session, payment.user_id, profile)

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ ОПЛАТА ПОДТВЕРЖДЕНА",
    )
    await callback.answer("✅ Подтверждено")


@router.callback_query(F.data.startswith("modpay:reject:"))
async def mod_reject_payment(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if callback.from_user.id != config.moderator_chat_id:
        await callback.answer("⛔ Нет доступа")
        return

    payment_id = int(callback.data.split(":")[2])
    payment = await session.get(Payment, payment_id)
    if not payment:
        await callback.answer("Оплата не найдена")
        return

    payment.status = PaymentStatus.REJECTED
    await session.commit()

    try:
        await bot.send_message(
            payment.user_id,
            "❌ Оплата отклонена модератором. Свяжитесь с модератором для уточнения.",
        )
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ ОПЛАТА ОТКЛОНЕНА",
    )
    await callback.answer("❌ Отклонено")
