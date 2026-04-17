"""Поиск анкет — 3 режима: по требованиям, ручные фильтры, все."""

import random
import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
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
)
from bot.utils.helpers import age_text, calculate_age, format_anketa_public
from bot.config import config
# SearchStates больше не используется — возраст теперь через кнопки

logger = logging.getLogger(__name__)

router = Router()


# ── Уведомления владельцу анкеты ──

NOTIFY_AT_VIEWS = {1, 5, 10, 25, 50, 100, 200, 500}


async def _notify_owner_view(bot: Bot, session: AsyncSession, profile: Profile, viewer_id: int):
    """Уведомляет владельца о просмотре при 1, 5, 10, 25, 50, 100..."""
    views = profile.views_count or 0
    if views not in NOTIFY_AT_VIEWS and views % 100 != 0:
        return
    if not profile.user_id or profile.user_id == viewer_id:
        return

    result = await session.execute(select(User).where(User.id == profile.user_id))
    user = result.scalar_one_or_none()
    lang = user.language.value if user and user.language else "ru"

    display_id = profile.display_id or "—"
    if lang == "uz":
        text = (
            f"👀 <b>Anketangizga qiziqish bor!</b>\n\n"
            f"🔖 {display_id}\n"
            f"Ko'rishlar soni: <b>{views}</b>\n\n"
            f"Anketangiz ishlayapti! 🤲"
        )
    else:
        text = (
            f"👀 <b>Вашу анкету просматривают!</b>\n\n"
            f"🔖 {display_id}\n"
            f"Просмотров уже: <b>{views}</b>\n\n"
            f"Ваша анкета работает! 🤲"
        )
    try:
        await bot.send_message(profile.user_id, text)
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

PROFILES_PER_PAGE = 3


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
            # Проживание
            "uzbekistan": "Узбекистан", "cis": "СНГ", "usa": "США",
            "europe": "Европа", "other_country": "Другое", "other": "Другое",
            # Регионы Узбекистана
            "tashkent": "Ташкент", "samarkand": "Самарканд",
            "fergana": "Фергана", "bukhara": "Бухара",
            "namangan": "Наманган", "andijan": "Андижан", "nukus": "Нукус",
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
            # Проживание
            "uzbekistan": "O'zbekiston", "cis": "MDH", "usa": "AQSH",
            "europe": "Yevropa", "other_country": "Boshqa", "other": "Boshqa",
            # Регионы Узбекистана
            "tashkent": "Toshkent", "samarkand": "Samarqand",
            "fergana": "Farg'ona", "bukhara": "Buxoro",
            "namangan": "Namangan", "andijan": "Andijon", "nukus": "Nukus",
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
    except Exception:
        pass


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
    await state.update_data(search_filters={}, search_offset=0)

    await show_search_filters(callback, session, state)


# ── Фильтр: возраст ──
@router.callback_query(F.data == "filter:age")
async def filter_age(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("18–23", "fval:age:18_23"),
        ("24–27", "fval:age:24_27"),
        ("28–35", "fval:age:28_35"),
        ("36–45", "fval:age:36_45"),
        ("45+",   "fval:age:45plus"),
    ]
    title = "Возраст:" if lang == "ru" else "Yosh:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Фильтр: религиозность ──
@router.callback_query(F.data == "filter:religion")
async def filter_religion(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("Практикующий" if lang == "ru" else "Amaliyotchi", "fval:religion:practicing"),
        ("Умеренный" if lang == "ru" else "Mo'tadil",       "fval:religion:moderate"),
        ("Светский" if lang == "ru" else "Dunyoviy",        "fval:religion:secular"),
    ]
    title = "Религиозность:" if lang == "ru" else "Dindorlik:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Фильтр: образование ──
@router.callback_query(F.data == "filter:education")
async def filter_education(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("Среднее" if lang == "ru" else "O'rta",                    "fval:education:secondary"),
        ("Среднее специальное" if lang == "ru" else "O'rta maxsus", "fval:education:vocational"),
        ("Высшее" if lang == "ru" else "Oliy",                      "fval:education:higher"),
        ("Студент" if lang == "ru" else "Talaba",                   "fval:education:studying"),
    ]
    title = "Образование:" if lang == "ru" else "Ma'lumot:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Фильтр: семейное положение ──
