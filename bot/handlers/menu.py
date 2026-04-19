"""Шаг 2 — Главное меню, Шаг 3 — О платформе, Шаг 4 — Мои заявки."""

import logging
import re
from aiogram import Router, F, Bot
from aiogram.types import (
    CallbackQuery, Message,
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    User, Profile, ProfileStatus, VipStatus, ContactRequest, Favorite,
    ProfileType, MaritalStatus, ChildrenStatus, PhotoType,
    FamilyPosition, Housing, ParentHousing, CarStatus,
)
from bot.utils.helpers import format_full_anketa, format_anketa_public
from bot.states import ModeratorContactStates, FeedbackSuggestionStates, EditProfileStates
from bot.texts import t
from bot.keyboards.inline import (
    main_menu_kb, _full_menu_kb, back_kb, back_main_kb, my_profile_kb,
    quest_start_kb, contact_moderator_kb, vip_duration_kb,
    choose_moderator_kb, search_submenu_kb, create_submenu_kb,
    edit_profile_kb, edit_education_kb, edit_religiosity_kb,
    edit_marital_kb, edit_nationality_kb, edit_nationality_more_kb, nav_kb, add_nav,
    edit_hub_kb, edit_candidate_kb, edit_family_kb, back_to_section_kb,
    children_kb,
)
from bot.utils.helpers import age_text, calculate_age
from bot.config import config, get_all_moderator_ids

logger = logging.getLogger(__name__)

router = Router()


async def get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


async def _safe_edit(callback: CallbackQuery, text: str, reply_markup=None):
    """Безопасная отправка — edit или answer если edit не удался."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup)


async def show_main_menu(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    await _safe_edit(
        callback,
        t("main_menu", lang),
        reply_markup=main_menu_kb(lang, callback.from_user.id),
    )
    # Уведомление о новых лайках
    try:
        await check_new_favorites(callback, session, callback.from_user.id, lang)
    except Exception as e:
        logger.error(f"Ошибка проверки новых лайков: {e}")


async def check_new_favorites(
    callback_or_message,
    session: AsyncSession,
    user_id: int,
    lang: str,
) -> None:
    """Проверить, сколько раз анкету пользователя добавили в избранное с прошлого входа.

    Если появились новые — показать уведомление и обновить seen_favorites_count.
    """
    from sqlalchemy import func as sqlfunc

    # Анкета пользователя
    profile_res = await session.execute(
        select(Profile).where(
            Profile.user_id == user_id,
            Profile.status != ProfileStatus.DELETED,
        ).limit(1)
    )
    my_profile = profile_res.scalar_one_or_none()
    if not my_profile:
        return

    # Сколько раз сейчас в избранном
    fav_res = await session.execute(
        select(sqlfunc.count(Favorite.id)).where(
            Favorite.profile_id == my_profile.id
        )
    )
    total_favs = fav_res.scalar() or 0

    user = await session.get(User, user_id)
    if not user:
        return
    seen = user.seen_favorites_count or 0
    new_favs = total_favs - seen
    if new_favs <= 0:
        return

    user.seen_favorites_count = total_favs
    await session.commit()

    is_male = my_profile.profile_type == ProfileType.SON
    if lang == "uz":
        who_word = "yigit" if not is_male else "qiz"
        text = (
            f"❤️ <b>Siz {new_favs} ta {who_word}ga yoqdingiz!</b>\n\n"
            f"Anketangiz e'tiborni tortmoqda. 🌟\n\n"
            f"Davom eting — munosib nomzod\n"
            f"sizni kutayotgan bo'lishi mumkin! 💍"
        )
        view_btn = "👀 Anketalarni ko'rish"
        cont_btn = "➡️ Davom etish"
    else:
        if is_male:
            who_word = "девушке" if new_favs == 1 else ("девушкам" if new_favs < 5 else "девушкам")
        else:
            who_word = "парню" if new_favs == 1 else ("парням" if new_favs < 5 else "парням")
        text = (
            f"❤️ <b>Вы понравились {new_favs} {who_word}!</b>\n\n"
            f"Ваша анкета привлекает внимание. 🌟\n\n"
            f"Продолжайте — достойный кандидат\n"
            f"может уже ждать вас! 💍"
        )
        view_btn = "👀 Посмотреть анкеты"
        cont_btn = "➡️ Продолжить"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=view_btn, callback_data="menu:search")],
        [InlineKeyboardButton(text=cont_btn, callback_data="menu:main")],
    ])

    target = getattr(callback_or_message, "message", callback_or_message)
    try:
        await target.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Не удалось показать уведомление о лайках: {e}")


@router.callback_query(F.data == "back:menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    await show_main_menu(callback, session)
    await callback.answer()


@router.callback_query(F.data == "menu:main")
async def menu_main_compat(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Совместимость: старая кнопка '🏠 Главное меню' → полное меню."""
    await state.clear()
    await show_main_menu(callback, session)
    await callback.answer()


