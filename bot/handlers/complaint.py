"""Шаг 19 — Система жалоб.

Flow:
  Юзер в карточке поиска → «🚩 Пожаловаться» (report:<profile_id>)
  → выбор причины (complaint_reason_kb) → callback «complaint:<reason>:<profile_id>»
  → запись Complaint + автопауза анкеты при >=3 уникальных жалобщиков.

Защита:
  - Жалоба только на PUBLISHED анкеты (на удалённые/заблокированные — нельзя)
  - Нельзя жаловаться на свою анкету (defence in depth — UI прячет кнопку, бекенд проверяет)
  - Один reporter = одна активная жалоба на профиль (дубликаты отклоняются)

Автопауза:
  При достижении COMPLAINT_AUTOPAUSE_THRESHOLD уникальных жалобщиков
  анкета автоматически ставится на паузу. Модератор рассматривает
  жалобы через /complaints и либо подтверждает (анкета остаётся
  на паузе/блокируется), либо отклоняет (анкета автоматически
  возвращается в PUBLISHED, если не осталось активных жалоб).
"""

import logging

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy import select, func, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    User, Complaint, ComplaintReason, ComplaintStatus,
    Profile, ProfileStatus,
)
from bot.texts import t
from bot.keyboards.inline import nav_kb, add_nav
from bot.config import config
from bot.utils.safe_send import safe_send_message
from bot.utils.audit import audit

router = Router()
logger = logging.getLogger(__name__)

