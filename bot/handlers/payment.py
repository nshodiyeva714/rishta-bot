"""Шаг 13-15 — Оплата и получение контактов."""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    User, Profile, Payment, PaymentMethod, PaymentStatus,
    ProfileType, ContactRequest, RequestStatus,
)
from bot.states import PaymentStates, MeetingStates
from bot.texts import t
from bot.keyboards.inline import (
    payment_uz_kb, payment_cis_kb, payment_intl_kb,
    mod_payment_kb, meeting_skip_kb, back_kb,
)
from bot.config import config
from bot.utils.helpers import format_anketa_private

router = Router()


async def get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


async def send_contact_details(bot: Bot, session: AsyncSession, user_id: int, profile: Profile):
    """Шаг 15 — Отправить контакты и адрес пользователю."""
    lang = await get_lang(session, user_id)

    # Подтверждение оплаты — тёплый текст
    display_id = profile.display_id or "—"
    if lang == "uz":
        confirm_text = (
            f"✅ <b>To'lov tasdiqlandi!</b>\n\n"
            f"🔖 {display_id}\n\n"
            f"Bu uchrashuv baxtning boshlanishi bo'lsin! 🤲"
        )
    else:
        confirm_text = (
            f"✅ <b>Оплата подтверждена!</b>\n\n"
            f"🔖 {display_id}\n\n"
            f"Пусть эта встреча станет\n"
            f"началом счастья! 🤲"
        )
    await bot.send_message(user_id, confirm_text)

    # Контакты и адрес
    private_text = format_anketa_private(profile, lang)
    await bot.send_message(user_id, private_text)

    # Фото если есть
    if profile.photo_file_id:
        try:
            await bot.send_photo(user_id, profile.photo_file_id,
                caption="📸 Фото кандидата\n🔒 Защищено от скриншотов" if lang == "ru"
                else "📸 Nomzodning fotosurati\n🔒 Skrinshotdan himoyalangan"
            )
        except Exception:
            pass

    # Предупреждение
    warn_text = (
        "⚠️ Просим сохранять уважение к семье и конфиденциальность.\n\n"
        "Модератор предупредил семью о вашем визите 🤝\n\n"
        "Удачи! Пусть всё сложится наилучшим образом 🤲\n\n"
        "<i>Через 14 дней спросим о результате 😊</i>"
    ) if lang == "ru" else (
        "⚠️ Oilaga hurmat va maxfiylikni saqlashingizni so'raymiz.\n\n"
        "Moderator oilani tashrifingiz haqida ogohlantirdi 🤝\n\n"
        "Omad! Hammasi yaxshi bo'lsin 🤲\n\n"
        "<i>14 kundan so'ng natija haqida so'raymiz 😊</i>"
    )
    await bot.send_message(user_id, warn_text)

    # Предлагаем запланировать встречу (Шаг 16)
    await bot.send_message(
        user_id,
        t("meeting_date", lang),
        reply_markup=meeting_skip_kb(lang),
    )

    # Обновляем статус запроса
    result = await session.execute(
        select(ContactRequest).where(
            ContactRequest.requester_user_id == user_id,
            ContactRequest.target_profile_id == profile.id,
        ).limit(1)
    )
    cr = result.scalar_one_or_none()
    if cr:
        cr.status = RequestStatus.CONTACT_GIVEN
        await session.commit()


# ── Шаг 13: Выбор способа оплаты ──
@router.callback_query(F.data.startswith("pay:"))
async def choose_payment(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    method = parts[1]
    profile_id = int(parts[2])

    lang = await get_lang(session, callback.from_user.id)

    if method == "card":
        # Перевод на карту — показываем реквизиты
        # Определяем сумму по региону пользователя
        result = await session.execute(
            select(Profile).where(Profile.user_id == callback.from_user.id).limit(1)
        )
        user_profile = result.scalar_one_or_none()
        residence = user_profile.residence_status.value if user_profile and user_profile.residence_status else "uzbekistan"
        amount = 30000_00  # 30,000 сум
        await state.update_data(pay_profile_id=profile_id, pay_method="card_transfer", pay_amount=amount, lang=lang)
        await callback.message.edit_text(t("payment_card_transfer", lang))
        await state.set_state(PaymentStates.awaiting_screenshot)
    elif method == "moderator":
        # Через модератора
        region = "🇺🇿 Узбекистан"
        moderator = config.moderator_tashkent
        hours = "08:00–00:00"
        await callback.message.edit_text(
            t("contact_moderator", lang, region=region, moderator=moderator, hours=hours),
            reply_markup=back_kb(lang),
        )
    elif method in ("payme", "click", "uzum", "stripe"):
        # Эти методы больше не доступны — направляем к карте
        await callback.message.edit_text(t("payment_card_transfer", lang))
        await state.update_data(pay_profile_id=profile_id, pay_method="card_transfer", pay_amount=30000_00, lang=lang)
        await state.set_state(PaymentStates.awaiting_screenshot)

    await callback.answer()


# ── Шаг 14: Скриншот оплаты ──
@router.message(PaymentStates.awaiting_screenshot, F.photo)
async def payment_screenshot(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    profile_id = data.get("pay_profile_id")
    lang = data.get("lang", "ru")

    photo = message.photo[-1]

    payment = Payment(
        user_id=message.from_user.id,
        profile_id=profile_id,
        amount=30000_00,
        currency="UZS",
        method=PaymentMethod.CARD_TRANSFER,
        status=PaymentStatus.PENDING,
        screenshot_file_id=photo.file_id,
    )
    session.add(payment)
    await session.commit()

    profile = await session.get(Profile, profile_id) if profile_id else None

    # Отправляем всем модераторам
    from bot.config import get_all_moderator_ids
    mod_text = t("mod_payment_manual", "ru",
        username=message.from_user.username or "—",
        user_id=message.from_user.id,
        display_id=profile.display_id if profile else "—",
        amount="30,000 сум",
    )
    for mod_id in get_all_moderator_ids():
        try:
            await bot.send_message(mod_id, mod_text, reply_markup=mod_payment_kb(payment.id))
            await bot.send_photo(mod_id, photo.file_id)
        except Exception:
            pass

    await message.answer(
        "✅ Скриншот отправлен модератору.\nОжидайте подтверждения оплаты." if lang == "ru"
        else "✅ Skrinshot moderatorga yuborildi.\nTo'lovni tasdiqlashni kuting."
    )
    # Не очищаем state — оплата ещё не подтверждена.
    # Модератор подтвердит → send_contact_details → meeting flow
    await state.clear()


@router.message(PaymentStates.awaiting_screenshot)
async def payment_screenshot_invalid(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = "📸 Пожалуйста, отправьте скриншот оплаты (фото)." if lang == "ru" else "📸 Iltimos, to'lov skrinshotini (foto) yuboring."
    await message.answer(text)