@router.callback_query(F.data == "menu:about")
async def about_platform(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 3 — О платформе с живой статистикой."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)

    # Живая статистика
    from sqlalchemy import func
    from datetime import datetime

    total_result = await session.execute(
        select(func.count(Profile.id)).where(Profile.status == ProfileStatus.PUBLISHED)
    )
    total_ankety = total_result.scalar() or 0

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    views_result = await session.execute(
        select(func.coalesce(func.sum(Profile.views_count), 0)).where(
            Profile.status == ProfileStatus.PUBLISHED
        )
    )
    total_views = views_result.scalar() or 0

    if lang == "uz":
        text = (
            f"ℹ️ <b>RISHTA HAQIDA</b>\n\n"
            f"O'zbekistondagi birinchi raqamli\n"
            f"sovchilik platformasi 🇺🇿\n\n"
            f"📊 <b>Bugungi holat:</b>\n"
            f"👥 Faol anketalar: <b>{total_ankety}</b>\n"
            f"👀 Jami ko'rishlar: <b>{total_views}</b>\n\n"
            f"✅ Har bir anketa shaxsan tekshiriladi\n"
            f"✅ Oshkor etilmaydi\n"
            f"✅ Kontakt — rozilik asosida beriladi\n"
            f"✅ Moderator yordam beradi\n"
            f"🔒 Foto skrinshotdan himoyalangan\n\n"
            f"📢 @Rishta_uz | 💬 @Rishta_chat"
        )
    else:
        text = (
            f"ℹ️ <b>О RISHTA</b>\n\n"
            f"Первая цифровая платформа\n"
            f"для сватовства в Узбекистане 🇺🇿\n\n"
            f"📊 <b>Сейчас на платформе:</b>\n"
            f"👥 Активных анкет: <b>{total_ankety}</b>\n"
            f"👀 Просмотров всего: <b>{total_views}</b>\n\n"
            f"✅ Каждая анкета проверяется лично\n"
            f"✅ Полная конфиденциальность\n"
            f"✅ Контакт — по взаимному согласию\n"
            f"✅ Модератор сопровождает процесс\n"
            f"🔒 Фото защищены от скриншотов\n\n"
            f"📢 @Rishta_uz | 💬 @Rishta_chat"
        )

    await _safe_edit(callback, text, reply_markup=back_main_kb(lang))
    await callback.answer()


@router.callback_query(F.data.in_({"menu:my", "my:main"}))
async def my_main(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Хаб «Мои заявки»: выбор между анкетой и избранным."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    if lang == "uz":
        text = "🗂 <b>Mening arizalarim:</b>"
        buttons = [
            [InlineKeyboardButton(text="📋 Mening anketam", callback_data="my:profile")],
            [InlineKeyboardButton(text="❤️ Sevimli anketalar", callback_data="my:favorites")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="menu:main")],
        ]
    else:
        text = "🗂 <b>Мои заявки:</b>"
        buttons = [
            [InlineKeyboardButton(text="📋 Моя анкета", callback_data="my:profile")],
            [InlineKeyboardButton(text="❤️ Избранные анкеты", callback_data="my:favorites")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="menu:main")],
        ]
    await _safe_edit(callback, text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data == "my:profile")