# Порог автопаузы: при стольких уникальных жалобщиках анкета
# автоматически ставится на паузу до рассмотрения модератором.
COMPLAINT_AUTOPAUSE_THRESHOLD = 3


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

    # Защита от жалобы на свою анкету (UI прячет, но на всякий случай)
    if profile and profile.user_id == callback.from_user.id:
        await callback.answer(
            "⚠️ Нельзя пожаловаться на свою анкету." if lang == "ru"
            else "⚠️ O'z anketangizga shikoyat qilib bo'lmaydi.",
            show_alert=True,
        )
        return

    # Защита: жалобы только на PUBLISHED анкеты
    if not profile or profile.status != ProfileStatus.PUBLISHED:
        await callback.answer(
            "⚠️ Анкета недоступна для жалоб." if lang == "ru"
            else "⚠️ Anketa shikoyat uchun mavjud emas.",
            show_alert=True,
        )
        return

    display_id = profile.display_id or "—"

    from bot.keyboards.inline import complaint_reason_kb
    await callback.message.answer(
        t("complaint_reason", lang, display_id=display_id),
        reply_markup=add_nav(complaint_reason_kb(profile_id, lang).inline_keyboard, lang, "back:menu"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("complaint:"))
async def submit_complaint(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Юзер выбрал причину жалобы — создаём запись + возможная автопауза."""
    parts = callback.data.split(":")
    reason_value = parts[1]
    profile_id = int(parts[2])

    lang = await get_lang(session, callback.from_user.id)
    reporter_id = callback.from_user.id

    profile = await session.get(Profile, profile_id)

    # Defence in depth: проверки на бекенде
    if not profile:
        await callback.answer("⚠️ Анкета не найдена.", show_alert=True)
        return
    if profile.user_id == reporter_id:
        await callback.answer(
            "⚠️ Нельзя пожаловаться на свою анкету." if lang == "ru"
            else "⚠️ O'z anketangizga shikoyat qilib bo'lmaydi.",
            show_alert=True,
        )
        return
    if profile.status != ProfileStatus.PUBLISHED:
        await callback.answer(
            "⚠️ Анкета недоступна для жалоб." if lang == "ru"
            else "⚠️ Anketa shikoyat uchun mavjud emas.",
            show_alert=True,
        )
        return

    # Duplicate-check: один reporter = одна живая жалоба на профиль
    existing_q = await session.execute(
        select(Complaint).where(
            Complaint.reporter_user_id == reporter_id,
            Complaint.profile_id == profile_id,
            Complaint.status != ComplaintStatus.DISMISSED,
        ).limit(1)
    )
    if existing_q.scalar_one_or_none() is not None:
        await callback.answer(
            "⚠️ Вы уже подавали жалобу на эту анкету." if lang == "ru"
            else "⚠️ Siz bu anketaga allaqachon shikoyat yuborgansiz.",
            show_alert=True,
        )
        return

    # Создаём жалобу
    complaint = Complaint(
        reporter_user_id=reporter_id,
        profile_id=profile_id,
        reason=ComplaintReason(reason_value),
    )
    session.add(complaint)
    await session.commit()

    # Автопауза: посчитать уникальных жалобщиков (не DISMISSED)
    count_q = await session.execute(
        select(func.count(distinct(Complaint.reporter_user_id)))
        .where(
            Complaint.profile_id == profile_id,
            Complaint.status != ComplaintStatus.DISMISSED,
        )
    )
    unique_reporters = count_q.scalar() or 0

    auto_paused_now = False
    if (unique_reporters >= COMPLAINT_AUTOPAUSE_THRESHOLD
            and profile.status == ProfileStatus.PUBLISHED):
        profile.status = ProfileStatus.PAUSED
        profile.is_active = False
        profile.auto_paused_by_complaints = True
        await session.commit()
        auto_paused_now = True
        audit(
            "profile_auto_paused",
            actor="system",
            target=f"user:{profile.user_id}" if profile.user_id else None,
            profile_id=profile.id,
            display_id=profile.display_id,
            unique_reporters=unique_reporters,
        )
        # Уведомление владельцу анкеты
        try:
            owner_lang = "ru"
            owner_q = await session.execute(select(User).where(User.id == profile.user_id))
            owner = owner_q.scalar_one_or_none()
            if owner and owner.language:
                owner_lang = owner.language.value
        except Exception as _e:
            logger.debug("ignored: %s", _e)
            owner_lang = "ru"

        display_id = profile.display_id or "—"
        if owner_lang == "uz":
            owner_msg = (
                f"🚫 <b>Anketangiz avtomatik pauzaga qo'yildi</b>\n\n"
                f"🔖 {display_id}\n\n"
                f"Anketaga {COMPLAINT_AUTOPAUSE_THRESHOLD} ta shikoyat tushdi.\n"
                f"Moderator har birini ko'rib chiqadi va tez orada qaror qabul qiladi.\n\n"
                f"Agar shikoyatlar asossiz bo'lsa — anketa avtomatik qidirishga qaytadi."
            )
        else:
            owner_msg = (
                f"🚫 <b>Ваша анкета автоматически приостановлена</b>\n\n"
                f"🔖 {display_id}\n\n"
                f"На анкету поступило {COMPLAINT_AUTOPAUSE_THRESHOLD} жалобы.\n"
                f"Модератор рассмотрит каждую и примет решение в ближайшее время.\n\n"
                f"Если жалобы окажутся необоснованными — анкета автоматически\n"
                f"вернётся в поиск."
            )
        if profile.user_id:
            await safe_send_message(
                bot, profile.user_id, owner_msg,
                parse_mode="HTML",
                label="autopause_notify_owner",
            )

    # Ответ юзеру (UI)
    from aiogram.types import InlineKeyboardMarkup
    await callback.message.edit_text(
        t("complaint_submitted", lang),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb(lang, show_back=False)),
    )

    # Адресный пуш: модератор обжалованной анкеты
    from bot.services.moderator_routing import resolve_primary_moderator
    from bot.config import config as _cfg
    reason_labels = {
        "wrong_data": "❗ Данные не соответствуют",
        "suspicious": "🤖 Подозрительная / фейковая",
        "stolen_photo": "📸 Чужое фото",
        "bad_behavior": "⚠️ Некорректное поведение",
        "other": "📵 Другая причина",
    }
    autopause_note = (
        f"\n\n🚫 <b>АВТОПАУЗА:</b> {unique_reporters} уникальных жалобщиков — анкета поставлена на паузу."
        if auto_paused_now else ""
    )
    mod_text = (
        f"🚩 <b>НОВАЯ ЖАЛОБА</b>\n\n"
        f"🔖 Анкета: {profile.display_id or '—'}\n"
        f"От: @{callback.from_user.username or '—'} (ID: {reporter_id})\n"
        f"Причина: {reason_labels.get(reason_value, reason_value)}\n"
        f"Жалобщиков всего: {unique_reporters}"
        f"{autopause_note}"
    )
    mod_id = resolve_primary_moderator(profile)["telegram_id"] if profile else _cfg.mod_tashkent_id
    await safe_send_message(bot, mod_id, mod_text, parse_mode="HTML", label="complaint_to_mod")

    await callback.answer()
