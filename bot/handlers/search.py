"""Поиск анкет — 3 режима: по требованиям, ручные фильтры, все."""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, desc, case, func as sa_func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    User, Profile, ProfileStatus, ProfileType, VipStatus,
    Requirement, Favorite, ContactRequest, RequestStatus,
)
from bot.texts import t
from bot.keyboards.inline import (
    profile_card_kb, search_nav_kb, back_kb, main_menu_kb,
    get_contact_kb, search_mode_kb, search_no_anketa_kb,
    search_filter_kb, filter_option_kb,
)
from bot.utils.helpers import age_text, calculate_age, format_anketa_public
from bot.config import config
from bot.states import SearchStates

router = Router()

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


def format_filters_summary(filters: dict, lang: str = "ru") -> str:
    """Текстовое описание текущих фильтров."""
    if not filters:
        return t("search_filters_empty", lang)

    _labels = {
        "age_from":  ("📅", {"ru": "Возраст", "uz": "Yosh"}),
        "religion":  ("🕌", {"ru": "Религиозность", "uz": "Dindorlik"}),
        "education": ("🎓", {"ru": "Образование", "uz": "Ma'lumoti"}),
        "marital":   ("💍", {"ru": "Сем. положение", "uz": "Oilaviy holat"}),
        "children":  ("👶", {"ru": "Дети", "uz": "Farzandlar"}),
        "residence": ("🌍", {"ru": "Проживание", "uz": "Yashash joyi"}),
    }

    lines = []
    if filters.get("age_from") and filters.get("age_to"):
        icon, label = _labels["age_from"]
        lines.append(f"{icon} {label[lang]}: {filters['age_from']}–{filters['age_to']}")
    for key in ("religion", "education", "marital", "children", "residence"):
        val = filters.get(key)
        if val and val != "any":
            icon, label = _labels[key]
            lines.append(f"{icon} {label[lang]}: {val}")

    return "\n".join(lines) if lines else t("search_filters_empty", lang)


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
        await callback.message.edit_text(
            t("search_no_anketa", lang),
            reply_markup=search_no_anketa_kb(lang),
        )
    await callback.answer()


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

