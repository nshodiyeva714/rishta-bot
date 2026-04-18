"""Поиск анкет — 3 режима: по требованиям, ручные фильтры, все."""

import random
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, desc, case, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    User, Profile, ProfileStatus, ProfileType, VipStatus,
    Requirement, Favorite, ContactRequest, RequestStatus,
)
from bot.texts import t
from bot.keyboards.inline import (
    profile_card_kb, search_nav_kb, back_kb, back_main_kb, main_menu_kb,
    get_contact_kb, search_mode_kb, search_no_anketa_kb,
    search_filter_kb, filter_option_kb, nav_kb,
    nationality_main_rows, nationality_more_rows,
)
from bot.utils.helpers import age_text, calculate_age, format_anketa_public, occupation_label
from bot.config import config
from bot.states import SearchStates, ContactStates

logger = logging.getLogger(__name__)

router = Router()


# ── Уведомления владельцу анкеты ──

NOTIFY_AT_VIEWS = {5, 10, 25, 50, 100, 200, 500}


async def _notify_owner_view(bot: Bot, session: AsyncSession, profile: Profile, viewer_id: int):
    """Уведомляет владельца на милстоунах просмотров 5/10/25/50/100/200/500 и каждые 100."""
    views = profile.views_count or 0
    if views not in NOTIFY_AT_VIEWS and (views < 500 or views % 100 != 0):
        return
    if not profile.user_id or profile.user_id == viewer_id:
        return

    result = await session.execute(select(User).where(User.id == profile.user_id))
    user = result.scalar_one_or_none()
    lang = user.language.value if user and user.language else "ru"

    display_id = profile.display_id or "—"
    if lang == "uz":
        text = (
            f"👁 <b>Anketangiz mashhur bo'lmoqda!</b>\n\n"
            f"🔖 {display_id}\n"
            f"Ko'rishlar soni: <b>{views}</b>\n\n"
            f"Anketangiz ishlayapti! 🤲"
        )
    else:
        text = (
            f"👁 <b>Ваша анкета набирает популярность!</b>\n\n"
            f"🔖 {display_id}\n"
            f"Просмотров: <b>{views}</b>\n\n"
            f"Ваша анкета работает! 🤲"
        )
    try:
        await bot.send_message(profile.user_id, text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка уведомления о просмотре: {e}")


async def _notify_owner_favorite(bot: Bot, session: AsyncSession, profile: Profile, user_id: int):
    """Уведомляет владельца что анкету добавили в избранное."""
    if not profile.user_id or profile.user_id == user_id:
        return

    result = await session.execute(select(User).where(User.id == profile.user_id))
    user = result.scalar_one_or_none()
    lang = user.language.value if user and user.language else "ru"

    display_id = profile.display_id or "—"
    if lang == "uz":
        text = (
            f"❤️ <b>Anketangiz tanlanganlar ga qo'shildi!</b>\n\n"
            f"🔖 {display_id}\n\n"
            f"Bu yaxshi belgi — oila qiziqyapti! 😊"
        )
    else:
        text = (
            f"❤️ <b>Вашу анкету добавили в избранное!</b>\n\n"
            f"🔖 {display_id}\n\n"
            f"Хороший знак — семья заинтересовалась! 😊"
        )
    try:
        await bot.send_message(profile.user_id, text)
    except Exception as e:
        logger.error(f"Ошибка уведомления об избранном: {e}")


async def _notify_owner_contact_request(bot: Bot, session: AsyncSession, profile: Profile):
    """Уведомляет владельца что запросили контакт."""
    if not profile.user_id:
        return

    result = await session.execute(select(User).where(User.id == profile.user_id))
    user = result.scalar_one_or_none()
    lang = user.language.value if user and user.language else "ru"

    display_id = profile.display_id or "—"
    if lang == "uz":
        text = (
            f"🔥 <b>Anketangizga jiddiy qiziqish!</b>\n\n"
            f"🔖 {display_id}\n\n"
            f"Bir oila sizning kontaktingizni so'radi.\n"
            f"Moderator tez orada siz bilan bog'lanadi 🤝"
        )
    else:
        text = (
            f"🔥 <b>Серьёзный интерес к вашей анкете!</b>\n\n"
            f"🔖 {display_id}\n\n"
            f"Семья запросила ваши контакты.\n"
            f"Модератор свяжется с вами в ближайшее время 🤝"
        )
    try:
        await bot.send_message(profile.user_id, text)
    except Exception as e:
        logger.error(f"Ошибка уведомления о запросе контакта: {e}")

PROFILES_PER_PAGE = 1  # Показывать по одной анкете


# ── helpers ──

async def get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


async def _get_user_profile(session: AsyncSession, user_id: int):
    """Получить первую не-удалённую анкету пользователя."""
    result = await session.execute(
        select(Profile).where(
            Profile.user_id == user_id,
            Profile.status != ProfileStatus.DELETED,
        ).limit(1)
    )
    return result.scalar_one_or_none()


async def _get_user_requirement(session: AsyncSession, profile_id: int):
    result = await session.execute(
        select(Requirement).where(Requirement.profile_id == profile_id)
    )
    return result.scalar_one_or_none()


def compute_match_score(profile: Profile, req: Requirement) -> int:
    """Простой расчёт процента совместимости."""
    if not req:
        return 50
    score = 50

    if profile.birth_year and req.age_from and req.age_to:
        age = calculate_age(profile.birth_year)
        if req.age_from <= age <= req.age_to:
            score += 15
        else:
            score -= 10

    if req.nationality and req.nationality != "any" and profile.nationality:
        if profile.nationality == req.nationality:
            score += 10

    if req.religiosity and req.religiosity != "any" and profile.religiosity:
        if profile.religiosity.value == req.religiosity:
            score += 10

    if req.education and req.education != "any" and profile.education:
        if profile.education.value == req.education or req.education == "vocational":
            score += 5

    if req.marital_status and req.marital_status != "any" and profile.marital_status:
        if profile.marital_status.value == req.marital_status:
            score += 5

    if req.children and req.children != "any" and profile.children_status:
        if req.children == "no_children" and profile.children_status.value == "no":
            score += 5

    return min(max(score, 10), 99)


def build_selected_filters_text(filters: dict, lang: str = "ru") -> str:
    """Формирует текст выбранных фильтров на языке пользователя."""
    if not filters:
        return ""

    L = lang if lang in ("ru", "uz") else "ru"

    labels = {
        "ru": {
            "age":         "Возраст",
            "religion":    "Религиозность",
            "education":   "Образование",
            "residence":   "Где проживает",
            "region":      "Регион",
            "nationality": "Национальность",
            "marital":     "Семейное положение",
            "children":    "Дети",
        },
        "uz": {
            "age":         "Yoshi",
            "religion":    "Dindorligi",
            "education":   "Ma'lumoti",
            "residence":   "Yashash joyi",
            "region":      "Hudud",
            "nationality": "Millati",
            "marital":     "Oilaviy holati",
            "children":    "Farzandlari",
        },
    }

    value_labels = {
        "ru": {
            # Возраст (кнопки)
            "18_23": "18–23", "24_27": "24–27", "28_35": "28–35",
            "36_45": "36–45", "45plus": "45+",
            # Религиозность
            "practicing": "Практикующий", "moderate": "Умеренный", "secular": "Светский",
            # Образование
            "secondary": "Среднее", "vocational": "Среднее специальное",
            "higher": "Высшее", "studying": "Студент",
            # Проживание / страны
            "uzbekistan": "🇺🇿 Узбекистан", "cis": "СНГ",
            "usa": "🇺🇸 США", "russia": "🇷🇺 Россия",
            "kazakhstan": "🇰🇿 Казахстан", "kyrgyzstan": "🇰🇬 Кыргызстан",
            "tajikistan": "🇹🇯 Таджикистан", "turkmenistan": "🇹🇲 Туркменистан",
            "europe": "🌍 Европа", "other_country": "Другое",
            "abroad": "🌏 За рубежом",
            # Регионы Узбекистана
            "tashkent": "Ташкент", "samarkand": "Самарканд",
            "fergana": "Фергана", "bukhara": "Бухара",
            "namangan": "Наманган", "andijan": "Андижан", "nukus": "Нукус",
            "other": "🌏 Другая страна",
            # Национальность
            "uzbek": "Узбек", "russian": "Русский", "korean": "Кореец",
            "tajik": "Таджик", "kazakh": "Казах",
            # Семейное положение
            "never_married": "Не был(а) в браке", "divorced": "Разведён/а",
            "widowed": "Вдовец/Вдова",
            # Дети
            "no": "Нет", "no_children": "Нет",
            "yes_with_me": "Есть, живут вместе",
            "yes_with_ex": "Есть, живут с бывшим",
            "has_children": "Есть",
            # Универсальное
            "any": "Не важно",
        },
        "uz": {
            # Возраст (кнопки)
            "18_23": "18–23", "24_27": "24–27", "28_35": "28–35",
            "36_45": "36–45", "45plus": "45+",
            # Религиозность
            "practicing": "Amaliyotchi", "moderate": "Mo'tadil", "secular": "Dunyoviy",
            # Образование
            "secondary": "O'rta", "vocational": "O'rta maxsus",
            "higher": "Oliy", "studying": "Talaba",
            # Проживание / страны
            "uzbekistan": "🇺🇿 O'zbekiston", "cis": "MDH",
            "usa": "🇺🇸 AQSH", "russia": "🇷🇺 Rossiya",
            "kazakhstan": "🇰🇿 Qozog'iston", "kyrgyzstan": "🇰🇬 Qirg'iziston",
            "tajikistan": "🇹🇯 Tojikiston", "turkmenistan": "🇹🇲 Turkmaniston",
            "europe": "🌍 Yevropa", "other_country": "Boshqa",
            "abroad": "🌏 Chet elda",
            # Регионы Узбекистана
            "tashkent": "Toshkent", "samarkand": "Samarqand",
            "fergana": "Farg'ona", "bukhara": "Buxoro",
            "namangan": "Namangan", "andijan": "Andijon", "nukus": "Nukus",
            "other": "🌏 Boshqa mamlakat",
            # Национальность
            "uzbek": "O'zbek", "russian": "Rus", "korean": "Koreys",
            "tajik": "Tojik", "kazakh": "Qozoq",
            # Семейное положение
            "never_married": "Turmush qurmagan", "divorced": "Ajrashgan",
            "widowed": "Beva",
            # Дети
            "no": "Yo'q", "no_children": "Yo'q",
            "yes_with_me": "Bor, birga yashaydi",
            "yes_with_ex": "Bor, sobiq bilan",
            "has_children": "Bor",
            # Универсальное
            "any": "Muhim emas",
        },
    }

    lines = []

    # Возраст: age_from/age_to (из требований) ИЛИ age (из кнопок)
    age_label = labels[L]["age"]
    if filters.get("age_from") or filters.get("age_to"):
        af = filters.get("age_from", "?")
        at = filters.get("age_to", "?")
        lines.append(f"• {age_label}: {af}–{at}")
    elif filters.get("age"):
        val = value_labels[L].get(filters["age"], filters["age"])
        lines.append(f"• {age_label}: {val}")

    # Остальные фильтры в фиксированном порядке
    ordered_keys = ["religion", "education", "residence", "region",
                    "nationality", "marital", "children"]
    for key in ordered_keys:
        value = filters.get(key)
        if not value:
            continue
        # Если выбран регион — не дублируем «Где проживает: Узбекистан»
        if key == "residence" and "region" in filters:
            continue
        label = labels[L].get(key, key)
        val = value_labels[L].get(str(value), str(value))
        lines.append(f"• {label}: {val}")

    return "\n".join(lines)


# Совместимость — старый вызов
def format_filters_summary(filters: dict, lang: str = "ru") -> str:
    text = build_selected_filters_text(filters, lang)
    return text if text else t("search_filters_empty", lang)


# ══════════════════════════════════════════════════════════
#  ИЗМЕНЕНИЕ 2 — Стартовый экран поиска (menu:search)
# ══════════════════════════════════════════════════════════


@router.callback_query(F.data == "menu:search")
async def search_start(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Начало поиска — выбор режима."""
    lang = await get_lang(session, callback.from_user.id)
    my_profile = await _get_user_profile(session, callback.from_user.id)

    if my_profile:
        await callback.message.edit_text(
            t("search_title", lang),
            reply_markup=search_mode_kb(lang),
        )
    else:
        # Нет анкеты — гостевой режим: спрашиваем кого ищет
        if lang == "uz":
            text = "🔍 Kimni qidiryapsiz?"
            buttons = [
                [InlineKeyboardButton(text="👦 Kuyov qidiryapman", callback_data="search_guest:son")],
                [InlineKeyboardButton(text="👧 Kelin qidiryapman", callback_data="search_guest:daughter")],
                [InlineKeyboardButton(text="← Orqaga", callback_data="back:menu")],
            ]
        else:
            text = "🔍 Кого вы ищете?"
            buttons = [
                [InlineKeyboardButton(text="👦 Ищу жениха", callback_data="search_guest:son")],
                [InlineKeyboardButton(text="👧 Ищу невесту", callback_data="search_guest:daughter")],
                [InlineKeyboardButton(text="← Назад", callback_data="back:menu")],
            ]
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("search_guest:"))
async def search_guest(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Поиск без анкеты — гостевой режим."""
    choice = callback.data.split(":")[1]  # son = ищем жениха, daughter = ищем невесту
    # son → показываем анкеты сыновей, daughter → анкеты дочерей
    search_type = ProfileType.SON if choice == "son" else ProfileType.DAUGHTER
    await state.update_data(
        search_filters={},
        search_offset=0,
        search_type=search_type.value,
        is_guest=True,
        search_results=None,
        search_scores=None,
        current_index=0,
    )
    lang = await get_lang(session, callback.from_user.id)
    await _show_search_results(callback, session, state, lang)


# ══════════════════════════════════════════════════════════
#  ИЗМЕНЕНИЕ 3 — Поиск по требованиям из анкеты
# ══════════════════════════════════════════════════════════


@router.callback_query(F.data == "search:my_req")
async def search_by_my_requirements(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Поиск по требованиям из анкеты пользователя."""
    lang = await get_lang(session, callback.from_user.id)
    my_profile = await _get_user_profile(session, callback.from_user.id)
    if not my_profile:
        await callback.answer("⚠️")
        return

    req = await _get_user_requirement(session, my_profile.id)

    filters = {}
    if req:
        if req.age_from:
            filters["age_from"] = req.age_from
        if req.age_to:
            filters["age_to"] = req.age_to
        if req.education and req.education != "any":
            filters["education"] = req.education
        if req.religiosity and req.religiosity != "any":
            filters["religion"] = req.religiosity
        if req.marital_status and req.marital_status != "any":
            filters["marital"] = req.marital_status
        if req.children and req.children != "any":
            filters["children"] = req.children
        if req.nationality and req.nationality != "any":
            filters["nationality"] = req.nationality
        if req.residence and req.residence != "any":
            filters["residence"] = req.residence

    # Противоположный пол
    search_type = ProfileType.DAUGHTER if my_profile.profile_type == ProfileType.SON else ProfileType.SON

    await state.update_data(
        search_filters=filters,
        search_offset=0,
        search_type=search_type.value,
        search_results=None,
        search_scores=None,
        current_index=0,
    )

    await _show_search_results(callback, session, state, lang)


# ══════════════════════════════════════════════════════════
#  ИЗМЕНЕНИЕ 4 — Ручные фильтры
# ══════════════════════════════════════════════════════════

async def show_search_filters(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Экран фильтров — выбранные показаны текстом, остальные кнопками."""
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    filters = data.get("search_filters", {})

    # Заголовок
    text = t("search_filters_title", lang)

    # Выбранные фильтры — текстом
    selected = build_selected_filters_text(filters, lang)
    if selected:
        text += "\n\n" + selected

    # Клавиатура — только невыбранные фильтры
    kb = search_filter_kb(lang, filters)
    try:
        await callback.message.edit_text(text, reply_markup=kb)
    except Exception:
        try:
            await callback.message.answer(text, reply_markup=kb)
        except Exception as e:
            logger.error(f"show_search_filters error: {e}")
    try:
        await callback.answer()
    except Exception as _e:
        logger.debug("ignored: %s", _e)


@router.callback_query(F.data == "search:manual")
async def search_manual(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать меню ручных фильтров — всегда с чистыми фильтрами."""
    data = await state.get_data()

    # Определяем search_type если ещё нет
    if "search_type" not in data:
        my_profile = await _get_user_profile(session, callback.from_user.id)
        search_type = "daughter" if my_profile and my_profile.profile_type == ProfileType.SON else "son"
        await state.update_data(search_type=search_type)

    # Всегда начинаем с пустых фильтров
    await state.update_data(search_filters={}, search_offset=0,
                            search_results=None, search_scores=None, current_index=0)

    await show_search_filters(callback, session, state)


# ── Возврат на экран фильтров без сброса (back-кнопка из сабменю фильтра) ──


@router.callback_query(F.data == "filter:back")
async def filter_back(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Вернуться на экран фильтров без очистки выбранных фильтров."""
    await show_search_filters(callback, session, state)


# ── Фильтр: возраст ──


@router.callback_query(F.data == "filter:age")
async def filter_age(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("🎂 18–23", "fval:age:18_23"),
        ("🎂 24–27", "fval:age:24_27"),
        ("🎂 28–35", "fval:age:28_35"),
        ("🎂 36–45", "fval:age:36_45"),
        ("🎂 45+",   "fval:age:45plus"),
        ("✏️ O'z oralig'ingiz" if lang == "uz" else "✏️ Свой диапазон",
                                                     "filter_age:custom"),
        ("✅ Muhim emas" if lang == "uz" else "✅ Не важно", "fval:age:any"),
    ]
    title = "🎂 Возраст:" if lang == "ru" else "🎂 Yosh:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Свой диапазон возраста ──


@router.callback_query(F.data == "filter_age:custom")
async def filter_age_custom(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    text = "🎂 Dan (yosh) kiriting:\n(masalan: 25)" if lang == "uz" else "🎂 Введите ОТ (лет):\n(например: 25)"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔙 Orqaga" if lang == "uz" else "🔙 Назад",
            callback_data="filter:age",
        )
    ]])
    await callback.message.edit_text(text, reply_markup=kb)
    await state.update_data(
        custom_age_lang=lang,
        last_bot_msg_id=callback.message.message_id,
    )
    await state.set_state(SearchStates.age_from)
    await callback.answer()


@router.message(SearchStates.age_from)
async def filter_age_from(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("custom_age_lang", "ru")
    try:
        age_from = int(message.text.strip())
    except (ValueError, AttributeError):
        err = "⚠️ Raqam kiriting" if lang == "uz" else "⚠️ Введите число"
        try:
            await message.delete()
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        tmp = await message.answer(err)
        # не ломаем state — юзер может попробовать ещё раз
        return
    if age_from < 18 or age_from > 60:
        err = "⚠️ Yosh 18 dan 60 gacha bo'lishi kerak" if lang == "uz" else "⚠️ От 18 до 60 лет"
        try:
            await message.delete()
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        await message.answer(err)
        return

    await state.update_data(custom_age_from=age_from)
    try:
        await message.delete()
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    # Удаляем старое сообщение бота
    last_id = data.get("last_bot_msg_id")
    if last_id:
        try:
            await message.bot.delete_message(message.chat.id, last_id)
        except Exception as _e:
            logger.debug("ignored: %s", _e)
    text = "🎂 Gacha (yosh) kiriting:\n(masalan: 35)" if lang == "uz" else "🎂 Введите ДО (лет):\n(например: 35)"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🔙 Orqaga" if lang == "uz" else "🔙 Назад",
            callback_data="filter:age",
        )
    ]])
    sent = await message.answer(text, reply_markup=kb)
    await state.update_data(last_bot_msg_id=sent.message_id)
    await state.set_state(SearchStates.age_to)