@router.callback_query(F.data == "filter:marital")
async def filter_marital(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("Не был(а) в браке" if lang == "ru" else "Turmush qurmagan", "fval:marital:never_married"),
        ("Разведён/а" if lang == "ru" else "Ajrashgan", "fval:marital:divorced"),
        ("Вдовец/Вдова" if lang == "ru" else "Beva", "fval:marital:widowed"),
    ]
    title = "Семейное положение:" if lang == "ru" else "Oilaviy holat:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Фильтр: проживание ──
@router.callback_query(F.data == "filter:residence")
async def filter_residence(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("Узбекистан" if lang == "ru" else "O'zbekiston", "filter:residence:uzb"),
        ("🌍 За рубежом" if lang == "ru" else "🌍 Chet elda", "fval:region:abroad"),
    ]
    title = "Где проживает:" if lang == "ru" else "Yashash joyi:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Узбекистан → выбор региона ──
@router.callback_query(F.data == "filter:residence:uzb")
async def filter_residence_uzb(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("Ташкент" if lang == "ru" else "Toshkent",       "fval:region:tashkent"),
        ("Самарканд" if lang == "ru" else "Samarqand",     "fval:region:samarkand"),
        ("Фергана" if lang == "ru" else "Farg'ona",        "fval:region:fergana"),
        ("Бухара" if lang == "ru" else "Buxoro",           "fval:region:bukhara"),
        ("Наманган" if lang == "ru" else "Namangan",       "fval:region:namangan"),
        ("Андижан" if lang == "ru" else "Andijon",         "fval:region:andijan"),
        ("Нукус" if lang == "ru" else "Nukus",             "fval:region:nukus"),
        ("Другой город" if lang == "ru" else "Boshqa shahar", "fval:region:other"),
        ("Не важно" if lang == "ru" else "Muhim emas",     "fval:region:any"),
    ]
    title = "Выберите регион:" if lang == "ru" else "Hududni tanlang:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Фильтр: национальность ──
@router.callback_query(F.data == "filter:nationality")
async def filter_nationality(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("Узбек" if lang == "ru" else "O'zbek", "fval:nationality:uzbek"),
        ("Русский" if lang == "ru" else "Rus", "fval:nationality:russian"),
        ("Кореец" if lang == "ru" else "Koreys", "fval:nationality:korean"),
        ("Таджик" if lang == "ru" else "Tojik", "fval:nationality:tajik"),
        ("Казах" if lang == "ru" else "Qozoq", "fval:nationality:kazakh"),
        ("Другая" if lang == "ru" else "Boshqa", "fval:nationality:other"),
    ]
    title = "Национальность:" if lang == "ru" else "Millat:"
    await callback.message.edit_text(title, reply_markup=filter_option_kb(options, lang))
    await callback.answer()