@router.callback_query(F.data == "search:manual")
async def search_manual(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Показать меню ручных фильтров."""
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()

    filters = data.get("search_filters", {})

    # Если search_type ещё не установлен — определяем
    if "search_type" not in data:
        my_profile = await _get_user_profile(session, callback.from_user.id)
        search_type = "daughter" if my_profile and my_profile.profile_type == ProfileType.SON else "son"
        await state.update_data(search_type=search_type, search_filters=filters, search_offset=0)

    summary = format_filters_summary(filters, lang)
    await callback.message.edit_text(
        t("search_filters_title", lang, summary=summary),
        reply_markup=search_filter_kb(lang),
    )
    await callback.answer()


# ── Фильтр: возраст ──
@router.callback_query(F.data == "filter:age")
async def filter_age_start(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    lang = await get_lang(session, callback.from_user.id)
    await callback.message.edit_text(
        t("search_filter_age_prompt", lang),
        reply_markup=back_kb(lang),
    )
    await state.set_state(SearchStates.filter_age)
    await callback.answer()


@router.message(SearchStates.filter_age)
async def filter_age_input(message: Message, session: AsyncSession, state: FSMContext):
    """Принимаем ввод вида '20-30'."""
    lang = await get_lang(session, message.from_user.id)
    text = message.text.strip().replace(" ", "")

    # Парсим
    parts = text.split("-")
    if len(parts) != 2:
        await message.answer(t("search_filter_age_error", lang))
        return

    try:
        age_from = int(parts[0])
        age_to = int(parts[1])
    except ValueError:
        await message.answer(t("search_filter_age_error", lang))
        return

    if age_from < 16 or age_to > 80 or age_from > age_to:
        await message.answer(t("search_filter_age_error", lang))
        return

    data = await state.get_data()
    filters = data.get("search_filters", {})
    filters["age_from"] = age_from
    filters["age_to"] = age_to
    await state.update_data(search_filters=filters)
    await state.set_state(None)

    # Показываем меню фильтров
    summary = format_filters_summary(filters, lang)
    await message.answer(
        t("search_filters_title", lang, summary=summary),
        reply_markup=search_filter_kb(lang),
    )


# ── Фильтр: религиозность ──
@router.callback_query(F.data == "filter:religion")
async def filter_religion(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("🕌 " + ("Практикующий" if lang == "ru" else "Amaliyotchi"), "fval:religion:practicing"),
        ("☪️ " + ("Умеренный" if lang == "ru" else "Mo'tadil"), "fval:religion:moderate"),
        ("🌐 " + ("Светский" if lang == "ru" else "Dunyoviy"), "fval:religion:secular"),
        ("🔄 " + ("Любая" if lang == "ru" else "Har qanday"), "fval:religion:any"),
    ]
    await callback.message.edit_text(
        "🕌 " + ("Выберите религиозность:" if lang == "ru" else "Dindorlikni tanlang:"),
        reply_markup=filter_option_kb(options, lang),
    )
    await callback.answer()


# ── Фильтр: образование ──
@router.callback_query(F.data == "filter:education")
async def filter_education(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("📚 " + ("Среднее" if lang == "ru" else "O'rta"), "fval:education:secondary"),
        ("📖 " + ("Среднее спец." if lang == "ru" else "O'rta maxsus"), "fval:education:vocational"),
        ("🎓 " + ("Высшее" if lang == "ru" else "Oliy"), "fval:education:higher"),
        ("🏛 " + ("Учится" if lang == "ru" else "O'qiyapti"), "fval:education:studying"),
        ("🔄 " + ("Любое" if lang == "ru" else "Har qanday"), "fval:education:any"),
    ]
    await callback.message.edit_text(
        "🎓 " + ("Выберите образование:" if lang == "ru" else "Ma'lumotni tanlang:"),
        reply_markup=filter_option_kb(options, lang),
    )
    await callback.answer()


# ── Фильтр: семейное положение ──
@router.callback_query(F.data == "filter:marital")
async def filter_marital(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("💍 " + ("Не был(а) в браке" if lang == "ru" else "Turmush qurmagan"), "fval:marital:never_married"),
        ("📝 " + ("Разведён(а)" if lang == "ru" else "Ajrashgan"), "fval:marital:divorced"),
        ("🕊 " + ("Вдовец/Вдова" if lang == "ru" else "Beva"), "fval:marital:widowed"),
        ("🔄 " + ("Любое" if lang == "ru" else "Har qanday"), "fval:marital:any"),
    ]
    await callback.message.edit_text(
        "💍 " + ("Выберите сем. положение:" if lang == "ru" else "Oilaviy holatni tanlang:"),
        reply_markup=filter_option_kb(options, lang),
    )
    await callback.answer()


# ── Фильтр: дети ──
@router.callback_query(F.data == "filter:children")
async def filter_children(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("🚫 " + ("Без детей" if lang == "ru" else "Farzandsiz"), "fval:children:no"),
        ("👶 " + ("Есть, живут с ним/ней" if lang == "ru" else "Bor, u bilan yashaydi"), "fval:children:yes_with_me"),
        ("👶 " + ("Есть, живут с бывшим" if lang == "ru" else "Bor, sobiq bilan"), "fval:children:yes_with_ex"),
        ("🔄 " + ("Любое" if lang == "ru" else "Har qanday"), "fval:children:any"),
    ]
    await callback.message.edit_text(
        "👶 " + ("Выберите:" if lang == "ru" else "Tanlang:"),
        reply_markup=filter_option_kb(options, lang),
    )
    await callback.answer()


# ── Фильтр: проживание ──
@router.callback_query(F.data == "filter:residence")
async def filter_residence(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    options = [
        ("🇺🇿 " + ("Узбекистан" if lang == "ru" else "O'zbekiston"), "fval:residence:uzbekistan"),
        ("🇷🇺 " + ("СНГ" if lang == "ru" else "MDH"), "fval:residence:cis"),
        ("🇺🇸 " + ("США" if lang == "ru" else "AQSH"), "fval:residence:usa"),
        ("🌍 " + ("Европа" if lang == "ru" else "Yevropa"), "fval:residence:europe"),
        ("🔄 " + ("Любое" if lang == "ru" else "Har qanday"), "fval:residence:any"),
    ]
    await callback.message.edit_text(
        "🌍 " + ("Где проживает:" if lang == "ru" else "Yashash joyi:"),
        reply_markup=filter_option_kb(options, lang),
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

    await state.update_data(search_filters=filters)

    lang = await get_lang(session, callback.from_user.id)
    summary = format_filters_summary(filters, lang)
    await callback.message.edit_text(
        t("search_filters_title", lang, summary=summary),
        reply_markup=search_filter_kb(lang),
    )
    await callback.answer()


# ── Сбросить фильтры ──
@router.callback_query(F.data == "filter:clear")
async def filter_clear(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.update_data(search_filters={}, search_offset=0)
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer(t("search_filters_cleared", lang), show_alert=True)

    summary = format_filters_summary({}, lang)
    await callback.message.edit_text(
        t("search_filters_title", lang, summary=summary),
        reply_markup=search_filter_kb(lang),
    )


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
        Profile.status == ProfileStatus.PUBLISHED,
        Profile.is_active == True,
        Profile.profile_type == target_type,
        Profile.user_id != user_id,
    ]

    # Фильтр: возраст
    if filters.get("age_from") or filters.get("age_to"):
        import datetime
        current_year = datetime.datetime.now().year
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
        try:
            conditions.append(Profile.children_status == ChildrenStatus(filters["children"]))
        except ValueError:
            pass

    # Фильтр: проживание
    if filters.get("residence") and filters["residence"] != "any":
        from bot.db.models import ResidenceStatus
        try:
            conditions.append(Profile.residence_status == ResidenceStatus(filters["residence"]))
        except ValueError:
            pass

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
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔧 " + ("Filtrlarni o'zgartirish" if lang == "uz" else "Изменить фильтры"),
                callback_data="search:manual",
            )],
            [InlineKeyboardButton(
                text="👀 " + ("Barchasini ko'rish" if lang == "uz" else "Показать все"),
                callback_data="search:all",
            )],
            [InlineKeyboardButton(
                text="🔙 " + ("Orqaga" if lang == "uz" else "Назад"),
                callback_data="back:menu",
            )],
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

    try:
        await callback.message.edit_text(header)
    except Exception:
        await callback.message.answer(header)

    # Показываем карточки
    for p, score in page_profiles:
        p.views_count = (p.views_count or 0) + 1
        card_text = format_anketa_public(p, score, lang)
        await callback.message.answer(
            card_text,
            reply_markup=profile_card_kb(p.id, lang, p.display_id or ""),
        )

    await session.commit()

    # Навигация
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
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

    nav_buttons.extend([
        [InlineKeyboardButton(
            text="🔧 " + ("Filtrlarni o'zgartirish" if lang == "uz" else "Изменить фильтры"),
            callback_data="search:manual",
        )],
        [InlineKeyboardButton(
            text="🔙 " + ("Bosh menyu" if lang == "uz" else "Главное меню"),
            callback_data="back:menu",
        )],
    ])

    await callback.message.answer(
        "─────────────────",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_buttons),
    )
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
    await callback.answer("❤️ " + ("Sevimlilarga qo'shildi" if lang == "uz" else "Добавлено в избранное"))


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
async def skip_profile(callback: CallbackQuery):
    await callback.answer("❌ Пропущено")