async def my_applications(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 4 — Моя анкета: статистика + полная анкета + управление."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    user_id = callback.from_user.id

    result = await session.execute(
        select(Profile).where(
            Profile.user_id == user_id,
            Profile.status != ProfileStatus.DELETED,
        ).order_by(Profile.created_at.desc())
    )
    profile = result.scalars().first()

    if not profile:
        if lang == "uz":
            text = (
                "📋 Sizda hozircha anketa yo'q.\n\n"
                "Anketa yaratib qidiruvni boshlang!"
            )
        else:
            text = (
                "📋 У вас пока нет анкеты.\n\n"
                "Создайте анкету чтобы начать поиск!"
            )
        from bot.keyboards.inline import create_submenu_kb
        await _safe_edit(callback, text, reply_markup=create_submenu_kb(lang))
        await callback.answer()
        return

    # ── Статистика ──
    from sqlalchemy import func as sqlfunc

    fav_result = await session.execute(
        select(sqlfunc.count(Favorite.id)).where(Favorite.profile_id == profile.id)
    )
    fav_count = fav_result.scalar() or 0

    req_result = await session.execute(
        select(sqlfunc.count(ContactRequest.id)).where(
            ContactRequest.target_profile_id == profile.id
        )
    )
    req_count = req_result.scalar() or 0

    views = profile.views_count or 0
    display_id = profile.display_id or "—"
    vip_active = profile.vip_status == VipStatus.ACTIVE

    status_map_ru = {
        ProfileStatus.DRAFT: "📝 Черновик",
        ProfileStatus.PENDING: "⏳ На проверке",
        ProfileStatus.PUBLISHED: "✅ Опубликована",
        ProfileStatus.REJECTED: "❌ Отклонена",
        ProfileStatus.PAUSED: "⏸ На паузе",
    }
    status_map_uz = {
        ProfileStatus.DRAFT: "📝 Qoralama",
        ProfileStatus.PENDING: "⏳ Tekshiruvda",
        ProfileStatus.PUBLISHED: "✅ Nashr etilgan",
        ProfileStatus.REJECTED: "❌ Rad etilgan",
        ProfileStatus.PAUSED: "⏸ Pauzada",
    }

    s_map = status_map_uz if lang == "uz" else status_map_ru
    status_label = s_map.get(profile.status, "—")
    vip_label = "⭐ VIP" if vip_active else ("📋 Oddiy" if lang == "uz" else "📋 Обычная")

    if lang == "uz":
        stats = (
            f"🗂 <b>Mening anketam</b>\n\n"
            f"🔖 #{display_id}\n"
            f"Holat: {status_label}  {vip_label}\n\n"
            f"👁 Ko'rishlar soni: <b>{views}</b>\n"
            f"❤️ Tanlanganlar: <b>{fav_count}</b>\n"
            f"💬 Kontakt so'rovlari: <b>{req_count}</b>"
        )
    else:
        stats = (
            f"🗂 <b>Моя анкета</b>\n\n"
            f"🔖 #{display_id}\n"
            f"Статус: {status_label}  {vip_label}\n\n"
            f"👁 Просмотров: <b>{views}</b>\n"
            f"❤️ В избранном: <b>{fav_count}</b>\n"
            f"💬 Запросов контакта: <b>{req_count}</b>"
        )

    # ── Полная анкета ──
    anketa_text = format_full_anketa(profile, lang=lang)

    full_text = stats + "\n\n━━━━━━━━━━━━━━━\n\n" + anketa_text

    # Telegram ограничение — 4096 символов
    if len(full_text) > 4000:
        full_text = full_text[:3997] + "..."

    is_active = profile.status == ProfileStatus.PUBLISHED and profile.is_active
    await _safe_edit(callback, full_text, reply_markup=my_profile_kb(profile.id, lang, is_active))

    if profile.photo_file_id:
        try:
            sent_photo = await callback.message.answer_photo(profile.photo_file_id)
            # Сохраняем id фото-сообщения — чтобы удалить при входе в редактирование
            await state.update_data(my_profile_photo_msg_id=sent_photo.message_id)
        except Exception as _e:
            logger.debug("my_applications send_photo failed: %s", _e)

    await callback.answer()


@router.callback_query(F.data == "my:favorites")
async def my_favorites(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показать список анкет, добавленных в избранное."""
    user_id = callback.from_user.id
    lang = await get_lang(session, user_id)

    result = await session.execute(
        select(Profile)
        .join(Favorite, Favorite.profile_id == Profile.id)
        .where(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
    )
    favorites = list(result.scalars().all())

    back_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔙 Orqaga" if lang == "uz" else "🔙 Назад",
            callback_data="my:main",
        )
    ]])

    if not favorites:
        if lang == "uz":
            text = "❤️ Sevimli anketalar yo'q.\n\nQidirishda ❤️ bosing!"
        else:
            text = "❤️ Избранных анкет нет.\n\nПри поиске нажмите ❤️!"
        await _safe_edit(callback, text, reply_markup=back_kb)
        await callback.answer()
        return

    if lang == "uz":
        header = f"❤️ <b>Sevimli anketalar ({len(favorites)}):</b>"
    else:
        header = f"❤️ <b>Избранные анкеты ({len(favorites)}):</b>"
    await _safe_edit(callback, header)

    for p in favorites:
        try:
            card_text = format_anketa_public(p, 0, lang)
        except Exception as e:
            logger.error(f"favorites: format error for profile {p.id}: {e}")
            continue
        if lang == "uz":
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💌 Kontaktni olish", callback_data=f"get_contact:{p.id}")],
                [InlineKeyboardButton(text="🗑 Sevimlilardan o'chirish", callback_data=f"unfav:{p.id}")],
            ])
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💌 Узнать контакт", callback_data=f"get_contact:{p.id}")],
                [InlineKeyboardButton(text="🗑 Удалить из избранного", callback_data=f"unfav:{p.id}")],
            ])
        try:
            await callback.message.answer(card_text, reply_markup=kb)
        except Exception as e:
            logger.error(f"favorites: send error for profile {p.id}: {e}")

    # Кнопка «Назад» в конце списка
    if lang == "uz":
        tail = "─" * 20
    else:
        tail = "─" * 20
    await callback.message.answer(tail, reply_markup=back_kb)
    await callback.answer()


@router.callback_query(F.data.startswith("mypause:"))
async def pause_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.PAUSED
        profile.is_active = False
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer("⏸ Анкета поставлена на паузу" if lang == "ru" else "⏸ Anketa pauzaga qo'yildi")
    # Обновляем экран «Мои заявки»
    await my_applications(callback, state, session)


@router.callback_query(F.data.startswith("myactivate:"))
async def activate_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.PUBLISHED
        profile.is_active = True
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer("🟢 Анкета активирована" if lang == "ru" else "🟢 Anketa faollashtirildi")
    await my_applications(callback, state, session)


@router.callback_query(F.data.startswith("myedit:"))
async def edit_profile_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показать хаб редактирования — 2 раздела (О кандидате / О семье)."""
    # Прочитать photo_msg_id ДО очистки state
    prev_data = await state.get_data()
    photo_msg_id = prev_data.get("my_profile_photo_msg_id")

    await state.clear()
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    lang = await get_lang(session, callback.from_user.id)

    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    # Удаляем фото из «Моя анкета» — оно мешает на экране редактирования
    if photo_msg_id:
        try:
            await callback.bot.delete_message(callback.message.chat.id, photo_msg_id)
        except Exception:
            pass

    await state.update_data(edit_profile_id=profile_id, lang=lang)
    title = t("edit_hub_title", lang) + "\n\n" + t("edit_hub_subtitle", lang)
    await _safe_edit(callback, title, reply_markup=edit_hub_kb(profile_id, lang))
    await callback.answer()


# ── Раздел: О кандидате ──
@router.callback_query(F.data.startswith("editsec:candidate:"))
async def edit_section_candidate(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    profile = await session.get(Profile, profile_id)
    lang = await get_lang(session, callback.from_user.id)

    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    await state.set_state(None)
    await state.update_data(edit_profile_id=profile_id, edit_section="candidate", lang=lang)
    await _safe_edit(
        callback,
        t("edit_section_candidate_title", lang),
        reply_markup=edit_candidate_kb(profile, lang),
    )
    await callback.answer()


# ── Раздел: О семье ──
@router.callback_query(F.data.startswith("editsec:family:"))
async def edit_section_family(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    profile = await session.get(Profile, profile_id)
    lang = await get_lang(session, callback.from_user.id)

    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    await state.set_state(None)
    await state.update_data(edit_profile_id=profile_id, edit_section="family", lang=lang)
    await _safe_edit(
        callback,
        t("edit_section_family_title", lang),
        reply_markup=edit_family_kb(profile, lang),
    )
    await callback.answer()


# ── «Назад» с экрана ввода поля → возврат в раздел редактирования ──
@router.callback_query(F.data == "back:editsec")
async def back_to_edit_section(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    profile_id = data.get("edit_profile_id")
    section = data.get("edit_section", "candidate")
    lang = data.get("lang") or await get_lang(session, callback.from_user.id)

    if not profile_id:
        # FSM data потеряна (рестарт бота) — в главное меню
        await show_main_menu(callback, session)
        await callback.answer()
        return

    profile = await session.get(Profile, profile_id)
    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    await state.set_state(None)
    await state.update_data(edit_profile_id=profile_id, edit_section=section, lang=lang)

    if section == "family":
        kb = edit_family_kb(profile, lang)
        title = t("edit_section_family_title", lang)
    else:
        kb = edit_candidate_kb(profile, lang)
        title = t("edit_section_candidate_title", lang)

    await _safe_edit(callback, title, reply_markup=kb)
    await callback.answer()


# ─── Обработчики кнопок edit:field:profile_id ───

async def _start_edit_field(callback: CallbackQuery, state: FSMContext, session: AsyncSession,
                            field_state, prompt_key: str):
    """Общая логика: показать промпт и перейти в FSM-состояние."""
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    # Merge: edit_section (если установлен при входе в раздел) сохраняется
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await state.set_state(field_state)
    await _safe_edit(callback, t(prompt_key, lang), reply_markup=back_to_section_kb(lang))
    await callback.answer()


async def _finish_edit(message_or_cb, state: FSMContext, session: AsyncSession, lang: str):
    """Вернуться в нужный раздел редактирования (candidate / family) после сохранения."""
    data = await state.get_data()
    profile_id = data.get("edit_profile_id")
    section = data.get("edit_section", "candidate")
    # set_state(None) — НЕ state.clear(): data (edit_section, edit_profile_id) сохраняется
    await state.set_state(None)

    profile = await session.get(Profile, profile_id) if profile_id else None

    if profile is None:
        # Fallback: profile не найден — плоский список (legacy)
        kb = edit_profile_kb(profile_id or 0, lang)
        title = t("edit_menu_title", lang)
    elif section == "family":
        kb = edit_family_kb(profile, lang)
        title = t("edit_section_family_title", lang)
    else:
        kb = edit_candidate_kb(profile, lang)
        title = t("edit_section_candidate_title", lang)

    saved_text = t("edit_saved", lang) + "\n\n" + title

    if isinstance(message_or_cb, Message):
        await message_or_cb.answer(saved_text, reply_markup=kb)
    else:
        await _safe_edit(message_or_cb, saved_text, reply_markup=kb)


# ── Имя ──
@router.callback_query(F.data.startswith("edit:name:"))
async def edit_name_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.name, "edit_name_prompt")


@router.message(EditProfileStates.name)
async def edit_name_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    name = message.text.strip()[:100] if message.text else None
    if not name:
        await message.answer(t("edit_name_prompt", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.name = name
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Год рождения ──
@router.callback_query(F.data.startswith("edit:birth_year:"))
async def edit_birth_year_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.birth_year, "edit_birth_year_prompt")


@router.message(EditProfileStates.birth_year)
async def edit_birth_year_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if not text.isdigit() or not (1960 <= int(text) <= 2008):
        await message.answer(t("invalid_year", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.birth_year = int(text)
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Рост / Вес ──
@router.callback_query(F.data.startswith("edit:height_weight:"))
async def edit_hw_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.height_weight, "edit_height_weight_prompt")


@router.message(EditProfileStates.height_weight)
async def edit_hw_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    parts = (message.text or "").strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await message.answer(t("edit_height_weight_prompt", lang))
        return
    h, w = int(parts[0]), int(parts[1])
    if not (100 <= h <= 250) or not (30 <= w <= 200):
        await message.answer(t("edit_height_weight_prompt", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.height_cm = h
        profile.weight_kg = w
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Национальность ──
@router.callback_query(F.data.startswith("edit:nationality:"))
async def edit_nationality_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await _safe_edit(callback, t("q12", lang), reply_markup=edit_nationality_kb(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("editnat:"))
async def edit_nationality_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    nat = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")

    if nat == "more":
        await callback.message.edit_reply_markup(reply_markup=edit_nationality_more_kb(lang))
        await callback.answer()
        return
    if nat == "back":
        await callback.message.edit_reply_markup(reply_markup=edit_nationality_kb(lang))
        await callback.answer()
        return
    if nat == "custom":
        prompt = "✍️ Введите национальность:" if lang != "uz" else "✍️ Millatingizni kiriting:"
        await _safe_edit(callback, prompt, reply_markup=back_to_section_kb(lang))
        await state.set_state(EditProfileStates.nationality_custom)
        await callback.answer()
        return

    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == callback.from_user.id:
        profile.nationality = nat
        await session.commit()
    await _finish_edit(callback, state, session, lang)


@router.message(EditProfileStates.nationality_custom)
async def edit_nationality_custom(message: Message, state: FSMContext, session: AsyncSession):
    nat = (message.text or "").strip()[:50]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    if not nat:
        await message.answer("✍️ Введите национальность:" if lang != "uz" else "✍️ Millatingizni kiriting:")
        return
    profile = await session.get(Profile, data.get("edit_profile_id"))
    if profile and profile.user_id == message.from_user.id:
        profile.nationality = nat
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Город ──
@router.callback_query(F.data.startswith("edit:city:"))
async def edit_city_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.city, "edit_city_prompt")


@router.message(EditProfileStates.city)
async def edit_city_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if not text:
        await message.answer(t("edit_city_prompt", lang))
        return
    parts = [p.strip() for p in text.split(",")]
    city = parts[0][:100]
    district = parts[1][:100] if len(parts) > 1 else ""
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.city = city
        profile.district = district
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Образование ──
@router.callback_query(F.data.startswith("edit:education:"))
async def edit_education_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await _safe_edit(callback, t("q5", lang), reply_markup=edit_education_kb(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("editedu:"))
async def edit_education_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    from bot.db.models import Education
    val = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == callback.from_user.id:
        profile.education = Education(val)
        await session.commit()
    await _finish_edit(callback, state, session, lang)


# ── Работа ──
@router.callback_query(F.data.startswith("edit:occupation:"))
async def edit_occupation_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.occupation, "edit_occupation_prompt")


@router.message(EditProfileStates.occupation)
async def edit_occupation_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if not text:
        await message.answer(t("edit_occupation_prompt", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.occupation = text[:500]
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Религиозность ──
@router.callback_query(F.data.startswith("edit:religiosity:"))
async def edit_religiosity_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await _safe_edit(callback, t("q16", lang), reply_markup=edit_religiosity_kb(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("editrel:"))
async def edit_religiosity_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    from bot.db.models import Religiosity
    val = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == callback.from_user.id:
        profile.religiosity = Religiosity(val)
        await session.commit()
    await _finish_edit(callback, state, session, lang)


# ── Семейное положение ──
@router.callback_query(F.data.startswith("edit:marital:"))
async def edit_marital_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    profile = await session.get(Profile, profile_id)
    is_male = profile.profile_type == ProfileType.SON if profile else True
    await _safe_edit(callback, t("q_marital_status", lang), reply_markup=edit_marital_kb(lang, is_male))
    await callback.answer()


@router.callback_query(F.data.startswith("editmar:"))
async def edit_marital_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    val = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data["edit_profile_id"])
    if not (profile and profile.user_id == callback.from_user.id):
        await callback.answer("⛔")
        return

    profile.marital_status = MaritalStatus(val)

    if val == "never_married":
        # Не был(а) в браке → детей нет → финиш
        profile.children_status = ChildrenStatus.NO
        await session.commit()
        await _finish_edit(callback, state, session, lang)
        return

    # divorced / widowed → подвопрос про детей
    await session.commit()
    is_son = profile.profile_type == ProfileType.SON
    kb_orig = children_kb(lang, is_son, prefix="editchild")
    rows = list(kb_orig.inline_keyboard) + [_back_editsec_row_local(lang)]
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    prompt = t("q_children", lang)
    await _safe_edit(callback, prompt, reply_markup=kb)
    await state.set_state(EditProfileStates.children)
    await callback.answer()


@router.callback_query(F.data.startswith("editchild:"), EditProfileStates.children)
async def edit_children_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    value = callback.data.replace("editchild:", "")
    mapping = {
        "no": ChildrenStatus.NO,
        "me": ChildrenStatus.YES_WITH_ME,
        "ex": ChildrenStatus.YES_WITH_EX,
    }
    enum_val = mapping.get(value)
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data.get("edit_profile_id"))
    if profile and profile.user_id == callback.from_user.id and enum_val:
        profile.children_status = enum_val
        await session.commit()
    await _finish_edit(callback, state, session, lang)


# ── Фото ──
@router.callback_query(F.data.startswith("edit:photo:"))
async def edit_photo_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.photo, "edit_photo_prompt")


@router.message(EditProfileStates.photo)
async def edit_photo_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    if not message.photo:
        await message.answer(t("edit_photo_prompt", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.photo_file_id = message.photo[-1].file_id
        profile.photo_type = PhotoType.REGULAR
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Телефон ──
@router.callback_query(F.data.startswith("edit:phone:"))
async def edit_phone_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.phone, "edit_phone_prompt")


@router.message(EditProfileStates.phone)
async def edit_phone_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    # Нормализуем номер
    digits = re.sub(r"[^\d]", "", text)
    if len(digits) == 9:
        digits = "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        phone = "+" + digits
    else:
        await message.answer(t("invalid_phone", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.parent_phone = phone
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Telegram родителей ──
@router.callback_query(F.data.startswith("edit:parent_telegram:"))
async def edit_parent_telegram_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.parent_telegram, "edit_parent_telegram_prompt")


@router.message(EditProfileStates.parent_telegram)
async def edit_parent_telegram_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    tg = (message.text or "").strip()[:100]
    if tg and not tg.startswith("@"):
        tg = f"@{tg}"
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.parent_telegram = tg or None
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Telegram кандидата ──
@router.callback_query(F.data.startswith("edit:candidate_telegram:"))
async def edit_candidate_telegram_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.candidate_telegram, "edit_candidate_telegram_prompt")


@router.message(EditProfileStates.candidate_telegram)
async def edit_candidate_telegram_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    tg = (message.text or "").strip()[:100]
    if tg and not tg.startswith("@"):
        tg = f"@{tg}"
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.candidate_telegram = tg or None
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ══════════════════════════════════════
# Редактирование полей Этапа 2
# ══════════════════════════════════════

# ── Отец: чем занимается ──
@router.callback_query(F.data.startswith("edit:father:"))
async def edit_father_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.father, "edit_father_prompt")


@router.message(EditProfileStates.father)
async def edit_father_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()[:100] if message.text else None
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.father_occupation = text or None
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Мать: чем занимается ──
@router.callback_query(F.data.startswith("edit:mother:"))
async def edit_mother_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.mother, "edit_mother_prompt")


@router.message(EditProfileStates.mother)
async def edit_mother_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()[:100] if message.text else None
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.mother_occupation = text or None
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Характер и увлечения ──
@router.callback_query(F.data.startswith("edit:character:"))
async def edit_character_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.character, "edit_character_prompt")


@router.message(EditProfileStates.character)
async def edit_character_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()[:500] if message.text else None
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.character_hobbies = text or None
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Здоровье ──
@router.callback_query(F.data.startswith("edit:health:"))
async def edit_health_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.health, "edit_health_prompt")


@router.message(EditProfileStates.health)
async def edit_health_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()[:500] if message.text else None
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.health_notes = text or None
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── О себе (идеальная семейная жизнь) ──
@router.callback_query(F.data.startswith("edit:about:"))
async def edit_about_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.about, "edit_about_prompt")


@router.message(EditProfileStates.about)
async def edit_about_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()[:500] if message.text else None
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.ideal_family_life = text or None
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ══════════════════════════════════════
# Братья / сёстры / место в семье (комбо из 3 экранов)
# ══════════════════════════════════════

def _back_editsec_row_local(lang: str):
    """Row «← Назад» с callback back:editsec (локально в menu.py)."""
    return [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back:editsec")]


def _siblings_count_kb(prefix: str, lang: str) -> InlineKeyboardMarkup:
    """0/1/2/3/4+ для братьев или сестёр. prefix = 'editbro' или 'editsis'."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="0", callback_data=f"{prefix}:0"),
            InlineKeyboardButton(text="1", callback_data=f"{prefix}:1"),
            InlineKeyboardButton(text="2", callback_data=f"{prefix}:2"),
            InlineKeyboardButton(text="3", callback_data=f"{prefix}:3"),
            InlineKeyboardButton(text="4+", callback_data=f"{prefix}:4"),
        ],
        _back_editsec_row_local(lang),
    ])


def _siblings_position_kb(lang: str) -> InlineKeyboardMarkup:
    if lang == "uz":
        opts = [("Katta", "editpos:oldest"), ("O'rtancha", "editpos:middle"),
                ("Kenja", "editpos:youngest"), ("Yagona", "editpos:only")]
    else:
        opts = [("Старший/ая", "editpos:oldest"), ("Средний/яя", "editpos:middle"),
                ("Младший/ая", "editpos:youngest"), ("Единственный/ая", "editpos:only")]
    rows = [[InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts]
    rows.append(_back_editsec_row_local(lang))
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("edit:siblings:"))
async def edit_siblings_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await state.set_state(EditProfileStates.siblings_brothers)
    await _safe_edit(
        callback,
        t("edit_siblings_brothers_prompt", lang),
        reply_markup=_siblings_count_kb("editbro", lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("editbro:"), EditProfileStates.siblings_brothers)
async def edit_siblings_brothers(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    count = int(callback.data.replace("editbro:", ""))
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data.get("edit_profile_id"))
    if profile and profile.user_id == callback.from_user.id:
        profile.brothers_count = count
        await session.commit()
    await state.set_state(EditProfileStates.siblings_sisters)
    await _safe_edit(
        callback,
        t("edit_siblings_sisters_prompt", lang),
        reply_markup=_siblings_count_kb("editsis", lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("editsis:"), EditProfileStates.siblings_sisters)
async def edit_siblings_sisters(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    count = int(callback.data.replace("editsis:", ""))
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data.get("edit_profile_id"))
    if profile and profile.user_id == callback.from_user.id:
        profile.sisters_count = count
        await session.commit()
    await state.set_state(EditProfileStates.siblings_position)
    await _safe_edit(
        callback,
        t("edit_siblings_position_prompt", lang),
        reply_markup=_siblings_position_kb(lang),
    )
    await callback.answer()


_FAMILY_POS_MAP = {
    "oldest": FamilyPosition.OLDEST,
    "middle": FamilyPosition.MIDDLE,
    "youngest": FamilyPosition.YOUNGEST,
    "only": FamilyPosition.ONLY,
}


@router.callback_query(F.data.startswith("editpos:"), EditProfileStates.siblings_position)
async def edit_siblings_position(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    value = callback.data.replace("editpos:", "")
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data.get("edit_profile_id"))
    if profile and profile.user_id == callback.from_user.id:
        enum_val = _FAMILY_POS_MAP.get(value)
        if enum_val:
            profile.family_position = enum_val
            await session.commit()
    await _finish_edit(callback, state, session, lang)


# ══════════════════════════════════════
# Жильё (housing) + тип жилья родителей (housing_parent)
# ══════════════════════════════════════

def _housing_kb(lang: str) -> InlineKeyboardMarkup:
    if lang == "uz":
        opts = [
            ("Shaxsiy uy", "edithouse:own_house"),
            ("Shaxsiy kvartira", "edithouse:own_apartment"),
            ("Ota-ona bilan", "edithouse:with_parents"),
            ("Ijara", "edithouse:rent"),
        ]
    else:
        opts = [
            ("Свой дом", "edithouse:own_house"),
            ("Своя квартира", "edithouse:own_apartment"),
            ("С родителями", "edithouse:with_parents"),
            ("Аренда", "edithouse:rent"),
        ]
    rows = [[InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts]
    rows.append(_back_editsec_row_local(lang))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _housing_parent_kb(lang: str) -> InlineKeyboardMarkup:
    if lang == "uz":
        opts = [("Uy", "editphouse:house"), ("Kvartira", "editphouse:apartment")]
    else:
        opts = [("Дом", "editphouse:house"), ("Квартира", "editphouse:apartment")]
    rows = [[InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts]
    rows.append(_back_editsec_row_local(lang))
    return InlineKeyboardMarkup(inline_keyboard=rows)


_HOUSING_MAP = {
    "own_house": Housing.OWN_HOUSE,
    "own_apartment": Housing.OWN_APARTMENT,
    "with_parents": Housing.WITH_PARENTS,
    "rent": Housing.RENT,
}

_PARENT_HOUSING_MAP = {
    "house": ParentHousing.HOUSE,
    "apartment": ParentHousing.APARTMENT,
}


@router.callback_query(F.data.startswith("edit:housing:"))
async def edit_housing_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await state.set_state(EditProfileStates.housing)
    await _safe_edit(callback, t("edit_housing_prompt", lang), reply_markup=_housing_kb(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("edithouse:"), EditProfileStates.housing)
async def edit_housing_choose(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    value = callback.data.replace("edithouse:", "")
    data = await state.get_data()
    lang = data.get("lang", "ru")
    enum_val = _HOUSING_MAP.get(value)
    if not enum_val:
        await callback.answer()
        return

    profile = await session.get(Profile, data.get("edit_profile_id"))
    if profile and profile.user_id == callback.from_user.id:
        profile.housing = enum_val
        if enum_val != Housing.WITH_PARENTS:
            # Сбрасываем подтип — он не имеет смысла без «с родителями»
            profile.parent_housing_type = None
        await session.commit()

    if enum_val == Housing.WITH_PARENTS:
        # Переход на второй экран: тип жилья родителей
        await state.set_state(EditProfileStates.housing_parent)
        await _safe_edit(callback, t("edit_housing_parent_prompt", lang), reply_markup=_housing_parent_kb(lang))
        await callback.answer()
    else:
        await _finish_edit(callback, state, session, lang)


@router.callback_query(F.data.startswith("editphouse:"), EditProfileStates.housing_parent)
async def edit_housing_parent_choose(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    value = callback.data.replace("editphouse:", "")
    data = await state.get_data()
    lang = data.get("lang", "ru")
    enum_val = _PARENT_HOUSING_MAP.get(value)
    profile = await session.get(Profile, data.get("edit_profile_id"))
    if profile and profile.user_id == callback.from_user.id and enum_val:
        profile.parent_housing_type = enum_val
        await session.commit()
    await _finish_edit(callback, state, session, lang)


# ══════════════════════════════════════
# Автомобиль
# ══════════════════════════════════════

def _car_kb(lang: str) -> InlineKeyboardMarkup:
    if lang == "uz":
        opts = [
            ("Shaxsiy", "editcar:personal"),
            ("Oilaviy", "editcar:family"),
            ("Yo'q", "editcar:none"),
        ]
    else:
        opts = [
            ("Личный", "editcar:personal"),
            ("Семейный", "editcar:family"),
            ("Нет", "editcar:none"),
        ]
    rows = [[InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts]
    rows.append(_back_editsec_row_local(lang))
    return InlineKeyboardMarkup(inline_keyboard=rows)


_CAR_MAP = {
    "personal": CarStatus.PERSONAL,
    "family": CarStatus.FAMILY,
    "none": CarStatus.NONE,
}


@router.callback_query(F.data.startswith("edit:car:"))
async def edit_car_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await state.set_state(EditProfileStates.car)
    await _safe_edit(callback, t("edit_car_prompt", lang), reply_markup=_car_kb(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("editcar:"), EditProfileStates.car)
async def edit_car_choose(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    value = callback.data.replace("editcar:", "")
    data = await state.get_data()
    lang = data.get("lang", "ru")
    enum_val = _CAR_MAP.get(value)
    profile = await session.get(Profile, data.get("edit_profile_id"))
    if profile and profile.user_id == callback.from_user.id and enum_val:
        profile.car = enum_val
        await session.commit()
    await _finish_edit(callback, state, session, lang)


# ══════════════════════════════════════
# Адрес (text / geolocation / link) — копия логики Q14
# ══════════════════════════════════════

def _address_choice_kb(lang: str) -> InlineKeyboardMarkup:
    if lang == "uz":
        opts = [
            ("🏠 Manzilni yozish", "editaddr:text"),
            ("📍 Geolokatsiya yuborish", "editaddr:geo"),
            ("🗺 Xarita havolasi", "editaddr:link"),
        ]
    else:
        opts = [
            ("🏠 Написать адрес", "editaddr:text"),
            ("📍 Отправить геолокацию", "editaddr:geo"),
            ("🗺 Ссылка на карту", "editaddr:link"),
        ]
    rows = [[InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts]
    rows.append(_back_editsec_row_local(lang))
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data.startswith("edit:address:"))
async def edit_address_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await state.set_state(EditProfileStates.address)
    await _safe_edit(callback, t("edit_address_prompt", lang), reply_markup=_address_choice_kb(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("editaddr:"), EditProfileStates.address)
async def edit_address_choose(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    choice = callback.data.replace("editaddr:", "")
    data = await state.get_data()
    lang = data.get("lang", "ru")

    # Удаляем окно выбора
    try:
        await callback.message.delete()
    except Exception:
        pass

    if choice == "text":
        prompt = "Ko'cha/mahalla nomini kiriting:" if lang == "uz" else "Введите улицу/махаллю:"
        sent = await callback.message.answer(prompt, reply_markup=back_to_section_kb(lang))
        await state.update_data(last_bot_msg_id=sent.message_id)
        await state.set_state(EditProfileStates.address_text)
    elif choice == "geo":
        geo_label = "📍 Geolokatsiya yuborish" if lang == "uz" else "📍 Отправить геолокацию"
        title = "📍 Geolokatsiya:" if lang == "uz" else "📍 Геолокация:"
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=geo_label, request_location=True)]],
            resize_keyboard=True, one_time_keyboard=True,
        )
        sent = await callback.message.answer(title, reply_markup=kb)
        await state.update_data(last_bot_msg_id=sent.message_id)
        await state.set_state(EditProfileStates.address_location)
    elif choice == "link":
        prompt = "🗺 Google Maps yoki 2GIS havolasini kiriting:" if lang == "uz" else "🗺 Вставьте ссылку Google Maps или 2GIS:"
        sent = await callback.message.answer(prompt, reply_markup=back_to_section_kb(lang))
        await state.update_data(last_bot_msg_id=sent.message_id)
        await state.set_state(EditProfileStates.address_link)

    await callback.answer()


@router.message(EditProfileStates.address_text)
async def edit_address_text(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if not text:
        return
    profile = await session.get(Profile, data.get("edit_profile_id"))
    if profile and profile.user_id == message.from_user.id:
        profile.address = text
        await session.commit()
    try:
        await message.delete()
    except Exception:
        pass
    await _finish_edit(message, state, session, lang)


@router.message(EditProfileStates.address_location)
async def edit_address_location(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        profile = await session.get(Profile, data.get("edit_profile_id"))
        if profile and profile.user_id == message.from_user.id:
            profile.location_lat = lat
            profile.location_lon = lon
            profile.location_link = f"https://maps.google.com/?q={lat},{lon}"
            await session.commit()
    try:
        await message.delete()
    except Exception:
        pass
    # Убираем reply-клавиатуру одноразовым сообщением
    try:
        tmp = await message.answer("✓", reply_markup=ReplyKeyboardRemove())
        await tmp.delete()
    except Exception:
        pass
    # Удаляем старый prompt «Геолокация:»
    last_id = data.get("last_bot_msg_id")
    if last_id:
        try:
            await message.bot.delete_message(message.chat.id, last_id)
        except Exception:
            pass
        await state.update_data(last_bot_msg_id=None)
    await _finish_edit(message, state, session, lang)


@router.message(EditProfileStates.address_link)
async def edit_address_link(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    link = (message.text or "").strip()
    if not link:
        return
    profile = await session.get(Profile, data.get("edit_profile_id"))
    if profile and profile.user_id == message.from_user.id:
        profile.location_link = link
        await session.commit()
    try:
        await message.delete()
    except Exception:
        pass
    await _finish_edit(message, state, session, lang)


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

    await state.update_data(vip_profile_id=profile_id, vip_region=region, vip_flow="upgrade")

    await _safe_edit(
        callback,
        t("vip_choose_duration", lang),
        reply_markup=vip_duration_kb(lang, region, back_cb="my:profile"),
    )
    await callback.answer()


# vip_duration_selected перенесён в bot/handlers/payment.py (теперь показывает
# экран «Как оплатить?» вместо старого экрана реквизитов с ссылкой на модератора)


@router.callback_query(F.data.startswith("mydelete:"))
async def delete_confirm(callback: CallbackQuery, session: AsyncSession):
    """Подтверждение удаления анкеты."""
    profile_id = callback.data.split(":")[1]
    lang = await get_lang(session, callback.from_user.id)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    if lang == "uz":
        text = "⚠️ Anketani o'chirishni tasdiqlaysizmi?\nBu amalni ortga qaytarib bo'lmaydi!"
    else:
        text = "⚠️ Вы уверены что хотите удалить анкету?\nЭто действие нельзя отменить!"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Да, удалить" if lang == "ru" else "✅ Ha, o'chirish",
            callback_data=f"mydelete_yes:{profile_id}",
        )],
        [InlineKeyboardButton(
            text="❌ Отмена" if lang == "ru" else "❌ Bekor qilish",
            callback_data="menu:my",
        )],
    ])
    await _safe_edit(callback, text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("mydelete_yes:"))
async def delete_execute(callback: CallbackQuery, session: AsyncSession):
    """Фактическое удаление анкеты."""
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.DELETED
        profile.is_active = False
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    text = "✅ Анкета удалена." if lang == "ru" else "✅ Anketa o'chirildi."
    await _safe_edit(callback, text, reply_markup=main_menu_kb(lang, callback.from_user.id))
    await callback.answer()


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
async def contact_moderator_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Связаться с модератором — выбор из двух."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await _safe_edit(
        callback,
        t("choose_moderator", lang),
        reply_markup=choose_moderator_kb(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:search_sub")
async def search_submenu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подменю: Найти кандидата → невестку / жениха."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await _safe_edit(callback, t("submenu_search", lang), reply_markup=search_submenu_kb(lang))
    await callback.answer()


@router.callback_query(F.data.in_({"menu:search_bride", "menu:search_groom"}))
async def search_redirect(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Поиск невестки / жениха — всегда уважаем явный выбор пользователя."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)

    # menu:search_bride → анкеты дочерей (искатель ищет невесту для сына)
    # menu:search_groom → анкеты сыновей (искатель ищет жениха для дочери)
    search_type = ProfileType.DAUGHTER if callback.data == "menu:search_bride" else ProfileType.SON

    # Сохраняем выбор в state (чтобы последующие search:all / search:manual
    # не переопределяли search_type автоматикой «противоположный пол»)
    await state.update_data(
        search_filters={},
        search_offset=0,
        search_type=search_type.value,
    )

    result = await session.execute(
        select(Profile).where(
            Profile.user_id == callback.from_user.id,
            Profile.status != ProfileStatus.DELETED,
        ).limit(1)
    )
    my_profile = result.scalar_one_or_none()

    if my_profile:
        # Пользователь зарегистрирован — показываем выбор режима
        # search_type уже сохранён в state, «Показать все» его использует
        from bot.keyboards.inline import search_mode_kb
        await _safe_edit(callback, t("search_title", lang), reply_markup=search_mode_kb(lang))
        await callback.answer()
        return

    # Без анкеты — гостевой режим
    await state.update_data(is_guest=True)
    from bot.handlers.search import _show_search_results
    await _show_search_results(callback, session, state, lang)


@router.callback_query(F.data == "menu:create_sub")
async def create_submenu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подменю: Создать анкету → сына / дочери."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await _safe_edit(callback, t("submenu_create", lang), reply_markup=create_submenu_kb(lang))
    await callback.answer()


@router.callback_query(F.data == "menu:son")
async def start_son_quest(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 5А — Всегда начинаем заполнение анкеты сына."""
    logger.info(f"menu:son от user {callback.from_user.id}")
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(lang=lang, profile_type="son")
    await _safe_edit(
        callback,
        t("quest_son_intro", lang),
        reply_markup=quest_start_kb(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:daughter")
async def start_daughter_quest(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 5Б — Всегда начинаем заполнение анкеты дочери."""
    logger.info(f"menu:daughter от user {callback.from_user.id}")
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(lang=lang, profile_type="daughter")
    await _safe_edit(
        callback,
        t("quest_daughter_intro", lang),
        reply_markup=quest_start_kb(lang),
    )
    await callback.answer()


# ── Написать модератору ──
@router.callback_query(F.data == "mod:write")
async def mod_write_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    prompt = "✍️ Напишите ваше сообщение модератору:" if lang == "ru" else "✍️ Moderatorga xabaringizni yozing:"
    await _safe_edit(callback, prompt, reply_markup=back_main_kb(lang))
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

    # Вариант В: есть анкета → свой модератор, нет анкеты (гость) → всем
    if profile:
        from bot.services.moderator_routing import resolve_primary_moderator
        target_ids = [resolve_primary_moderator(profile)["telegram_id"]]
    else:
        target_ids = get_all_moderator_ids()

    for mod_id in target_ids:
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
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await _safe_edit(
        callback,
        t("user_feedback_prompt", lang),
        reply_markup=back_main_kb(lang),
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


# ── Extend: дополнить анкету / пропустить ──

@router.callback_query(F.data == "extend:skip")
async def extend_skip(callback: CallbackQuery):
    lang = "ru"
    try:
        await callback.message.edit_text(
            "👌 " + ("Xabar olasiz keyinroq" if callback.from_user.language_code == "uz" else "Хорошо, напомним позже")
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("extend:"))
async def extend_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пользователь хочет дополнить анкету — запускаем Этап 2."""
    profile_id_str = callback.data.split(":")[1]
    if not profile_id_str.isdigit():
        await callback.answer()
        return

    profile_id = int(profile_id_str)
    lang = await get_lang(session, callback.from_user.id)

    profile = await session.get(Profile, profile_id)
    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    # Запускаем расширенную анкету
    await state.clear()
    await state.update_data(
        ext_profile_id=profile_id,
        lang=lang,
        profile_type=profile.profile_type.value if profile.profile_type else "son",
    )

    from bot.keyboards.inline import housing_kb
    from bot.states import QuestionnaireStates

    await _safe_edit(
        callback,
        t("ext_housing", lang),
        reply_markup=add_nav(housing_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_housing)
    await callback.answer()
