"""Шаг 2 — Главное меню, Шаг 3 — О платформе, Шаг 4 — Мои заявки."""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, Profile, ProfileStatus, VipStatus, ContactRequest, Favorite, ProfileType
from bot.states import ModeratorContactStates, FeedbackSuggestionStates
from bot.texts import t
from bot.keyboards.inline import (
    main_menu_kb, _full_menu_kb, back_kb, my_profile_kb,
    quest_start_kb, contact_moderator_kb, vip_duration_kb,
    choose_moderator_kb,
)
from bot.utils.helpers import age_text, calculate_age
from bot.config import config, get_all_moderator_ids

router = Router()


async def get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


async def show_main_menu(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    await callback.message.edit_text(
        t("main_menu", lang),
        reply_markup=main_menu_kb(lang, callback.from_user.id),
    )


@router.callback_query(F.data == "back:menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    await show_main_menu(callback, session)
    await callback.answer()


@router.callback_query(F.data == "menu:main")
async def show_user_full_menu(callback: CallbackQuery, session: AsyncSession):
    """Обычный пользователь нажал '🏠 Главное меню' → показываем полное меню."""
    lang = await get_lang(session, callback.from_user.id)
    menu_title = "Bosh menyu:" if lang == "uz" else "Главное меню:"
    await callback.message.edit_text(menu_title, reply_markup=_full_menu_kb(lang))
    await callback.answer()


@router.callback_query(F.data == "menu:about")
async def about_platform(callback: CallbackQuery, session: AsyncSession):
    """Шаг 3 — О платформе."""
    lang = await get_lang(session, callback.from_user.id)
    await callback.message.edit_text(t("about", lang), reply_markup=back_kb(lang))
    await callback.answer()


@router.callback_query(F.data == "menu:my")
async def my_applications(callback: CallbackQuery, session: AsyncSession):
    """Шаг 4 — Мои заявки."""
    lang = await get_lang(session, callback.from_user.id)
    user_id = callback.from_user.id

    result = await session.execute(
        select(Profile).where(
            Profile.user_id == user_id,
            Profile.status != ProfileStatus.DELETED,
        )
    )
    profiles = result.scalars().all()

    if not profiles:
        await callback.message.edit_text(t("no_profiles", lang), reply_markup=back_kb(lang))
        await callback.answer()
        return

    for profile in profiles:
        # Считаем запросы и избранное
        req_result = await session.execute(
            select(ContactRequest).where(ContactRequest.target_profile_id == profile.id)
        )
        requests = req_result.scalars().all()

        fav_result = await session.execute(
            select(Favorite).where(Favorite.user_id == user_id)
        )
        fav_count = len(fav_result.scalars().all())

        vip_label = "⭐ VIP" if profile.vip_status == VipStatus.ACTIVE else "📋 Обычная"
        status_map = {
            ProfileStatus.DRAFT: "📝 Черновик",
            ProfileStatus.PENDING: "⏳ На проверке",
            ProfileStatus.PUBLISHED: "✅ Опубликована",
            ProfileStatus.REJECTED: "❌ Отклонена",
            ProfileStatus.PAUSED: "⏸ На паузе",
        }
        status_label = status_map.get(profile.status, str(profile.status))

        text = (
            f"📋 <b>МОИ ЗАЯВКИ</b>\n\n"
            f"🔖 Анкета: {profile.display_id or '—'}\n"
            f"Статус: {status_label}\n"
            f"Тип: {vip_label}\n"
            f"👁 Просмотров: {profile.views_count or 0}\n"
            f"💬 Запросов: {len(requests)}\n\n"
            f"❤️ Избранное ({fav_count} анкет)"
        )

        # Добавляем список запросов
        if requests:
            text += "\n\n📨 Мои запросы:"
            for req in requests[:5]:
                target = await session.get(Profile, req.target_profile_id)
                status_icons = {
                    "pending": "⏳ Ожидание",
                    "talking": "⏳ Общаемся",
                    "contact_given": "✅ Контакт получен",
                    "rejected": "❌ Не подошли",
                }
                icon = status_icons.get(req.status.value, req.status.value)
                text += f"\n• {target.display_id if target else '—'} — {icon}"

        is_active = profile.status == ProfileStatus.PUBLISHED and profile.is_active
        await callback.message.edit_text(
            text,
            reply_markup=my_profile_kb(profile.id, lang, is_active),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("mypause:"))
async def pause_profile(callback: CallbackQuery, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.PAUSED
        profile.is_active = False
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer("⏸ Анкета поставлена на паузу" if lang == "ru" else "⏸ Anketa pauzaga qo'yildi")
    await show_main_menu(callback, session)


@router.callback_query(F.data.startswith("myactivate:"))
async def activate_profile(callback: CallbackQuery, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.PUBLISHED
        profile.is_active = True
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer("🟢 Анкета активирована" if lang == "ru" else "🟢 Anketa faollashtirildi")
    await show_main_menu(callback, session)


@router.callback_query(F.data.startswith("myedit:"))
async def edit_profile(callback: CallbackQuery, session: AsyncSession):
    """Редактирование — через модератора."""
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer(
        "✏️ Свяжитесь с модератором для редактирования" if lang == "ru"
        else "✏️ Tahrirlash uchun moderator bilan bog'laning"
    )


@router.callback_query(F.data.startswith("myvip:"))
async def upgrade_to_vip(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Переход на VIP — показываем выбор срока с ценами."""
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    lang = await get_lang(session, callback.from_user.id)

    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    if profile.vip_status == VipStatus.ACTIVE:
        expires = ""
        if profile.vip_expires_at:
            expires = profile.vip_expires_at.strftime("%d.%m.%Y")
        msg = f"⭐ VIP активен до {expires}" if lang == "ru" else f"⭐ VIP {expires} gacha faol"
        await callback.answer(msg, show_alert=True)
        return

    # Определяем регион для цен
    region = "uzb"
    if profile.residence_status:
        res = profile.residence_status.value
        if res in ("usa", "europe", "citizenship_other", "other_country"):
            region = "usa"
        elif res == "cis":
            region = "sng"

    await state.update_data(vip_profile_id=profile_id, vip_region=region)

    text = (
        f"⭐ <b>VIP анкета</b>\n\n"
        f"🔖 Анкета: {profile.display_id or '—'}\n\n"
        f"Ваша анкета будет:\n"
        f"• Показываться первой в поиске\n"
        f"• Выделена значком ⭐\n"
        f"• Привлекать больше внимания\n\n"
        f"Выберите срок:"
    ) if lang == "ru" else (
        f"⭐ <b>VIP anketa</b>\n\n"
        f"🔖 Anketa: {profile.display_id or '—'}\n\n"
        f"Anketangiz:\n"
        f"• Qidirishda birinchi ko'rinadi\n"
        f"• ⭐ belgisi bilan ajratiladi\n"
        f"• Ko'proq e'tibor tortadi\n\n"
        f"Muddatni tanlang:"
    )

    await callback.message.edit_text(text, reply_markup=vip_duration_kb(lang, region))
    await callback.answer()


@router.callback_query(F.data.startswith("vip_dur:"))
async def vip_duration_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пользователь выбрал срок VIP — направляем к модератору для оплаты."""
    days = int(callback.data.split(":")[1])
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    profile_id = data.get("vip_profile_id")
    region = data.get("vip_region", "uzb")

    from bot.config import VIP_PRICES_UZB, VIP_PRICES_USD, VIP_PRICES_SNG, VIP_DURATION_LABELS

    prices = {"uzb": VIP_PRICES_UZB, "sng": VIP_PRICES_SNG, "usa": VIP_PRICES_USD}.get(region, VIP_PRICES_UZB)
    price = prices.get(str(days), 0)

    days_label = VIP_DURATION_LABELS.get(days, {}).get(lang, f"{days}")

    if region == "usa":
        price_str = f"${price // 100}"
    else:
        price_str = f"{price:,} сум".replace(",", " ")

    from bot.config import config
    moderator = config.moderator_tashkent

    profile = await session.get(Profile, profile_id) if profile_id else None
    display_id = profile.display_id if profile else "—"

    text = (
        f"⭐ <b>VIP — {days_label}</b>\n\n"
        f"🔖 Анкета: {display_id}\n"
        f"💰 Стоимость: <b>{price_str}</b>\n\n"
        f"Для оплаты свяжитесь с модератором:\n{moderator}"
    ) if lang == "ru" else (
        f"⭐ <b>VIP — {days_label}</b>\n\n"
        f"🔖 Anketa: {display_id}\n"
        f"💰 Narxi: <b>{price_str}</b>\n\n"
        f"To'lov uchun moderator bilan bog'laning:\n{moderator}"
    )

    from bot.keyboards.inline import back_kb
    await callback.message.edit_text(text, reply_markup=back_kb(lang))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("mydelete:"))
async def delete_profile(callback: CallbackQuery, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.DELETED
        profile.is_active = False
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer("🗑 Анкета удалена" if lang == "ru" else "🗑 Anketa o'chirildi")
    await show_main_menu(callback, session)


# ── Напоминания (Шаг 18) ──
@router.callback_query(F.data.startswith("remind:"))
async def handle_reminder(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    action = parts[1]
    profile_id = int(parts[2])
    profile = await session.get(Profile, profile_id)

    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    lang = await get_lang(session, callback.from_user.id)

    if action == "keep":
        await callback.answer("✅ Анкета остаётся активной" if lang == "ru" else "✅ Anketa faol qoladi")
    elif action == "pause":
        profile.status = ProfileStatus.PAUSED
        profile.is_active = False
        await session.commit()
        await callback.answer("⏸ Анкета на паузе" if lang == "ru" else "⏸ Anketa pauzada")
    elif action == "delete":
        profile.status = ProfileStatus.DELETED
        profile.is_active = False
        await session.commit()
        await callback.answer("🗑 Анкета удалена" if lang == "ru" else "🗑 Anketa o'chirildi")
    elif action == "edit":
        await callback.answer("✏️ Свяжитесь с модератором для обновления" if lang == "ru" else "✏️ Yangilash uchun moderator bilan bog'laning")

    await callback.message.edit_text(callback.message.text + f"\n\n→ {action.upper()}")


@router.callback_query(F.data == "menu:moderator")
async def contact_moderator_menu(callback: CallbackQuery, session: AsyncSession):
    """Связаться с модератором — выбор из двух."""
    lang = await get_lang(session, callback.from_user.id)
    await callback.message.edit_text(
        t("choose_moderator", lang),
        reply_markup=choose_moderator_kb(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:son")
async def start_son_quest(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 5А — Начало анкеты сына. Если анкета уже есть — переходим к поиску."""
    lang = await get_lang(session, callback.from_user.id)

    # Проверяем, есть ли у пользователя уже анкета типа SON
    result = await session.execute(
        select(Profile).where(
            Profile.user_id == callback.from_user.id,
            Profile.profile_type == ProfileType.SON,
            Profile.status != ProfileStatus.DELETED,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Уже есть анкета — показываем поиск невесток
        callback.data = "search:browse"
        from bot.handlers.search import search_browse_compat
        await search_browse_compat(callback, session, state)
        return

    await state.update_data(lang=lang, profile_type="son")
    await callback.message.edit_text(
        t("quest_son_intro", lang),
        reply_markup=quest_start_kb(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:daughter")
async def start_daughter_quest(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 5Б — Начало анкеты дочери."""
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(lang=lang, profile_type="daughter")
    await callback.message.edit_text(
        t("quest_daughter_intro", lang),
        reply_markup=quest_start_kb(lang),
    )
    await callback.answer()


# ── Написать модератору ──
@router.callback_query(F.data == "mod:write")
async def mod_write_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    prompt = "✍️ Напишите ваше сообщение модератору:" if lang == "ru" else "✍️ Moderatorga xabaringizni yozing:"
    await callback.message.edit_text(prompt, reply_markup=back_kb(lang))
    await state.set_state(ModeratorContactStates.awaiting_message)
    await callback.answer()


@router.message(ModeratorContactStates.awaiting_message)
async def mod_write_forward(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    from bot.config import config
    lang = await get_lang(session, message.from_user.id)

    if not config.moderator_chat_id:
        err = "⚠️ Модератор временно недоступен." if lang == "ru" else "⚠️ Moderator vaqtincha mavjud emas."
        await message.answer(err)
        await state.clear()
        return

    # Находим анкету пользователя
    result = await session.execute(
        select(Profile).where(Profile.user_id == message.from_user.id).limit(1)
    )
    profile = result.scalar_one_or_none()
    display_id = profile.display_id if profile else "—"

    header = (
        f"📩 <b>СООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"👤 @{message.from_user.username or '—'} (ID: {message.from_user.id})\n"
        f"🔖 Анкета: {display_id}\n"
        f"━━━━━━━━━━━━━━━\n"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    reply_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Ответить", callback_data=f"modreply:{message.from_user.id}")],
    ])

    for mod_id in get_all_moderator_ids():
        try:
            await bot.send_message(mod_id, header + (message.text or ""), reply_markup=reply_kb)
            if message.photo:
                await bot.send_photo(mod_id, message.photo[-1].file_id)
            if message.document:
                await bot.send_document(mod_id, message.document.file_id)
            if message.voice:
                await bot.send_voice(mod_id, message.voice.file_id)
            if message.video:
                await bot.send_video(mod_id, message.video.file_id)
        except Exception:
            pass

    ok = "✅ Сообщение отправлено модератору. Ожидайте ответа." if lang == "ru" else "✅ Xabar moderatorga yuborildi. Javobni kuting."
    await message.answer(ok, reply_markup=main_menu_kb(lang, message.from_user.id))
    await state.clear()


# ── Обратная связь / Предложения ──

@router.callback_query(F.data == "menu:feedback")
async def user_feedback_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    await callback.message.edit_text(
        t("user_feedback_prompt", lang),
        reply_markup=back_kb(lang),
    )
    await state.set_state(FeedbackSuggestionStates.awaiting_text)
    await callback.answer()


@router.message(FeedbackSuggestionStates.awaiting_text)
async def user_feedback_receive(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    lang = await get_lang(session, message.from_user.id)
    user = message.from_user

    # Находим анкету пользователя
    result = await session.execute(
        select(Profile).where(Profile.user_id == user.id).limit(1)
    )
    profile = result.scalar_one_or_none()
    display_id = profile.display_id if profile else "—"

    mod_text = (
        f"💡 <b>НОВОЕ ПРЕДЛОЖЕНИЕ</b>\n\n"
        f"От: @{user.username or '—'} (ID: {user.id})\n"
        f"🔖 Анкета: {display_id}\n"
        f"Язык: {lang}\n\n"
        f"Текст:\n{message.text}"
    )

    for mod_id in get_all_moderator_ids():
        try:
            await bot.send_message(mod_id, mod_text)
        except Exception:
            pass

    await message.answer(t("user_feedback_thanks", lang), reply_markup=main_menu_kb(lang, user.id))
    await state.clear()
