"""Шаг 19 — Система жалоб."""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, Complaint, ComplaintReason, Profile
from bot.texts import t
from bot.keyboards.inline import nav_kb, add_nav
from bot.config import config

router = Router()


async def get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


@router.callback_query(F.data.startswith("report:"))
async def report_profile(callback: CallbackQuery, session: AsyncSession):
    """Показать меню жалобы."""
    profile_id = int(callback.data.split(":")[1])
    lang = await get_lang(session, callback.from_user.id)

    profile = await session.get(Profile, profile_id)
    display_id = profile.display_id if profile else "—"

    from bot.keyboards.inline import complaint_reason_kb
    await callback.message.answer(
        t("complaint_reason", lang, display_id=display_id),
        reply_markup=add_nav(complaint_reason_kb(profile_id, lang).inline_keyboard, lang, "back:menu"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("complaint:"))
async def submit_complaint(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Пользователь выбрал причину жалобы."""
    parts = callback.data.split(":")
    reason_value = parts[1]
    profile_id = int(parts[2])

    lang = await get_lang(session, callback.from_user.id)

    complaint = Complaint(
        reporter_user_id=callback.from_user.id,
        profile_id=profile_id,
        reason=ComplaintReason(reason_value),
    )
    session.add(complaint)
    await session.commit()

    from aiogram.types import InlineKeyboardMarkup
    await callback.message.edit_text(
        t("complaint_submitted", lang),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb(lang, show_back=False)),
    )

    # Адресный пуш: модератор обжалованной анкеты
    from bot.services.moderator_routing import resolve_primary_moderator
    from bot.config import config as _cfg
    profile = await session.get(Profile, profile_id)
    reason_labels = {
        "wrong_data": "❗ Данные не соответствуют",
        "suspicious": "🤖 Подозрительная / фейковая",
        "stolen_photo": "📸 Чужое фото",
        "bad_behavior": "⚠️ Некорректное поведение",
        "other": "📵 Другая причина",
    }
    mod_text = (
        f"🚩 <b>НОВАЯ ЖАЛОБА</b>\n\n"
        f"🔖 Анкета: {profile.display_id if profile else '—'}\n"
        f"От: @{callback.from_user.username or '—'} (ID: {callback.from_user.id})\n"
        f"Причина: {reason_labels.get(reason_value, reason_value)}"
    )
    mod_id = resolve_primary_moderator(profile)["telegram_id"] if profile else _cfg.mod_tashkent_id
    try:
        await bot.send_message(mod_id, mod_text)
    except Exception:
        pass

    await callback.answer()