@router.message(SearchStates.age_to)
async def filter_age_to(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("custom_age_lang", "ru")
    age_from = data.get("custom_age_from", 18)
    filters = data.get("search_filters", {})

    try:
        age_to = int(message.text.strip())
    except (ValueError, AttributeError):
        err = "⚠️ Raqam kiriting" if lang == "uz" else "⚠️ Введите число"
        try:
            await message.delete()
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        await message.answer(err)
        return

    if age_to < age_from:
        err = (f"⚠️ Yosh {age_from} dan katta bo'lishi kerak"
               if lang == "uz" else
               f"⚠️ Должно быть больше {age_from}")
        try:
            await message.delete()
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        await message.answer(err)
        return
    if age_to > 60:
        err = "⚠️ 60 dan oshmasin" if lang == "uz" else "⚠️ Не более 60 лет"
        try:
            await message.delete()
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        await message.answer(err)
        return

    # Сохраняем кастомный диапазон
    filters["age"] = f"custom_{age_from}_{age_to}"
    filters["age_from"] = age_from
    filters["age_to"] = age_to
    await state.update_data(search_filters=filters)
    await state.set_state(None)

    try:
        await message.delete()
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    last_id = data.get("last_bot_msg_id")
    if last_id:
        try:
            await message.bot.delete_message(message.chat.id, last_id)
        except Exception as _e:
            logger.debug("ignored: %s", _e)
    # Показываем экран фильтров с сохранённым диапазоном
    text = t("search_filters_title", lang)
    selected = build_selected_filters_text(filters, lang)
    if selected:
        text += "\n\n" + selected
    kb = search_filter_kb(lang, filters)
    sent = await message.answer(text, reply_markup=kb)
    await state.update_data(last_bot_msg_id=sent.message_id)


# ── Фильтр: религиозность ──


@router.callback_query(F.data == "filter:religion")
async def filter_religion(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("🕌 Практикующий/ая" if lang == "ru" else "🕌 Amaliyotchi", "fval:religion:practicing"),
        ("☪️ Умеренный/ая"    if lang == "ru" else "☪️ Mo'tadil",    "fval:religion:moderate"),
        ("🌐 Светский/ая"     if lang == "ru" else "🌐 Dunyoviy",    "fval:religion:secular"),
        ("✅ Не важно"        if lang == "ru" else "✅ Muhim emas",  "fval:religion:any"),
    ]
    title = "🕌 Религиозность:" if lang == "ru" else "🕌 Dindorlik:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Фильтр: образование ──


@router.callback_query(F.data == "filter:education")
async def filter_education(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("📚 Среднее" if lang == "ru" else "📚 O'rta",                        "fval:education:secondary"),
        ("📋 Среднее специальное" if lang == "ru" else "📋 O'rta maxsus",     "fval:education:vocational"),
        ("🎓 Высшее" if lang == "ru" else "🎓 Oliy",                          "fval:education:higher"),
        ("🏛 Студент/ка" if lang == "ru" else "🏛 Talaba",                    "fval:education:studying"),
        ("✅ Не важно" if lang == "ru" else "✅ Muhim emas",                  "fval:education:any"),
    ]
    title = "🎓 Образование:" if lang == "ru" else "🎓 Ma'lumot:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Фильтр: семейное положение ──


@router.callback_query(F.data == "filter:marital")
async def filter_marital(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("💍 Не был(а) в браке" if lang == "ru" else "💍 Turmush qurmagan", "fval:marital:never_married"),
        ("💔 Разведён/а" if lang == "ru" else "💔 Ajrashgan",               "fval:marital:divorced"),
        ("🕊 Вдовец/Вдова" if lang == "ru" else "🕊 Beva",                  "fval:marital:widowed"),
        ("✅ Не важно" if lang == "ru" else "✅ Muhim emas",                "fval:marital:any"),
    ]
    title = "💍 Семейное положение:" if lang == "ru" else "💍 Oilaviy holat:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Фильтр: проживание ──


@router.callback_query(F.data == "filter:residence")
async def filter_residence(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    if lang == "uz":
        options = [
            ("🇺🇿 O'zbekiston",   "filter:residence:uzb"),
            ("🇺🇸 AQSH",          "fval:region:usa"),
            ("🇷🇺 Rossiya",       "fval:region:russia"),
            ("🇰🇿 Qozog'iston",   "fval:region:kazakhstan"),
            ("🇰🇬 Qirg'iziston",  "fval:region:kyrgyzstan"),
            ("🇹🇯 Tojikiston",    "fval:region:tajikistan"),
            ("🇹🇲 Turkmaniston",  "fval:region:turkmenistan"),
            ("🌍 Yevropa",        "fval:region:europe"),
            ("✅ Muhim emas",     "fval:region:any"),
        ]
        title = "🏡 Yashash joyi:"
    else:
        options = [
            ("🇺🇿 Узбекистан",    "filter:residence:uzb"),
            ("🇺🇸 США",           "fval:region:usa"),
            ("🇷🇺 Россия",        "fval:region:russia"),
            ("🇰🇿 Казахстан",     "fval:region:kazakhstan"),
            ("🇰🇬 Кыргызстан",    "fval:region:kyrgyzstan"),
            ("🇹🇯 Таджикистан",   "fval:region:tajikistan"),
            ("🇹🇲 Туркменистан",  "fval:region:turkmenistan"),
            ("🌍 Европа",         "fval:region:europe"),
            ("✅ Не важно",       "fval:region:any"),
        ]
        title = "🏡 Где проживает:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Узбекистан → выбор региона ──


@router.callback_query(F.data == "filter:residence:uzb")
async def filter_residence_uzb(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    if lang == "uz":
        options = [
            ("🏙 Toshkent (shahar)",  "fval:region:tashkent"),
            ("🌆 Toshkent viloyati",  "fval:region:tashkent_region"),
            ("🏛 Samarqand",          "fval:region:samarkand"),
            ("🌸 Farg'ona",           "fval:region:fergana"),
            ("🌿 Andijon",            "fval:region:andijan"),
            ("🏔 Namangan",           "fval:region:namangan"),
            ("🏜 Buxoro",            "fval:region:bukhara"),
            ("🌾 Qashqadaryo",        "fval:region:kashkadarya"),
            ("🏕 Surxondaryo",        "fval:region:surkhandarya"),
            ("🌊 Xorazm",            "fval:region:khorezm"),
            ("🏝 Qoraqalpog'iston",  "fval:region:karakalpakstan"),
            ("🌄 Jizzax",            "fval:region:jizzakh"),
            ("🌻 Sirdaryo",          "fval:region:sirdarya"),
            ("✅ Muhim emas",        "fval:region:any"),
        ]
        title = "🇺🇿 Viloyatni tanlang:"
    else:
        options = [
            ("🏙 Ташкент (город)",     "fval:region:tashkent"),
            ("🌆 Ташкентская область", "fval:region:tashkent_region"),
            ("🏛 Самарканд",           "fval:region:samarkand"),
            ("🌸 Фергана",            "fval:region:fergana"),
            ("🌿 Андижан",            "fval:region:andijan"),
            ("🏔 Наманган",           "fval:region:namangan"),
            ("🏜 Бухара",             "fval:region:bukhara"),
            ("🌾 Кашкадарья",         "fval:region:kashkadarya"),
            ("🏕 Сурхандарья",        "fval:region:surkhandarya"),
            ("🌊 Хорезм",             "fval:region:khorezm"),
            ("🏝 Каракалпакстан",     "fval:region:karakalpakstan"),
            ("🌄 Джизак",             "fval:region:jizzakh"),
            ("🌻 Сырдарья",           "fval:region:sirdarya"),
            ("✅ Не важно",           "fval:region:any"),
        ]
        title = "🇺🇿 Выберите область:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Фильтр: национальность ──


_FILTER_NAT_PREFIX = "fval:nationality"


def _filter_nat_main_kb(lang: str) -> InlineKeyboardMarkup:
    rows = nationality_main_rows(lang, _FILTER_NAT_PREFIX, show_any=True)
    rows.extend(nav_kb(lang, "filter:back"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _filter_nat_more_kb(lang: str) -> InlineKeyboardMarkup:
    rows = nationality_more_rows(lang, _FILTER_NAT_PREFIX, show_custom=False)
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.callback_query(F.data == "filter:nationality")
async def filter_nationality(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    title = "Национальность:" if lang == "ru" else "Millat:"
    await callback.message.edit_text(title, reply_markup=_filter_nat_main_kb(lang))
    await callback.answer()


@router.callback_query(F.data == "fval:nationality:more")
async def filter_nationality_more(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=_filter_nat_more_kb(lang))
    await callback.answer()


@router.callback_query(F.data == "fval:nationality:back")
async def filter_nationality_back(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=_filter_nat_main_kb(lang))
    await callback.answer()


# ── Фильтр: наличие детей ──


@router.callback_query(F.data == "filter:children")
async def filter_children(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    if lang == "uz":
        options = [
            ("👶 Farzandsiz",      "fval:children:no"),
            ("👨\u200d👧 Farzand bor", "fval:children:has_children"),
            ("✅ Muhim emas",      "fval:children:any"),
        ]
        title = "👶 Farzandlar:"
    else:
        options = [
            ("👶 Без детей",       "fval:children:no"),
            ("👨\u200d👧 Есть дети",  "fval:children:has_children"),
            ("✅ Не важно",        "fval:children:any"),
        ]
        title = "👶 Наличие детей:"
    await callback.message.edit_text(
        title, reply_markup=filter_option_kb(options, lang)
    )
    await callback.answer()


# ── Универсальный обработчик значений фильтров ──


@router.callback_query(F.data.startswith("fval:"))
async def filter_value_set(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Callback: fval:<field>:<value>"""
    parts = callback.data.split(":")
    field = parts[1]
    value = parts[2]

    data = await state.get_data()
    filters = data.get("search_filters", {})

    # Сохраняем значение (в т.ч. "any") — так кнопка исчезнет, а текст покажет "Не важно"
    filters[field] = value

    # Возраст: при выборе — убираем старые age_from/age_to из требований
    if field == "age":
        filters.pop("age_from", None)
        filters.pop("age_to", None)

    # Не автовыставляем residence — сам фильтр region уже покрывает UZ-анкеты
    # через city_code/country/NULL. Иначе старые анкеты с residence_status=NULL
    # не пройдут условие Profile.residence_status == UZBEKISTAN.
    _UZ_REGION_CODES = {
        "tashkent", "tashkent_region", "samarkand",
        "fergana", "andijan", "namangan", "bukhara",
        "kashkadarya", "surkhandarya", "khorezm",
        "karakalpakstan", "jizzakh", "sirdarya",
        "nukus", "uz_other", "uzbekistan",
    }
    if field == "region":
        filters.pop("residence", None)

    # Если выбрано residence — убираем регион
    if field == "residence":
        filters.pop("region", None)

    await state.update_data(search_filters=filters)
    await show_search_filters(callback, session, state)


# ── Сбросить фильтры ──


@router.callback_query(F.data == "filter:clear")
async def filter_clear(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.update_data(search_filters={}, search_offset=0,
                            search_results=None, search_scores=None, current_index=0)

    # Обновляем экран фильтров (show_search_filters сам вызовет callback.answer)
    await show_search_filters(callback, session, state)


# ── Запустить поиск из фильтров ──


@router.callback_query(F.data == "filter:go")
async def filter_go(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()

    # Убедимся что search_type установлен
    if "search_type" not in data:
        my_profile = await _get_user_profile(session, callback.from_user.id)
        search_type = "daughter" if my_profile and my_profile.profile_type == ProfileType.SON else "son"
        await state.update_data(search_type=search_type)

    await state.update_data(search_offset=0, search_results=None,
                            search_scores=None, current_index=0)
    await _show_search_results(callback, session, state, lang)


# ══════════════════════════════════════════════════════════
#  Показать все анкеты без фильтров
# ══════════════════════════════════════════════════════════


@router.callback_query(F.data == "search:all")
async def search_all(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    # Если search_type уже выбран (menu:search_bride/groom) — не перезаписываем
    search_type = data.get("search_type")
    if not search_type:
        my_profile = await _get_user_profile(session, callback.from_user.id)
        search_type = "daughter" if my_profile and my_profile.profile_type == ProfileType.SON else "son"
    await state.update_data(search_filters={}, search_offset=0, search_type=search_type,
                            search_results=None, search_scores=None, current_index=0)
    await _show_search_results(callback, session, state, lang)


# ══════════════════════════════════════════════════════════
#  Старый вход через menu:son (search:browse) — совместимость
# ══════════════════════════════════════════════════════════


@router.callback_query(F.data == "search:browse")
async def search_browse_compat(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Совместимость со старым входом через 'Ищем невестку'."""
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    search_type = data.get("search_type")
    if not search_type:
        my_profile = await _get_user_profile(session, callback.from_user.id)
        search_type = "daughter" if my_profile and my_profile.profile_type == ProfileType.SON else "son"
    await state.update_data(search_filters={}, search_offset=0, search_type=search_type,
                            search_results=None, search_scores=None, current_index=0)
    await _show_search_results(callback, session, state, lang)


# ══════════════════════════════════════════════════════════
#  ИЗМЕНЕНИЕ 5 — Показ результатов с пагинацией
# ══════════════════════════════════════════════════════════

async def _build_search_query(session: AsyncSession, user_id: int, search_type: str, filters: dict, is_guest: bool = False):
    """Построить query с фильтрами, вернуть (profiles, user_req)."""
    target_type = ProfileType.SON if search_type == "son" else ProfileType.DAUGHTER

    from sqlalchemy import or_ as _or_active
    conditions = [
        Profile.status == ProfileStatus.PUBLISHED,
        # is_active: True или NULL (старые записи) — исключаем только явное False
        _or_active(Profile.is_active.is_(True), Profile.is_active.is_(None)),
        Profile.profile_type == target_type,
    ]
    # Исключать свои анкеты из поиска (в гостевом режиме у user_id нет анкет)
    if not is_guest:
        conditions.append(Profile.user_id != user_id)

    # Фильтр: возраст — поддержка кнопок-диапазонов И старого формата age_from/age_to
    import datetime
    current_year = datetime.datetime.now().year

    age_ranges = {
        "18_23": (18, 23), "24_27": (24, 27), "28_35": (28, 35),
        "36_45": (36, 45), "45plus": (45, 80),
    }
    if filters.get("age") and filters["age"] in age_ranges:
        a_from, a_to = age_ranges[filters["age"]]
        conditions.append(Profile.birth_year >= current_year - a_to)
        conditions.append(Profile.birth_year <= current_year - a_from)
    elif filters.get("age_from") or filters.get("age_to"):
        if filters.get("age_to"):
            conditions.append(Profile.birth_year >= current_year - filters["age_to"])
        if filters.get("age_from"):
            conditions.append(Profile.birth_year <= current_year - filters["age_from"])

    # Фильтр: образование
    if filters.get("education") and filters["education"] != "any":
        from bot.db.models import Education
        try:
            conditions.append(Profile.education == Education(filters["education"]))
        except ValueError:
            pass

    # Фильтр: религиозность
    if filters.get("religion") and filters["religion"] != "any":
        from bot.db.models import Religiosity
        try:
            conditions.append(Profile.religiosity == Religiosity(filters["religion"]))
        except ValueError:
            pass

    # Фильтр: семейное положение
    if filters.get("marital") and filters["marital"] != "any":
        from bot.db.models import MaritalStatus
        try:
            conditions.append(Profile.marital_status == MaritalStatus(filters["marital"]))
        except ValueError:
            pass

    # Фильтр: дети
    if filters.get("children") and filters["children"] != "any":
        from bot.db.models import ChildrenStatus
        from sqlalchemy import or_
        ch = filters["children"]
        if ch in ("no", "no_children"):
            conditions.append(Profile.children_status == ChildrenStatus.NO)
        elif ch == "has_children":
            conditions.append(or_(
                Profile.children_status == ChildrenStatus.YES_WITH_ME,
                Profile.children_status == ChildrenStatus.YES_WITH_EX,
            ))
        else:
            try:
                conditions.append(Profile.children_status == ChildrenStatus(ch))
            except ValueError:
                pass

    # Фильтр: проживание (тollerance для NULL — старые анкеты без заполненного residence_status)
    if filters.get("residence") and filters["residence"] != "any":
        from bot.db.models import ResidenceStatus
        from sqlalchemy import or_ as _or_res
        try:
            conditions.append(_or_res(
                Profile.residence_status == ResidenceStatus(filters["residence"]),
                Profile.residence_status.is_(None),
            ))
        except ValueError:
            pass

    # Фильтр: регион / страна — по city_code/country или ILIKE по city/family_region
    if filters.get("region"):
        region_val = filters["region"]
        from sqlalchemy import or_

        # Коды зарубежных стран и «Европа», «Другая»
        _country_codes = {
            "usa", "russia", "kazakhstan", "kyrgyzstan",
            "tajikistan", "turkmenistan", "europe",
        }
        # Коды 13 областей Узбекистана
        _uz_region_codes = {
            "tashkent", "tashkent_region", "samarkand",
            "fergana", "andijan", "namangan", "bukhara",
            "kashkadarya", "surkhandarya", "khorezm",
            "karakalpakstan", "jizzakh", "sirdarya",
            "nukus",  # legacy
        }

        if region_val == "any":
            pass  # фильтр не применяется
        elif region_val == "uzbekistan":
            # Все узбекистанские анкеты — любой регион Узбекистана или страна UZ
            uz_codes = list(_uz_region_codes) + ["uz_other", "uzbekistan"]
            conditions.append(or_(
                Profile.country == "uzbekistan",
                Profile.city_code.in_(uz_codes),
                # Старые анкеты без country могли быть узбекистанскими
                Profile.country.is_(None),
            ))
        elif region_val in _country_codes:
            # Иностранная страна — совпадение по country или city_code
            conditions.append(or_(
                Profile.country == region_val,
                Profile.city_code == region_val,
            ))
        elif region_val == "other":
            # Другая страна — пользователь ввёл свободно
            conditions.append(or_(
                Profile.country == "other",
                Profile.city_code == "other",
            ))
        else:
            # Конкретный регион Узбекистана — ILIKE всеми вариантами написания
            region_map_ru = {
                "tashkent":        "%ташкент%",
                "tashkent_region": "%ташкентск%",
                "samarkand":       "%самарканд%",
                "fergana":         "%ферган%",
                "andijan":         "%андижан%",
                "namangan":        "%наманган%",
                "bukhara":         "%бухар%",
                "kashkadarya":     "%кашкадарь%",
                "surkhandarya":    "%сурхандарь%",
                "khorezm":         "%хорезм%",
                "karakalpakstan":  "%каракалпак%",
                "jizzakh":         "%джизак%",
                "sirdarya":        "%сырдарь%",
                "nukus":           "%нукус%",
            }
            region_map_uz = {
                "tashkent":        "%toshkent%",
                "tashkent_region": "%toshkent viloyat%",
                "samarkand":       "%samarqand%",
                "fergana":         "%farg'ona%",
                "andijan":         "%andijon%",
                "namangan":        "%namangan%",
                "bukhara":         "%buxoro%",
                "kashkadarya":     "%qashqadaryo%",
                "surkhandarya":    "%surxondaryo%",
                "khorezm":         "%xorazm%",
                "karakalpakstan":  "%qoraqalpog'%",
                "jizzakh":         "%jizzax%",
                "sirdarya":        "%sirdaryo%",
                "nukus":           "%nukus%",
            }
            region_map_en = {
                "tashkent":        "%tashkent%",
                "tashkent_region": "%tashkent region%",
                "samarkand":       "%samarkand%",
                "fergana":         "%fergana%",
                "andijan":         "%andijan%",
                "namangan":        "%namangan%",
                "bukhara":         "%bukhara%",
                "kashkadarya":     "%kashkadarya%",
                "surkhandarya":    "%surkhandarya%",
                "khorezm":         "%khorezm%",
                "karakalpakstan":  "%karakalpak%",
                "jizzakh":         "%jizzakh%",
                "sirdarya":        "%sirdarya%",
                "nukus":           "%nukus%",
            }
            pat_ru = region_map_ru.get(region_val, f"%{region_val}%")
            pat_uz = region_map_uz.get(region_val, f"%{region_val}%")
            pat_en = region_map_en.get(region_val, f"%{region_val}%")
            conditions.append(or_(
                Profile.city_code == region_val,
                Profile.family_region.ilike(pat_ru),
                Profile.family_region.ilike(pat_uz),
                Profile.family_region.ilike(pat_en),
                Profile.city.ilike(pat_ru),
                Profile.city.ilike(pat_uz),
                Profile.city.ilike(pat_en),
            ))

    # Фильтр: национальность
    if filters.get("nationality") and filters["nationality"] != "any":
        conditions.append(Profile.nationality == filters["nationality"])

    query = select(Profile).where(*conditions).order_by(
        case((Profile.vip_status == VipStatus.ACTIVE, 0), else_=1),
        desc(Profile.published_at),
    )

    result = await session.execute(query)
    profiles = result.scalars().all()

    # Получаем требования пользователя для scoring
    my_profile = await _get_user_profile(session, user_id)
    user_req = None
    if my_profile:
        user_req = await _get_user_requirement(session, my_profile.id)

    return profiles, user_req


async def _safe_show_card(callback: CallbackQuery, text: str, kb: InlineKeyboardMarkup) -> None:
    """Показать карточку: edit_text, фолбэк — delete+answer (перекрывает фото↔текст)."""
    try:
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        return
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    try:
        await callback.message.delete()
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    try:
        await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка показа анкеты: {e}")


async def _rebuild_search_snapshot(
    session: AsyncSession, state: FSMContext, user_id: int
) -> list[int]:
    """Пересобрать список ID анкет в FSM (снимок порядка)."""
    data = await state.get_data()
    filters = data.get("search_filters", {})
    search_type = data.get("search_type", "daughter")
    is_guest = data.get("is_guest", False)

    profiles, user_req = await _build_search_query(
        session, user_id, search_type, filters, is_guest=is_guest
    )

    scored = [(p, compute_match_score(p, user_req)) for p in profiles]
    scored.sort(key=lambda x: (
        0 if x[0].vip_status == VipStatus.ACTIVE else 1,
        -(x[0].vip_expires_at.timestamp()
          if x[0].vip_status == VipStatus.ACTIVE and x[0].vip_expires_at else 0),
        -x[1],
        -(x[0].published_at.timestamp() if x[0].published_at else 0),
    ))

    ids = [p.id for p, _ in scored]
    scores = {p.id: s for p, s in scored}
    await state.update_data(
        search_results=ids,
        search_scores=scores,
        current_index=0,
        search_offset=0,  # back-compat
    )
    return ids


async def _show_search_results(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext, lang: str
):
    """Показать текущую анкету. Список ID хранится в FSM (search_results)."""
    user_id = callback.from_user.id
    data = await state.get_data()

    ids: list[int] = data.get("search_results") or []

    # Нет снимка — собираем
    if not ids:
        ids = await _rebuild_search_snapshot(session, state, user_id)
        data = await state.get_data()

    total = len(ids)
    idx = data.get("current_index", 0)

    # Пустой результат
    if total == 0:
        text = "🔍 Anketalar topilmadi." if lang == "uz" else "🔍 Анкеты не найдены."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔧 Filtrlarni o'zgartirish" if lang == "uz" else "🔧 Изменить фильтры",
                callback_data="search:manual",
            )],
            [InlineKeyboardButton(
                text="👀 Barchasini ko'rish" if lang == "uz" else "👀 Показать все",
                callback_data="search:all",
            )],
            [InlineKeyboardButton(
                text="🏠 Menyu" if lang == "uz" else "🏠 Меню",
                callback_data="menu:main",
            )],
        ])
        await _safe_show_card(callback, text, kb)
        await callback.answer()
        return

    # Индекс за границей — экран «просмотрели все»
    if idx >= total:
        text = (
            f"🔍 Siz barcha {total} ta anketani ko'rdingiz!"
            if lang == "uz" else
            f"🔍 Вы просмотрели все {total} анкет!"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Boshidan boshlash" if lang == "uz" else "🔄 Начать сначала",
                callback_data="search:restart",
            )],
            [InlineKeyboardButton(
                text="🔧 Filtrlarni o'zgartirish" if lang == "uz" else "🔧 Изменить фильтры",
                callback_data="search:manual",
            )],
            [InlineKeyboardButton(
                text="🏠 Menyu" if lang == "uz" else "🏠 Меню",
                callback_data="menu:main",
            )],
        ])
        await _safe_show_card(callback, text, kb)
        await callback.answer()
        return

    # Подгружаем анкету из БД по ID
    profile_id = ids[idx]
    profile = await session.get(Profile, profile_id)

    if not profile:
        # Анкета удалена/скрыта — пропускаем
        ids.pop(idx)
        await state.update_data(search_results=ids)
        if not ids:
            await _show_search_results(callback, session, state, lang)
            return
        if idx >= len(ids):
            await state.update_data(current_index=len(ids) - 1, search_offset=len(ids) - 1)
        await _show_search_results(callback, session, state, lang)
        return

    scores: dict = data.get("search_scores") or {}
    score = scores.get(profile_id) or scores.get(str(profile_id)) or 50

    # Иллюзия загрузки — только при первом показе
    if idx == 0 and callback.data in ("search:my_req", "search:manual", "search:all",
                                      "search:restart", "filter:go", None):
        loading = (
            "🔍 Siz uchun eng yaxshilarini tanlamoqdamiz..."
            if lang == "uz" else
            "🔍 Подбираем лучшие варианты для вас..."
        )
        try:
            await callback.message.edit_text(loading)
            await asyncio.sleep(0.8)
        except Exception as _e:
            logger.debug("ignored: %s", _e)
    counter = (
        f"🔍 Anketa {idx + 1} / {total}"
        if lang == "uz" else
        f"🔍 Анкета {idx + 1} из {total}"
    )
    card_text = format_anketa_public(profile, score, lang)
    full_text = counter + "\n\n" + card_text

    kb = profile_card_kb(
        profile.id, lang,
        profile.display_id or "",
        show_prev=(idx > 0),
        show_next=(idx < total - 1),
        current=idx + 1,
        total=total,
    )

    await _safe_show_card(callback, full_text, kb)

    # Ритм: каждые 5 анкет — мотивирующая фраза
    if idx > 0 and idx % 5 == 0:
        import random
        if lang == "uz":
            phrases = [
                "🔥 Hozir qiziqarliroqlari keladi!",
                "💎 Maxsus siz uchun tanlab oldik",
                "✨ Yanada yaxshilari oldinda!",
            ]
        else:
            phrases = [
                "🔥 Сейчас пойдут интереснее!",
                "💎 Специально подобрали для вас",
                "✨ Впереди ещё лучше!",
            ]
        try:
            await callback.message.answer(random.choice(phrases))
            await asyncio.sleep(0.5)
        except Exception as _e:
            logger.debug("ignored: %s", _e)
    # Счётчик просмотров + уведомление владельцу
    profile.views_count = (profile.views_count or 0) + 1
    try:
        await _notify_owner_view(callback.bot, session, profile, user_id)
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await session.commit()
    try:
        await callback.answer()
    except Exception as _e:
        logger.debug("ignored: %s", _e)


# ── Навигация: вперёд / назад / рестарт ──


@router.callback_query(F.data.startswith("search_nav:"))
async def search_nav(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Двусторонняя навигация по снимку search_results."""
    import random
    lang = await get_lang(session, callback.from_user.id)
    direction = callback.data.split(":", 1)[1]  # "prev" | "next"

    data = await state.get_data()
    ids: list[int] = data.get("search_results") or []
    idx = data.get("current_index", 0)
    total = len(ids)

    if total == 0:
        await _show_search_results(callback, session, state, lang)
        return

    if direction == "prev":
        if idx <= 0:
            await callback.answer(
                "⬅️ Bu birinchi anketa" if lang == "uz" else "⬅️ Это первая анкета",
                show_alert=False,
            )
            return
        idx -= 1
    else:  # next
        if idx >= total - 1:
            await callback.answer(
                "➡️ Boshqa anketalar yo'q" if lang == "uz" else "➡️ Больше анкет нет",
                show_alert=False,
            )
            return
        idx += 1
        # Микро-реакция «Следующая»
        if lang == "uz":
            phrases = [
                "Qidiramiz... 🔍",
                "Keyingisi! 👉",
                "Mos kelmadi — bo'ladi 😊",
                "Qidirishda davom etamiz 🚀",
            ]
        else:
            phrases = [
                "Ищем дальше... 🔍",
                "Следующая! 👉",
                "Не подошло — бывает 😊",
                "Продолжаем поиск 🚀",
            ]
        try:
            await callback.answer(random.choice(phrases), show_alert=False)
        except Exception as _e:
            logger.debug("ignored: %s", _e)
    await state.update_data(current_index=idx, search_offset=idx)
    await _show_search_results(callback, session, state, lang)


@router.callback_query(F.data == "search:restart")
async def search_restart(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Начать поиск сначала — пересобрать снимок."""
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(search_results=None, search_scores=None,
                            current_index=0, search_offset=0)
    await _show_search_results(callback, session, state, lang)


# Back-compat: старый callback «Следующая ➡️»


@router.callback_query(F.data == "search:next_one")
async def search_next_one_legacy(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    import random
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    ids: list[int] = data.get("search_results") or []
    idx = data.get("current_index", 0)
    if ids and idx >= len(ids) - 1:
        await callback.answer(
            "➡️ Boshqa anketalar yo'q" if lang == "uz" else "➡️ Больше анкет нет",
            show_alert=False,
        )
        return
    if lang == "uz":
        phrases = [
            "Qidiramiz... 🔍",
            "Keyingisi! 👉",
            "Mos kelmadi — bo'ladi 😊",
            "Qidirishda davom etamiz 🚀",
        ]
    else:
        phrases = [
            "Ищем дальше... 🔍",
            "Следующая! 👉",
            "Не подошло — бывает 😊",
            "Продолжаем поиск 🚀",
        ]
    try:
        await callback.answer(random.choice(phrases), show_alert=False)
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await state.update_data(current_index=idx + 1, search_offset=idx + 1)
    await _show_search_results(callback, session, state, lang)


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    """Тихий ответ на кнопку-счётчик."""
    await callback.answer()


# Совместимость со старой пагинацией search_page:N


@router.callback_query(F.data.startswith("search_page:"))
async def search_page_compat(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    page = int(callback.data.split(":")[1])
    offset = page * PROFILES_PER_PAGE
    await state.update_data(search_offset=offset)
    lang = await get_lang(session, callback.from_user.id)
    await _show_search_results(callback, session, state, lang)


# ══════════════════════════════════════════════════════════
#  Избранное, интерес, контакт, пропуск — без изменений
# ══════════════════════════════════════════════════════════


@router.callback_query(F.data.startswith("fav:"))
async def add_favorite(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    profile_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    lang = await get_lang(session, user_id)

    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.profile_id == profile_id,
        )
    )
    existing = result.scalar_one_or_none()

    if not existing:
        fav = Favorite(user_id=user_id, profile_id=profile_id)
        session.add(fav)
        await session.commit()

        # Уведомление владельцу
        profile = await session.get(Profile, profile_id)
        if profile:
            try:
                await _notify_owner_favorite(callback.bot, session, profile, user_id)
            except Exception as _e:
                logger.debug("ignored: %s", _e)
    # Микро-реакция — случайная фраза
    import random
    if existing:
        toast = "❤️ " + ("Allaqachon sevimlilarda" if lang == "uz" else "Уже в избранном")
    else:
        if lang == "uz":
            phrases = [
                "❤️ Yaxshi tanlov! 😉",
                "❤️ Ajoyib! Saqlandi 👌",
                "❤️ Saqlandi! Ko'ramiz 😊",
                "❤️ Did bor! 🌟",
            ]
        else:
            phrases = [
                "❤️ Хороший вкус! 😉",
                "❤️ Отличный выбор 👌",
                "❤️ Сохранено! Посмотрим 😊",
                "❤️ Есть вкус! 🌟",
            ]
        toast = random.choice(phrases)
    await callback.answer(toast, show_alert=False)

    # Автоматически к следующей анкете (если не последняя)
    data = await state.get_data()
    ids: list = data.get("search_results") or []
    idx = data.get("current_index", data.get("search_offset", 0))
    if ids and idx >= len(ids) - 1:
        # Уже на последней — просто перерисовываем текущую
        await _show_search_results(callback, session, state, lang)
        return
    await state.update_data(current_index=idx + 1, search_offset=idx + 1)
    await _show_search_results(callback, session, state, lang)


@router.callback_query(F.data.startswith("unfav:"))
async def remove_favorite(callback: CallbackQuery, session: AsyncSession):
    """Удалить из избранного."""
    profile_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    lang = await get_lang(session, user_id)

    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.profile_id == profile_id,
        )
    )
    fav = result.scalar_one_or_none()
    if fav:
        await session.delete(fav)
        await session.commit()
        text = "💔 Tanlanganlardan o'chirildi" if lang == "uz" else "💔 Удалено из избранного"
        await callback.answer(text, show_alert=False)
    else:
        await callback.answer("—")


@router.callback_query(F.data.startswith("interest:"))
async def express_interest(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Пользователь нажал «Узнать подробнее» — уведомляем семью."""
    target_profile_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    lang = await get_lang(session, user_id)

    target_profile = await session.get(Profile, target_profile_id)
    if not target_profile:
        await callback.answer("Анкета не найдена")
        return

    cr = ContactRequest(
        requester_user_id=user_id,
        target_profile_id=target_profile_id,
        status=RequestStatus.PENDING,
    )
    session.add(cr)
    target_profile.requests_count = (target_profile.requests_count or 0) + 1
    await session.commit()

    # Уведомление владельца о запросе контакта
    try:
        await _notify_owner_contact_request(bot, session, target_profile)
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    result = await session.execute(
        select(Profile).where(Profile.user_id == user_id).limit(1)
    )
    requester_profile = result.scalar_one_or_none()

    if target_profile.user_id:
        target_lang = "ru"
        result = await session.execute(select(User).where(User.id == target_profile.user_id))
        target_user = result.scalar_one_or_none()
        if target_user and target_user.language:
            target_lang = target_user.language.value

        age_str = "?"
        edu_str = "—"
        occ_str = "—"
        req_city = "—"
        res_str = "—"

        if requester_profile:
            if requester_profile.birth_year:
                age_str = age_text(calculate_age(requester_profile.birth_year))
            edu_map = {"secondary": "среднее", "vocational": "среднее спец.", "higher": "высшее", "studying": "учится"}
            if requester_profile.education:
                edu_str = edu_map.get(requester_profile.education.value, "—")
            occ_str = occupation_label(requester_profile.occupation, target_lang)
            req_city = requester_profile.city or "—"
            if requester_profile.residence_status:
                res_map = {"uzbekistan": "🇺🇿 Узбекистан", "cis": "🇷🇺 СНГ", "usa": "🇺🇸 США", "europe": "🌍 Европа"}
                res_str = res_map.get(requester_profile.residence_status.value, "—")

        try:
            await bot.send_message(
                target_profile.user_id,
                t("notify_interest", target_lang,
                    display_id=target_profile.display_id,
                    city=req_city,
                    age=age_str,
                    education=edu_str,
                    occupation=occ_str,
                    requester_city=req_city,
                    residence=res_str,
                ),
            )
        except Exception as _e:
            logger.debug("ignored: %s", _e)
    region = "🇺🇿 Узбекистан"
    moderator = config.moderator_tashkent
    hours = "08:00–00:00 (UZT)"

    if requester_profile and requester_profile.residence_status:
        res = requester_profile.residence_status.value
        if res == "cis":
            region = "🇷🇺 СНГ"
            moderator = config.moderator_cis
            hours = "08:00–00:00 (MSK)"
        elif res == "usa":
            region = "🇺🇸 США"
            moderator = config.moderator_usa
            hours = "08:00–00:00 (EST)"
        elif res == "europe":
            region = "🌍 Европа"
            moderator = config.moderator_europe
            hours = "08:00–00:00 (CET)"

    await callback.message.answer(
        t("contact_moderator", lang, region=region, moderator=moderator, hours=hours),
    )

    await callback.message.answer(
        t("payment_prompt", lang, display_id=target_profile.display_id or "—"),
        reply_markup=get_contact_kb(target_profile_id, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("getcontact:"))
async def get_contact_payment(callback: CallbackQuery, session: AsyncSession):
    """Шаг 13 — переход к оплате для получения контакта."""
    profile_id = int(callback.data.split(":")[1])
    lang = await get_lang(session, callback.from_user.id)

    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена")
        return

    result = await session.execute(
        select(Profile).where(Profile.user_id == callback.from_user.id).limit(1)
    )
    user_profile = result.scalar_one_or_none()

    display_id = profile.display_id or "—"
    residence = user_profile.residence_status.value if user_profile and user_profile.residence_status else "uzbekistan"

    from bot.keyboards.inline import payment_uz_kb, payment_cis_kb, payment_intl_kb

    if residence in ("usa", "europe", "citizenship_other", "other_country"):
        text = t("payment_intl", lang, display_id=display_id)
        kb = payment_intl_kb(profile_id, lang)
    elif residence == "cis":
        text = t("payment_cis", lang, display_id=display_id)
        kb = payment_cis_kb(profile_id, lang)
    else:
        text = t("payment_uz", lang, display_id=display_id)
        kb = payment_uz_kb(profile_id, lang)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_profile:"))
async def back_to_profile(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Назад из подменю контакта — вернуть карточку анкеты."""
    lang = await get_lang(session, callback.from_user.id)
    await _show_search_results(callback, session, state, lang)
    await callback.answer()


# ══════════════════════════════════════════════════════════
#  Узнать контакт — выбор между модератором или оплатой картой
# ══════════════════════════════════════════════════════════


@router.callback_query(F.data.startswith("get_contact:"))
async def get_contact(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Пользователь жмёт 💌 — меню: задать вопрос или запросить контакт."""
    profile_id = int(callback.data.split(":")[1])
    lang = await get_lang(session, callback.from_user.id)

    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена" if lang == "ru" else "Anketa topilmadi")
        return

    display_id = profile.display_id or "—"

    if lang == "uz":
        text = (
            f"🔖 <b>{display_id}</b>\n\n"
            f"Bu anketa sizni qiziqtirdimi?\n\n"
            f"Nima qilmoqchisiz?"
        )
        buttons = [
            [InlineKeyboardButton(
                text="💬 Operatorga savol berish",
                callback_data=f"ask_op:{profile_id}",
            )],
            [InlineKeyboardButton(
                text="📤 Kontakt so'rash",
                callback_data=f"req_contact:{profile_id}",
            )],
            [InlineKeyboardButton(
                text="🔙 Orqaga",
                callback_data=f"back_to_profile:{profile_id}",
            )],
        ]
    else:
        text = (
            f"🔖 <b>{display_id}</b>\n\n"
            f"Вас заинтересовала эта анкета!\n\n"
            f"Что хотите сделать?"
        )
        buttons = [
            [InlineKeyboardButton(
                text="💬 Задать вопрос оператору",
                callback_data=f"ask_op:{profile_id}",
            )],
            [InlineKeyboardButton(
                text="📤 Запросить контакт",
                callback_data=f"req_contact:{profile_id}",
            )],
            [InlineKeyboardButton(
                text="🔙 Назад",
                callback_data=f"back_to_profile:{profile_id}",
            )],
        ]

    try:
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML",
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


async def _next_req_number(session: AsyncSession) -> str:
    """Сгенерировать следующий порядковый номер ЗАП-NNN."""
    try:
        count_res = await session.execute(
            select(sa_func.count()).select_from(ContactRequest)
        )
        count = (count_res.scalar() or 0) + 1
    except Exception as _e:
        logger.debug("ignored: %s", _e)
        count = 1
    return f"ЗАП-{count:03d}"


@router.callback_query(F.data.startswith("ask_op:"))
async def ask_operator(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Пользователь жмёт «💬 Задать вопрос» — ждём текст вопроса."""
    profile_id = int(callback.data.split(":")[1])
    lang = await get_lang(session, callback.from_user.id)

    await state.update_data(question_profile_id=profile_id)
    await state.set_state(ContactStates.waiting_question)

    text = "💬 Savolingizni yozing:" if lang == "uz" else "💬 Напишите ваш вопрос:"
    try:
        await callback.message.edit_text(text)
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


@router.message(ContactStates.waiting_question, F.text)
async def send_question(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Пользователь прислал текст вопроса — уведомляем всех модераторов."""
    from bot.config import get_all_moderator_ids

    data = await state.get_data()
    profile_id = data.get("question_profile_id")
    profile = await session.get(Profile, profile_id) if profile_id else None
    display_id = (profile.display_id if profile else "—") or "—"
    lang = await get_lang(session, message.from_user.id)

    req_number = await _next_req_number(session)
    await state.update_data(req_number=req_number, req_profile_id=profile_id)

    user_id = message.from_user.id
    mod_text = (
        f"💬 <b>ВОПРОС ОТ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"📋 #{req_number}\n"
        f"🔖 {display_id}\n"
        f"👤 ID: <code>{user_id}</code>\n\n"
        f"❓ {message.text}"
    )
    mod_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="💬 Ответить",
            callback_data=f"op_reply:{user_id}:{profile_id}:{req_number}",
        )],
        [InlineKeyboardButton(
            text="📤 Отправить реквизиты",
            callback_data=f"op_send_req:{user_id}:{profile_id}:{req_number}",
        )],
        [InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"op_reject:{user_id}:{profile_id}:{req_number}",
        )],
    ])

    for mod_id in get_all_moderator_ids():
        if not mod_id:
            continue
        try:
            await bot.send_message(mod_id, mod_text, reply_markup=mod_kb, parse_mode="HTML")
        except Exception as _e:
            logger.debug("ignored: %s", _e)

    if lang == "uz":
        reply = (
            f"✅ Savolingiz yuborildi!\n"
            f"📋 #{req_number}\n\n"
            f"Operator tez orada javob beradi. 🤝"
        )
    else:
        reply = (
            f"✅ Вопрос отправлен!\n"
            f"📋 #{req_number}\n\n"
            f"Оператор ответит в ближайшее время. 🤝"
        )
    await message.answer(reply, parse_mode="HTML")
    await state.set_state(None)


@router.callback_query(F.data.startswith("req_contact:"))
async def request_contact(callback: CallbackQuery, session: AsyncSession, state: FSMContext, bot: Bot):
    """Пользователь жмёт «📤 Запросить контакт» — создаём запись + уведомляем модераторов."""
    from bot.config import get_all_moderator_ids
    import datetime

    profile_id = int(callback.data.split(":")[1])
    lang = await get_lang(session, callback.from_user.id)

    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена" if lang == "ru" else "Anketa topilmadi")
        return

    display_id = profile.display_id or "—"
    req_number = await _next_req_number(session)

    # Сохранить запрос в БД
    try:
        cr = ContactRequest(
            requester_user_id=callback.from_user.id,
            target_profile_id=profile_id,
            status=RequestStatus.PENDING,
            display_id=req_number,
        )
        session.add(cr)
        profile.requests_count = (profile.requests_count or 0) + 1
        await session.commit()
    except Exception as _e:
        logger.debug("ignored: %s", _e)

    await state.update_data(contact_req_number=req_number)

    # Карточка модератору
    age = (datetime.datetime.now().year - profile.birth_year) if profile.birth_year else "?"
    edu_raw = profile.education.value if profile.education else "—"
    rel_raw = profile.religiosity.value if profile.religiosity else "—"
    mar_raw = profile.marital_status.value if profile.marital_status else "—"
    occ_raw = occupation_label(profile.occupation, "ru")

    mod_text = (
        f"💌 <b>НОВЫЙ ЗАПРОС #{req_number}</b>\n\n"
        f"КТО ИЩЕТ:\n"
        f"👤 ID: <code>{callback.from_user.id}</code>\n\n"
        f"НА КОГО:\n"
        f"🔖 {display_id}\n"
        f"🪪 {profile.name or '—'} · {age} · {profile.city or '—'}\n"
        f"🎓 {edu_raw} · 💼 {occ_raw}\n"
        f"🕌 {rel_raw} · 💍 {mar_raw}"
    )
    mod_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📤 Отправить реквизиты",
            callback_data=f"op_send_req:{callback.from_user.id}:{profile_id}:{req_number}",
        )],
        [InlineKeyboardButton(
            text="💬 Написать пользователю",
            callback_data=f"op_reply:{callback.from_user.id}:{profile_id}:{req_number}",
        )],
        [InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"op_reject:{callback.from_user.id}:{profile_id}:{req_number}",
        )],
    ])

    for mod_id in get_all_moderator_ids():
        if not mod_id:
            continue
        try:
            await bot.send_message(mod_id, mod_text, reply_markup=mod_kb, parse_mode="HTML")
        except Exception as _e:
            logger.debug("ignored: %s", _e)

    if lang == "uz":
        text = (
            f"✅ So'rovingiz yuborildi!\n\n"
            f"📋 #{req_number}\n\n"
            f"Operator tez orada\n"
            f"siz bilan bog'lanadi. 🤝"
        )
    else:
        text = (
            f"✅ Запрос отправлен!\n\n"
            f"📋 #{req_number}\n\n"
            f"Оператор свяжется с вами\n"
            f"в ближайшее время. 🤝"
        )

    try:
        await callback.message.edit_text(text, parse_mode="HTML")
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


# ══════════════════════════════════════════════════════════
#  Скриншот оплаты
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("send_screenshot:"))
async def send_screenshot_start(callback: CallbackQuery, state: FSMContext):
    """Пользователь жмёт «📸 Отправить скриншот» — ждём фото."""
    parts = callback.data.split(":")
    profile_id = int(parts[1])
    req_number = parts[2] if len(parts) > 2 else "—"
    await state.update_data(
        screenshot_profile_id=profile_id,
        screenshot_req_number=req_number,
    )
    await state.set_state(ContactStates.waiting_screenshot)
    try:
        await callback.message.edit_text(
            f"📸 Отправьте скриншот оплаты\n📋 #{req_number}",
            parse_mode="HTML",
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


@router.message(ContactStates.waiting_screenshot, F.photo)
async def receive_screenshot(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Пользователь прислал скриншот — пересылаем всем операторам с кнопками."""
    from bot.config import get_all_moderator_ids
    data = await state.get_data()
    profile_id = data.get("screenshot_profile_id")
    req_number = data.get("screenshot_req_number") or "—"
    profile = await session.get(Profile, profile_id) if profile_id else None
    display_id = (profile.display_id if profile else "—") or "—"

    photo_id = message.photo[-1].file_id
    user_id = message.from_user.id

    mod_caption = (
        f"📸 <b>СКРИНШОТ ОПЛАТЫ</b>\n\n"
        f"📋 #{req_number}\n"
        f"👤 ID: <code>{user_id}</code>\n"
        f"🔖 {display_id}"
    )
    mod_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Подтвердить — передать контакт",
            callback_data=f"confirm_pay:{user_id}:{profile_id}:{req_number}",
        )],
        [InlineKeyboardButton(
            text="❌ Оплата не подтверждена",
            callback_data=f"reject_pay:{user_id}:{profile_id}:{req_number}",
        )],
    ])

    for mod_id in get_all_moderator_ids():
        if not mod_id:
            continue
        try:
            await bot.send_photo(mod_id, photo_id, caption=mod_caption, reply_markup=mod_kb, parse_mode="HTML")
        except Exception as _e:
            logger.debug("ignored: %s", _e)

    await message.answer(
        f"✅ Скриншот получен!\n"
        f"📋 #{req_number}\n\n"
        f"Оператор проверит оплату\n"
        f"и передаст контакт. 🤝",
        parse_mode="HTML",
    )
    await state.set_state(None)
