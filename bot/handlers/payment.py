"""Шаг 13-15 — Оплата и получение контактов."""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    User, Profile, Payment, PaymentMethod, PaymentStatus,
    ProfileType, ContactRequest, RequestStatus,
    VipRequest, VipRequestStatus, VipPaymentMethod,
)
from bot.states import PaymentStates, MeetingStates, VipPaymentStates
from bot.texts import t
from bot.keyboards.inline import (
    payment_uz_kb, payment_cis_kb, payment_intl_kb,
    mod_payment_kb, meeting_skip_kb, back_main_kb,
    main_menu_kb, nav_kb,
    vip_duration_kb, vip_method_kb, vip_pay_card_kb,
    _vip_price_for, _fmt_price, VIP_DURATIONS,
)
from bot.config import config, get_all_moderator_ids
from bot.utils.helpers import format_anketa_private
from sqlalchemy import func
import logging
logger = logging.getLogger(__name__)

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
        await callback.message.edit_text(
            t("payment_card_transfer", lang),
            reply_markup=back_main_kb(lang),
        )
        await state.set_state(PaymentStates.awaiting_screenshot)
    elif method == "moderator":
        # Через модератора
        region = "🇺🇿 Узбекистан"
        moderator = config.moderator_tashkent
        hours = "08:00–00:00"
        await callback.message.edit_text(
            t("contact_moderator", lang, region=region, moderator=moderator, hours=hours),
            reply_markup=back_main_kb(lang),
        )
    elif method in ("payme", "click", "uzum", "stripe"):
        # Эти методы больше не доступны — направляем к карте
        await callback.message.edit_text(
            t("payment_card_transfer", lang),
            reply_markup=back_main_kb(lang),
        )
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

    from aiogram.types import InlineKeyboardMarkup
    await message.answer(
        "✅ Скриншот отправлен модератору.\nОжидайте подтверждения оплаты." if lang == "ru"
        else "✅ Skrinshot moderatorga yuborildi.\nTo'lovni tasdiqlashni kuting.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb(lang, show_back=False)),
    )
    # Не очищаем state — оплата ещё не подтверждена.
    # Модератор подтвердит → send_contact_details → meeting flow
    await state.clear()