# ── Фильтр: наличие детей ──
@router.callback_query(F.data == "filter:children")
async def filter_children(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    if lang == "uz":
        options = [
            ("👶 Farzandsiz",  "fval:children:no"),
            ("👶 Farzand bor", "fval:children:has_children"),
            ("✅ Muhim emas",  "fval:children:any"),
        ]
        title = "Farzandlar:"
    else:
        options = [
            ("👶 Без детей",  "fval:children:no"),
            ("👶 Есть дети",  "fval:children:has_children"),
            ("✅ Не важно",   "fval:children:any"),
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

    if value == "any":
        filters.pop(field, None)
    else:
        filters[field] = value

    # Возраст: при выборе/сбросе через кнопки — убираем старые age_from/age_to
    if field == "age":
        filters.pop("age_from", None)
        filters.pop("age_to", None)

    # Если выбран регион — также ставим residence = uzbekistan
    if field == "region":
        filters["residence"] = "uzbekistan"

    # Если выбрано residence (весь Узбекистан или другая страна) — убираем регион
    if field == "residence":
        filters.pop("region", None)

    await state.update_data(search_filters=filters)
    await show_search_filters(callback, session, state)


# ── Сбросить фильтры ──
@router.callback_query(F.data == "filter:clear")
async def filter_clear(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.update_data(search_filters={}, search_offset=0)

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

    await state.update_data(search_offset=0)
    await _show_search_results(callback, session, state, lang)


# ══════════════════════════════════════════════════════════
#  Показать все анкеты без фильтров
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "search:all")
async def search_all(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    lang = await get_lang(session, callback.from_user.id)
    my_profile = await _get_user_profile(session, callback.from_user.id)
    search_type = "daughter" if my_profile and my_profile.profile_type == ProfileType.SON else "son"
    await state.update_data(search_filters={}, search_offset=0, search_type=search_type)
    await _show_search_results(callback, session, state, lang)


# ══════════════════════════════════════════════════════════
#  Старый вход через menu:son (search:browse) — совместимость
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "search:browse")
async def search_browse_compat(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Совместимость со старым входом через 'Ищем невестку'."""
    lang = await get_lang(session, callback.from_user.id)
    my_profile = await _get_user_profile(session, callback.from_user.id)
    search_type = "daughter" if my_profile and my_profile.profile_type == ProfileType.SON else "son"
    await state.update_data(search_filters={}, search_offset=0, search_type=search_type)
    await _show_search_results(callback, session, state, lang)


# ══════════════════════════════════════════════════════════
#  ИЗМЕНЕНИЕ 5 — Показ результатов с пагинацией
# ══════════════════════════════════════════════════════════

async def _build_search_query(session: AsyncSession, user_id: int, search_type: str, filters: dict):
    """Построить query с фильтрами, вернуть (profiles, user_req)."""
    target_type = ProfileType.SON if search_type == "son" else ProfileType.DAUGHTER

    conditions = [
        Profile.status.in_([
            ProfileStatus.PUBLISHED,
            ProfileStatus.PENDING,  # временно показывать анкеты на проверке
        ]),
        Profile.is_active != False,   # включает True и NULL
        Profile.profile_type == target_type,
        Profile.user_id != user_id,
    ]

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

    # Фильтр: проживание
    if filters.get("residence") and filters["residence"] != "any":
        from bot.db.models import ResidenceStatus
        try:
            conditions.append(Profile.residence_status == ResidenceStatus(filters["residence"]))
        except ValueError:
            pass

    # Фильтр: регион (город) — по city_code или ILIKE по city/family_region
    if filters.get("region"):
        region_val = filters["region"]
        if region_val == "any":
            pass  # не фильтровать
        elif region_val == "other":
            # Анкеты с city_code="other" (пользователь ввёл город свободным текстом)
            conditions.append(Profile.city_code == "other")
        else:
            region_map = {
                "tashkent": "ташкент%", "samarkand": "самарканд%",
                "fergana": "ферган%", "bukhara": "бухар%",
                "namangan": "наманган%", "andijan": "андижан%", "nukus": "нукус%",
            }
            region_map_uz = {
                "tashkent": "toshkent%", "samarkand": "samarqand%",
                "fergana": "farg'ona%", "bukhara": "buxoro%",
                "namangan": "namangan%", "andijan": "andijon%", "nukus": "nukus%",
            }
            pat_ru = region_map.get(region_val, f"{region_val}%")
            pat_uz = region_map_uz.get(region_val, f"{region_val}%")
            from sqlalchemy import or_
            conditions.append(or_(
                Profile.city_code == region_val,
                Profile.family_region.ilike(pat_ru),
                Profile.family_region.ilike(pat_uz),
                Profile.city.ilike(pat_ru),
                Profile.city.ilike(pat_uz),
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

    # ── DEBUG (временно) ──
    logger.warning(
        f"SEARCH DEBUG: "
        f"search_type={search_type} "
        f"target_type={target_type} "
        f"total_found={len(profiles)} "
        f"filters={filters} "
        f"user_id={user_id}"
    )
    try:
        all_q = await session.execute(
            select(sa_func.count()).select_from(Profile).where(Profile.profile_type == target_type)
        )
        logger.warning(f"TOTAL IN DB for {target_type}: {all_q.scalar()}")
    except Exception as e:
        logger.warning(f"TOTAL IN DB error: {e}")

    return profiles, user_req


async def _show_search_results(callback: CallbackQuery, session: AsyncSession, state: FSMContext, lang: str):
    """Показать результаты поиска — 3 анкеты за раз."""
    data = await state.get_data()
    filters = data.get("search_filters", {})
    offset = data.get("search_offset", 0)
    search_type = data.get("search_type", "daughter")
    user_id = callback.from_user.id

    profiles, user_req = await _build_search_query(session, user_id, search_type, filters)

    total = len(profiles)

    if total == 0:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔧 " + ("Filtrlarni o'zgartirish" if lang == "uz" else "Изменить фильтры"),
                callback_data="search:manual",
            )],
            [InlineKeyboardButton(
                text="👀 " + ("Barchasini ko'rish" if lang == "uz" else "Показать все"),
                callback_data="search:all",
            )],
            *nav_kb(lang, "back:menu"),
        ])
        await callback.message.edit_text(t("search_empty", lang), reply_markup=kb)
        await callback.answer()
        return

    # Вычисляем score и сортируем: VIP → score → дата
    scored = []
    for p in profiles:
        score = compute_match_score(p, user_req)
        scored.append((p, score))

    scored.sort(key=lambda x: (
        0 if x[0].vip_status == VipStatus.ACTIVE else 1,
        -x[1],
    ))

    # Пагинация
    page_profiles = scored[offset:offset + PROFILES_PER_PAGE]

    if not page_profiles and offset > 0:
        # Вернулись назад но анкеты кончились — сбрасываем
        await state.update_data(search_offset=0)
        page_profiles = scored[0:PROFILES_PER_PAGE]
        offset = 0

    # Заголовок
    from_ = offset + 1
    to = min(offset + PROFILES_PER_PAGE, total)
    header = t("search_found", lang, total=total, from_=from_, to=to)

    # Иллюзия загрузки
    loading = "🔍 Siz uchun eng yaxshilarini tanlamoqdamiz..." if lang == "uz" else "🔍 Подбираем лучшие варианты для вас..."
    try:
        await callback.message.edit_text(loading)
        await asyncio.sleep(0.8)
    except Exception:
        pass

    # Заголовок с результатами
    try:
        await callback.message.edit_text(header, parse_mode="HTML")
    except Exception:
        try:
            await callback.message.answer(header, parse_mode="HTML")
        except Exception:
            await callback.message.answer(header)

    # Навигационные кнопки (собираем заранее — будут прикреплены к последней карточке)
    nav_buttons = []
    if offset + PROFILES_PER_PAGE < total:
        remaining = total - offset - PROFILES_PER_PAGE
        nav_buttons.append([InlineKeyboardButton(
            text=f"➡️ {'Keyingi 3' if lang == 'uz' else 'Следующие 3'} "
                 f"({'qoldi' if lang == 'uz' else 'осталось'}: {remaining})",
            callback_data="search:next",
        )])
    if offset > 0:
        nav_buttons.append([InlineKeyboardButton(
            text=f"⬅️ {'Oldingi' if lang == 'uz' else 'Предыдущие'}",
            callback_data="search:prev",
        )])
    nav_buttons.append([InlineKeyboardButton(
        text="🔧 " + ("Filtrlarni o'zgartirish" if lang == "uz" else "Изменить фильтры"),
        callback_data="search:manual",
    )])
    nav_buttons.extend(nav_kb(lang, "back:menu"))

    # Показываем карточки + уведомляем владельцев
    bot = callback.bot
    last_idx = len(page_profiles) - 1
    for i, (p, score) in enumerate(page_profiles):
        p.views_count = (p.views_count or 0) + 1
        card_text = format_anketa_public(p, score, lang)

        # На последней карточке — прикрепляем навигацию сразу под кнопками карточки
        if i == last_idx:
            card_kb = profile_card_kb(p.id, lang, p.display_id or "")
            combined_rows = list(card_kb.inline_keyboard) + nav_buttons
            kb = InlineKeyboardMarkup(inline_keyboard=combined_rows)
        else:
            kb = profile_card_kb(p.id, lang, p.display_id or "")

        try:
            await callback.message.answer(card_text, reply_markup=kb)
        except Exception as e:
            logger.error(f"Ошибка отправки карточки {p.id}: {e}")
        # Уведомление владельца о просмотре
        try:
            await _notify_owner_view(bot, session, p, callback.from_user.id)
        except Exception:
            pass

    await session.commit()
    await callback.answer()


# ── Пагинация ──

@router.callback_query(F.data == "search:next")
async def search_next(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    offset = data.get("search_offset", 0) + PROFILES_PER_PAGE
    await state.update_data(search_offset=offset)
    await _show_search_results(callback, session, state, lang)


@router.callback_query(F.data == "search:prev")
async def search_prev(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    offset = max(0, data.get("search_offset", 0) - PROFILES_PER_PAGE)
    await state.update_data(search_offset=offset)
    await _show_search_results(callback, session, state, lang)


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
async def add_favorite(callback: CallbackQuery, session: AsyncSession):
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

    if existing:
        await callback.answer("❤️ " + ("Allaqachon sevimlilarda" if lang == "uz" else "Уже в избранном"))
        return

    fav = Favorite(user_id=user_id, profile_id=profile_id)
    session.add(fav)
    await session.commit()

    # Микро-реакция — случайная фраза
    import random
    if lang == "uz":
        phrases = [
            "❤️ Saqlandi! Yaxshi tanlov 😊",
            "❤️ Ajoyib! Saqlandi 👌",
            "❤️ Zo'r tanlov!",
        ]
    else:
        phrases = [
            "❤️ Сохранено! Хороший выбор 😊",
            "❤️ Отлично! Сохранено 👌",
            "❤️ Хороший выбор!",
        ]
    await callback.answer(random.choice(phrases))

    # Уведомление владельцу
    profile = await session.get(Profile, profile_id)
    if profile:
        try:
            await _notify_owner_favorite(callback.bot, session, profile, user_id)
        except Exception:
            pass


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
        await callback.answer("💔 " + ("Tanlanganlardan o'chirildi" if lang == "uz" else "Удалено из избранного"))
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
    except Exception:
        pass

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
            occ_str = requester_profile.occupation or "—"
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
        except Exception:
            pass

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


@router.callback_query(F.data.startswith("skip_profile:"))
async def skip_profile(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    if lang == "uz":
        phrases = ["Keyingisi! 👉", "Davom etamiz 🔍", "Izlashda davom etamiz..."]
    else:
        phrases = ["Идём дальше! 👉", "Продолжаем поиск 🔍", "Ищем дальше..."]
    await callback.answer(random.choice(phrases))


# ══════════════════════════════════════════════════════════
#  Узнать контакт — выбор между модератором или оплатой картой
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("get_contact:"))
async def get_contact(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Пользователь хочет получить контакт — показать выбор способа."""
    profile_id = int(callback.data.split(":")[1])
    lang = await get_lang(session, callback.from_user.id)

    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена" if lang == "ru" else "Anketa topilmadi")
        return

    display_id = profile.display_id or "—"
    await state.update_data(contact_profile_id=profile_id, contact_display_id=display_id)

    # Регистрируем запрос и уведомляем владельца (как в interest: handler)
    try:
        cr = ContactRequest(
            requester_user_id=callback.from_user.id,
            target_profile_id=profile_id,
            status=RequestStatus.PENDING,
        )
        session.add(cr)
        profile.requests_count = (profile.requests_count or 0) + 1
        await session.commit()
    except Exception:
        pass

    if lang == "uz":
        text = (
            f"📋 Anketa: <b>{display_id}</b>\n\n"
            f"Kontaktni qanday olmoqchisiz?"
        )
        buttons = [
            [InlineKeyboardButton(text="💬 Moderator orqali", callback_data=f"contact_via:mod:{profile_id}")],
            [InlineKeyboardButton(text="💳 Karta orqali to'lov (30 000 so'm)", callback_data=f"contact_via:pay:{profile_id}")],
            [InlineKeyboardButton(text="← Orqaga", callback_data=f"skip_profile:{profile_id}")],
        ]
    else:
        text = (
            f"📋 Анкета: <b>{display_id}</b>\n\n"
            f"Как хотите получить контакт?"
        )
        buttons = [
            [InlineKeyboardButton(text="💬 Связаться с модератором", callback_data=f"contact_via:mod:{profile_id}")],
            [InlineKeyboardButton(text="💳 Оплатить картой (30 000 сум)", callback_data=f"contact_via:pay:{profile_id}")],
            [InlineKeyboardButton(text="← Назад", callback_data=f"skip_profile:{profile_id}")],
        ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("contact_via:mod:"))
async def contact_via_mod(callback: CallbackQuery, session: AsyncSession):
    """Связаться с модератором — показать deep-ссылки двух модераторов."""
    profile_id = int(callback.data.split(":")[2])
    lang = await get_lang(session, callback.from_user.id)

    profile = await session.get(Profile, profile_id)
    display_id = (profile.display_id if profile else "—") or "—"

    from bot.config import MODERATOR_USERNAMES
    mod_tashkent = MODERATOR_USERNAMES.get("tashkent") or "rishta_manager_tashkent"
    mod_samarkand = MODERATOR_USERNAMES.get("samarkand") or "rishta_manager_samarkand"

    if lang == "uz":
        text = (
            f"📋 Anketa: <b>{display_id}</b>\n\n"
            f"💁‍♀️ Moderatorni tanlang:"
        )
        start_text = f"Anketa {display_id} bo'yicha bog'lanmoqchiman"
    else:
        text = (
            f"📋 Анкета: <b>{display_id}</b>\n\n"
            f"💁‍♀️ Выберите модератора:"
        )
        start_text = f"Хочу узнать контакт анкеты {display_id}"

    from urllib.parse import quote
    url_text = quote(start_text)

    buttons = [
        [InlineKeyboardButton(
            text=f"💬 @{mod_tashkent}",
            url=f"https://t.me/{mod_tashkent}?text={url_text}",
        )],
        [InlineKeyboardButton(
            text=f"💬 @{mod_samarkand}",
            url=f"https://t.me/{mod_samarkand}?text={url_text}",
        )],
        [InlineKeyboardButton(
            text="← Orqaga" if lang == "uz" else "← Назад",
            callback_data=f"get_contact:{profile_id}",
        )],
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("contact_via:pay:"))
async def contact_via_pay(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Оплата картой — показать реквизиты и ждать скриншот."""
    from bot.states import PaymentStates
    profile_id = int(callback.data.split(":")[2])
    lang = await get_lang(session, callback.from_user.id)

    profile = await session.get(Profile, profile_id)
    display_id = (profile.display_id if profile else "—") or "—"

    if lang == "uz":
        text = (
            f"💳 <b>Ma'lumotlar uchun to'lov</b>\n\n"
            f"🔖 {display_id}\n"
            f"💰 Summa: <b>30 000 so'm</b>\n\n"
            f"Rekvizitlar:\n"
            f"💳 <code>5614 6887 0899 8959</code>\n"
            f"👤 SHODIYEVA NASIBA\n\n"
            f"📸 To'lovdan so'ng skrinshot yuboring"
        )
    else:
        text = (
            f"💳 <b>Оплата контакта</b>\n\n"
            f"🔖 {display_id}\n"
            f"💰 Сумма: <b>30 000 сум</b>\n\n"
            f"Реквизиты для перевода:\n"
            f"💳 <code>5614 6887 0899 8959</code>\n"
            f"👤 SHODIYEVA NASIBA\n\n"
            f"📸 Отправьте скриншот после оплаты"
        )

    buttons = [
        [InlineKeyboardButton(
            text="← Orqaga" if lang == "uz" else "← Назад",
            callback_data=f"get_contact:{profile_id}",
        )],
    ]

    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )

    await state.update_data(
        contact_profile_id=profile_id,
        contact_display_id=display_id,
    )
    await state.set_state(PaymentStates.awaiting_contact_screenshot)
    await callback.answer()


from bot.states import PaymentStates as _PaymentStates


@router.message(F.photo, _PaymentStates.awaiting_contact_screenshot)
async def contact_payment_screenshot(message, state: FSMContext, session: AsyncSession, bot: Bot):
    """Скриншот оплаты за контакт → модераторам."""
    data = await state.get_data()
    profile_id = data.get("contact_profile_id")
    display_id = data.get("contact_display_id", "—")
    user_id = message.from_user.id
    lang = await get_lang(session, user_id)
    photo_id = message.photo[-1].file_id

    # Уведомляем модераторов
    from bot.config import get_all_moderator_ids
    mod_text = (
        f"💳 <b>НОВАЯ ОПЛАТА ЗА КОНТАКТ</b>\n\n"
        f"Анкета: <b>{display_id}</b>\n"
        f"От: @{message.from_user.username or '—'} "
        f"(ID: <code>{user_id}</code>)\n\n"
        f"Проверьте скриншот и подтвердите:"
    )
    mod_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Подтвердить — передать контакт",
            callback_data=f"pay_confirm:{user_id}:{profile_id}",
        )],
        [InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"pay_reject:{user_id}:{profile_id}",
        )],
    ])

    for mod_id in get_all_moderator_ids():
        try:
            await bot.send_photo(
                mod_id, photo_id,
                caption=mod_text,
                reply_markup=mod_kb,
                parse_mode="HTML",
            )
        except Exception:
            pass

    if lang == "uz":
        reply = (
            "✅ Skrinshot qabul qilindi!\n\n"
            "Moderator to'lovni tekshirib,\n"
            "ma'lumotlarni yaqin orada yuboradi. 🤝\n\n"
            "Odatda 1-2 soat ichida."
        )
    else:
        reply = (
            "✅ Скриншот получен!\n\n"
            "Модератор проверит оплату\n"
            "и передаст контакт в\n"
            "ближайшее время. 🤝\n\n"
            "Обычно в течение 1-2 часов."
        )

    await message.answer(reply)
    await state.set_state(None)


@router.callback_query(F.data.startswith("pay_confirm:"))
async def pay_confirm(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор подтверждает оплату → передаём контакт покупателю."""
    parts = callback.data.split(":")
    buyer_id = int(parts[1])
    profile_id = int(parts[2])

    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("❌ Анкета не найдена")
        return

    display_id = profile.display_id or "—"

    contacts = []
    if getattr(profile, "parent_phone", None):
        contacts.append(f"📞 {profile.parent_phone}")
    if getattr(profile, "parent_telegram", None):
        contacts.append(f"📱 {profile.parent_telegram}")
    if getattr(profile, "candidate_telegram", None):
        contacts.append(f"💬 {profile.candidate_telegram}")
    if getattr(profile, "address", None):
        contacts.append(f"🏠 {profile.address}")
    contact_text = "\n".join(contacts) if contacts else "Контакты не указаны"

    try:
        await bot.send_message(
            buyer_id,
            f"✅ <b>Оплата подтверждена!</b>\n\n"
            f"🔖 {display_id}\n\n"
            f"<b>Контакты семьи:</b>\n"
            f"{contact_text}\n\n"
            f"Пусть эта встреча станет\n"
            f"началом счастья! 🤲",
            parse_mode="HTML",
        )
    except Exception:
        pass

    # Уведомляем владельца анкеты
    if profile.user_id:
        try:
            await bot.send_message(
                profile.user_id,
                f"🔥 Вашей анкетой <b>{display_id}</b>\n"
                f"заинтересовалась семья.\n\n"
                f"Модератор свяжется с вами\n"
                f"для организации знакомства. 🤝",
                parse_mode="HTML",
            )
        except Exception:
            pass

    # Обновляем подпись у модератора
    try:
        old_caption = callback.message.caption or ""
        await callback.message.edit_caption(
            caption=old_caption + "\n\n✅ <b>Подтверждено — контакт передан</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await callback.answer("✅ Контакт передан!")


@router.callback_query(F.data.startswith("pay_reject:"))
async def pay_reject(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор отклоняет оплату."""
    parts = callback.data.split(":")
    buyer_id = int(parts[1])
    profile_id = int(parts[2])

    profile = await session.get(Profile, profile_id)
    display_id = (profile.display_id if profile else "—") or "—"

    from bot.config import MODERATOR_USERNAMES
    mod_username = MODERATOR_USERNAMES.get("tashkent") or "rishta_manager_tashkent"

    try:
        await bot.send_message(
            buyer_id,
            f"❌ Оплата по анкете <b>{display_id}</b> не подтверждена.\n\n"
            f"Обратитесь к модератору:\n"
            f"@{mod_username}",
            parse_mode="HTML",
        )
    except Exception:
        pass

    try:
        old_caption = callback.message.caption or ""
        await callback.message.edit_caption(
            caption=old_caption + "\n\n❌ <b>Отклонено</b>",
            parse_mode="HTML",
        )
    except Exception:
        pass

    await callback.answer("❌ Отклонено")