@router.message(PaymentStates.awaiting_screenshot)
async def payment_screenshot_invalid(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = "📸 Пожалуйста, отправьте скриншот оплаты (фото)." if lang == "ru" else "📸 Iltimos, to'lov skrinshotini (foto) yuboring."
    await message.answer(text, reply_markup=back_main_kb(lang))


# ══════════════════════════════════════════════════════════
#  VIP flow: duration → method → pay (self/moderator) → confirm
# ══════════════════════════════════════════════════════════

def _days_label(days: int, lang: str) -> str:
    for d, labels in VIP_DURATIONS:
        if d == days:
            return labels.get(lang, str(days))
    return str(days)


async def _generate_vip_display_id(session: AsyncSession) -> str:
    """VIP-NNN — порядковый номер VipRequest."""
    count_result = await session.execute(select(func.count(VipRequest.id)))
    count = count_result.scalar() or 0
    return f"VIP-{count + 1:03d}"


async def _notify_mods_new_vip_request(bot: Bot, req: VipRequest, profile: Profile, username_or_id: str):
    """Пуш всем модераторам о новой VIP-заявке."""
    days_label_ru = _days_label(req.days, "ru")
    price_str = _fmt_price(req.amount, "uzb")
    method_label = (
        t("vip_method_self_label", "ru")
        if req.payment_method == VipPaymentMethod.SELF
        else t("vip_method_moderator_label", "ru")
    )
    text = t(
        "vip_new_request_mod", "ru",
        display_id=req.display_id,
        username_or_id=username_or_id,
        profile_display_id=profile.display_id or "—",
        days_label=days_label_ru,
        price=price_str,
        method_label=method_label,
    )
    for mod_id in get_all_moderator_ids():
        try:
            if req.payment_method == VipPaymentMethod.SELF and req.screenshot_file_id:
                await bot.send_photo(mod_id, photo=req.screenshot_file_id, caption=text)
            else:
                await bot.send_message(mod_id, text)
        except Exception as _e:
            logger.debug("notify mod %s failed: %s", mod_id, _e)


# ── vip_dur:N — пользователь выбрал срок (глобальный, без state) ──
@router.callback_query(F.data.startswith("vip_dur:"))
async def vip_duration_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """После выбора срока VIP — показать «Как оплатить?»"""
    try:
        days = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    data = await state.get_data()
    profile_id = data.get("vip_profile_id")
    region = data.get("vip_region", "uzb")
    lang = await get_lang(session, callback.from_user.id)

    if not profile_id:
        await callback.answer("⚠️ Контекст утерян, начните заново", show_alert=True)
        return

    price = _vip_price_for(days, region)
    price_str = _fmt_price(price, region)
    days_label = _days_label(days, lang)

    await state.update_data(vip_days=days, vip_amount=price)

    text = t("vip_choose_method", lang, days_label=days_label, price=price_str)
    try:
        await callback.message.edit_text(text, reply_markup=vip_method_kb(profile_id, days, lang))
    except Exception as _e:
        logger.debug("edit_text failed: %s", _e)
        await callback.message.answer(text, reply_markup=vip_method_kb(profile_id, days, lang))
    await callback.answer()


# ── «🔙 Назад» к выбору срока (из method-экрана) ──
@router.callback_query(F.data.startswith("vip:back_to_duration:"))
async def vip_back_to_duration(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    region = data.get("vip_region", "uzb")
    flow = data.get("vip_flow", "creation")

    if flow == "creation":
        kb = vip_duration_kb(lang, region, show_skip=True)
    else:
        kb = vip_duration_kb(lang, region, back_cb="my:profile")
    try:
        await callback.message.edit_text(t("vip_choose_duration", lang), reply_markup=kb)
    except Exception as _e:
        logger.debug("edit_text failed: %s", _e)
    await callback.answer()


# ── «🔙 Назад» к method-экрану (из экрана реквизитов) ──
@router.callback_query(F.data.startswith("vip:back_to_method:"))
async def vip_back_to_method(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    try:
        profile_id = int(parts[2])
        days = int(parts[3])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    region = data.get("vip_region", "uzb")
    price_str = _fmt_price(_vip_price_for(days, region), region)
    days_label = _days_label(days, lang)

    text = t("vip_choose_method", lang, days_label=days_label, price=price_str)
    try:
        await callback.message.edit_text(text, reply_markup=vip_method_kb(profile_id, days, lang))
    except Exception as _e:
        logger.debug("edit_text failed: %s", _e)
    await state.set_state(None)  # сбрасываем waiting_screenshot если был
    await callback.answer()


# ── «💳 Оплатить сейчас» — показать реквизиты ──
@router.callback_query(F.data.startswith("vip_pay:self:"))
async def vip_pay_self(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    try:
        profile_id = int(parts[2])
        days = int(parts[3])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    region = data.get("vip_region", "uzb")
    price_str = _fmt_price(_vip_price_for(days, region), region)

    text = t("vip_pay_card_text", lang, price=price_str)
    try:
        await callback.message.edit_text(text, reply_markup=vip_pay_card_kb(profile_id, days, lang))
    except Exception as _e:
        logger.debug("edit_text failed: %s", _e)
    await callback.answer()


# ── «📤 Отправить скриншот» — перейти в ожидание фото ──
@router.callback_query(F.data.startswith("vip_send_ss:"))
async def vip_send_ss_prompt(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    try:
        profile_id = int(parts[1])
        days = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(vip_profile_id=profile_id, vip_days=days)
    await state.set_state(VipPaymentStates.waiting_screenshot)
    try:
        await callback.message.edit_text(t("vip_pay_card_prompt", lang))
    except Exception as _e:
        logger.debug("edit_text failed: %s", _e)
    await callback.answer()


# ── Получение фото-скриншота (Путь А) ──
@router.message(VipPaymentStates.waiting_screenshot, F.photo)
async def vip_receive_screenshot(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    profile_id = data.get("vip_profile_id")
    days = data.get("vip_days")
    amount = data.get("vip_amount")
    lang = (await get_lang(session, message.from_user.id)) if message.from_user else "ru"

    if not (profile_id and days and amount):
        await state.clear()
        await message.answer("⚠️ Контекст утерян. Начните заново через «Мои заявки».")
        return

    profile = await session.get(Profile, profile_id)
    if not profile or profile.user_id != message.from_user.id:
        await state.clear()
        await message.answer("⚠️ Анкета не найдена.")
        return

    file_id = message.photo[-1].file_id
    display_id = await _generate_vip_display_id(session)
    req = VipRequest(
        profile_id=profile.id,
        user_id=message.from_user.id,
        days=days,
        amount=amount,
        display_id=display_id,
        status=VipRequestStatus.PENDING,
        payment_method=VipPaymentMethod.SELF,
        screenshot_file_id=file_id,
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)

    username_or_id = f"@{message.from_user.username}" if message.from_user.username else f"ID:{message.from_user.id}"
    await _notify_mods_new_vip_request(bot, req, profile, username_or_id)

    await message.answer(
        t("vip_request_sent", lang, display_id=display_id),
        reply_markup=main_menu_kb(lang, message.from_user.id),
    )
    await state.clear()


@router.message(VipPaymentStates.waiting_screenshot)
async def vip_screenshot_invalid(message: Message, state: FSMContext, session: AsyncSession):
    lang = await get_lang(session, message.from_user.id)
    await message.answer(t("vip_pay_card_prompt", lang))


# ── «💁‍♀️ Связаться с модератором» (Путь Б) — создаём VipRequest сразу ──
@router.callback_query(F.data.startswith("vip_pay:moderator:"))
async def vip_pay_moderator(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    parts = callback.data.split(":")
    try:
        profile_id = int(parts[2])
        days = int(parts[3])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    region = data.get("vip_region", "uzb")
    amount = _vip_price_for(days, region)
    price_str = _fmt_price(amount, region)

    profile = await session.get(Profile, profile_id)
    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⚠️ Анкета не найдена", show_alert=True)
        return

    display_id = await _generate_vip_display_id(session)
    req = VipRequest(
        profile_id=profile.id,
        user_id=callback.from_user.id,
        days=days,
        amount=amount,
        display_id=display_id,
        status=VipRequestStatus.PENDING,
        payment_method=VipPaymentMethod.MODERATOR,
        screenshot_file_id=None,
    )
    session.add(req)
    await session.commit()
    await session.refresh(req)

    moderator = config.moderator_tashkent
    text = t(
        "vip_pay_moderator_text", lang,
        price=price_str,
        moderator=moderator,
        display_id=profile.display_id or display_id,
    )
    try:
        await callback.message.edit_text(
            text,
            reply_markup=main_menu_kb(lang, callback.from_user.id),
        )
    except Exception as _e:
        logger.debug("edit_text failed: %s", _e)

    username_or_id = f"@{callback.from_user.username}" if callback.from_user.username else f"ID:{callback.from_user.id}"
    await _notify_mods_new_vip_request(bot, req, profile, username_or_id)

    await state.clear()
    await callback.answer()
