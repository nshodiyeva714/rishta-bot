"""Шаг 6 — Тариф, Шаг 7 — Требования, Шаг 8 — Подтверждение анкеты."""

from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    Profile, ProfileType, ProfileStatus, VipStatus,
    Education, Housing, ParentHousing, CarStatus, ResidenceStatus,
    SearchScope, Religiosity, MaritalStatus, ChildrenStatus,
    PhotoType, FamilyPosition, Requirement,
)
from bot.states import TariffStates, RequirementStates
from bot.texts import t
from bot.keyboards.inline import (
    req_age_kb, req_education_kb, req_residence_kb,
    req_residence_simple_kb, req_residence_regions_kb,
    req_nationality_kb, req_nationality_more_kb,
    req_religiosity_kb, req_marital_kb, req_children_kb,
    req_car_kb, req_housing_kb, req_job_kb,
    skip_kb, confirm_profile_kb, main_menu_kb,
    mod_review_kb,
    anketa_finish_kb, enhance_or_publish_kb, after_publish_kb,
    housing_kb, add_nav, nav_kb, back_kb,
)
from bot.utils.helpers import generate_display_id, age_text, calculate_age, format_full_anketa, occupation_label
from bot.config import config

router = Router()


async def _lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "ru")


# ── Шаг 6: Тариф ──
@router.callback_query(F.data == "tariff:free", TariffStates.choose)
async def choose_tariff_free(callback: CallbackQuery, state: FSMContext):
    await state.update_data(is_vip=False, vip_days=0)
    await _show_summary(callback, state, is_callback=True)


@router.callback_query(F.data == "tariff:vip")
async def choose_tariff_vip(callback: CallbackQuery, state: FSMContext):
    """Показываем выбор срока VIP."""
    lang = await _lang(state)
    data = await state.get_data()

    # Определяем регион по residence_status из анкеты (если уже заполнен)
    region = "uzb"
    res = data.get("residence_status")
    if res in ("usa", "europe", "citizenship_other", "other_country"):
        region = "usa"
    elif res == "cis":
        region = "sng"

    from bot.keyboards.inline import vip_duration_kb
    text = (
        "⭐ <b>VIP анкета</b>\n\n"
        "• Показывается первой в поиске\n"
        "• Выделена значком ⭐\n\n"
        "Выберите срок:"
    ) if lang == "ru" else (
        "⭐ <b>VIP anketa</b>\n\n"
        "• Qidirishda birinchi ko'rinadi\n"
        "• ⭐ belgisi bilan ajratiladi\n\n"
        "Muddatni tanlang:"
    )
    await callback.message.edit_text(text, reply_markup=vip_duration_kb(lang, region))
    # Остаёмся в TariffStates.choose — ждём vip_dur:N
    await callback.answer()


@router.callback_query(F.data.startswith("vip_dur:"), TariffStates.choose)
async def choose_vip_duration(callback: CallbackQuery, state: FSMContext):
    """Пользователь выбрал срок VIP — переходим к требованиям."""
    days = int(callback.data.split(":")[1])
    await state.update_data(is_vip=True, vip_days=days)
    lang = await _lang(state)
    await _show_summary(callback, state, is_callback=True)


# ── Шаг 7: Требования (отключено, хендлеры оставлены для совместимости) ──
_AGE_MAP = {
    "age_18_23": (18, 23),
    "age_24_27": (24, 27),
    "age_28_35": (28, 35),
    "age_36_45": (36, 45),
    "age_45_plus": (45, 99),
    "age_any": (0, 0),
}


@router.callback_query(F.data.startswith("age_"), RequirementStates.age)
async def req_age(callback: CallbackQuery, state: FSMContext):
    age_from, age_to = _AGE_MAP.get(callback.data, (0, 0))
    await state.update_data(req_age_from=age_from, req_age_to=age_to)
    lang = await _lang(state)
    await callback.message.edit_text(
        t("req_education", lang),
        reply_markup=add_nav(req_education_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(RequirementStates.education)
    await callback.answer()


@router.callback_query(F.data.startswith("reqedu:"), RequirementStates.education)
async def req_education(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_education=value)
    lang = await _lang(state)
    await callback.message.edit_text(
        t("req_residence", lang),
        reply_markup=add_nav(req_residence_simple_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(RequirementStates.residence)
    await callback.answer()


@router.callback_query(F.data.startswith("rres_"), RequirementStates.residence)
async def req_residence(callback: CallbackQuery, state: FSMContext):
    value = callback.data
    lang = await _lang(state)

    if value == "rres_uzb":
        # Show regions keyboard
        await callback.message.edit_text(
            t("req_residence_region", lang),
            reply_markup=add_nav(req_residence_regions_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
        )
        await state.set_state(RequirementStates.residence_city)
        await callback.answer()
        return
    elif value == "rres_other":
        await state.update_data(req_residence="other")
    else:  # rres_skip
        await state.update_data(req_residence="")

    await callback.message.edit_text(
        t("req_children", lang),
        reply_markup=add_nav(req_children_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(RequirementStates.children)
    await callback.answer()


@router.callback_query(F.data.startswith("rregion_"), RequirementStates.residence_city)
async def req_residence_region(callback: CallbackQuery, state: FSMContext):
    region = callback.data.replace("rregion_", "")
    if region == "any":
        await state.update_data(req_residence="uzbekistan")
    else:
        await state.update_data(req_residence=region)
    lang = await _lang(state)
    await callback.message.edit_text(
        t("req_children", lang),
        reply_markup=add_nav(req_children_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(RequirementStates.children)
    await callback.answer()


async def _advance_after_req_nationality(callback_or_message, state: FSMContext, lang: str) -> None:
    """После выбора/ввода национальности-требования — переход к религиозности."""
    kb = add_nav(req_religiosity_kb(lang).inline_keyboard, lang, "back:menu", show_main=False)
    if hasattr(callback_or_message, "message"):
        await callback_or_message.message.edit_text(t("req_religiosity", lang), reply_markup=kb)
    else:
        await callback_or_message.answer(t("req_religiosity", lang), reply_markup=kb)
    await state.set_state(RequirementStates.religiosity)


@router.callback_query(F.data.startswith("reqnat:"), RequirementStates.nationality)
async def req_nationality(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    lang = await _lang(state)

    if value == "more":
        await callback.message.edit_reply_markup(reply_markup=req_nationality_more_kb(lang))
        await callback.answer()
        return
    if value == "back":
        await callback.message.edit_reply_markup(reply_markup=req_nationality_kb(lang))
        await callback.answer()
        return
    if value == "custom":
        prompt = "✍️ Введите национальность:" if lang != "uz" else "✍️ Millatingizni kiriting:"
        await callback.message.edit_text(prompt)
        await state.set_state(RequirementStates.nationality_custom)
        await callback.answer()
        return

    await state.update_data(req_nationality=value)
    await _advance_after_req_nationality(callback, state, lang)
    await callback.answer()


@router.message(RequirementStates.nationality_custom)
async def req_nationality_custom(message: Message, state: FSMContext):
    nat = (message.text or "").strip()[:50]
    lang = await _lang(state)
    if not nat:
        await message.answer("✍️ Введите национальность:" if lang != "uz" else "✍️ Millatingizni kiriting:")
        return
    await state.update_data(req_nationality=nat)
    await _advance_after_req_nationality(message, state, lang)


@router.callback_query(F.data.startswith("reqrel:"), RequirementStates.religiosity)
async def req_religiosity(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_religiosity=value)
    lang = await _lang(state)
    await callback.message.edit_text(
        t("req_marital", lang),
        reply_markup=add_nav(req_marital_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(RequirementStates.marital_status)
    await callback.answer()


@router.callback_query(F.data.startswith("reqmar:"), RequirementStates.marital_status)
async def req_marital(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_marital_status=value)
    lang = await _lang(state)

    if value == "never_married":
        # Не замужем/не женат → детей нет автоматически → пропускаем вопрос
        await state.update_data(req_children="no_children")
        await _after_req_children(callback, state)
    else:
        # Разведена/вдова/любое → спросить про детей
        await callback.message.edit_text(
            t("req_children", lang),
            reply_markup=add_nav(req_children_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
        )
        await state.set_state(RequirementStates.children)
    await callback.answer()


@router.callback_query(F.data.startswith("reqchild:"), RequirementStates.children)
async def req_children(callback: CallbackQuery, state: FSMContext):
    value = callback.data.replace("reqchild:", "")
    children_map = {
        "no": "no_children",
        "yes": "has_children",
        "any": "any",
    }
    value = children_map.get(value, value)
    await state.update_data(req_children=value)
    await _after_req_children(callback, state)
    await callback.answer()


async def _after_req_children(callback: CallbackQuery, state: FSMContext):
    """Общий переход после вопроса о детях в требованиях."""
    lang = await _lang(state)
    data = await state.get_data()

    # Для анкеты дочери — дополнительные вопросы (машина, жильё, работа)
    if data.get("profile_type") == "daughter":
        await callback.message.edit_text(
            t("req_car", lang),
            reply_markup=add_nav(req_car_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
        )
        await state.set_state(RequirementStates.car_required)
    else:
        # Сын → сразу к резюме (пропускаем «другие пожелания»)
        await _show_summary(callback, state, is_callback=True)


# Дополнительные требования для дочери
@router.callback_query(F.data.startswith("reqcar:"), RequirementStates.car_required)
async def req_car(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_car=value)
    lang = await _lang(state)
    await callback.message.edit_text(
        t("req_housing", lang),
        reply_markup=add_nav(req_housing_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(RequirementStates.housing_required)
    await callback.answer()


@router.callback_query(F.data.startswith("reqhouse:"), RequirementStates.housing_required)
async def req_housing(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_housing=value)
    lang = await _lang(state)
    await callback.message.edit_text(
        t("req_job", lang),
        reply_markup=add_nav(req_job_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(RequirementStates.job_required)
    await callback.answer()


@router.callback_query(F.data.startswith("reqjob:"), RequirementStates.job_required)
async def req_job(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_job=value)
    # Дочь → сразу к резюме (пропускаем «другие пожелания»)
    await _show_summary(callback, state, is_callback=True)
    await callback.answer()


@router.message(RequirementStates.other_wishes)
async def req_other_wishes(message: Message, state: FSMContext):
    await state.update_data(req_other=message.text.strip())
    await _show_summary(message, state)


@router.callback_query(F.data == "skip", RequirementStates.other_wishes)
async def req_other_skip(callback: CallbackQuery, state: FSMContext):
    await _show_summary(callback, state, is_callback=True)


# ══════════════════════════════════════
# Экран резюме анкеты
# ══════════════════════════════════════

_EDU_LABELS = {
    "ru": {"secondary": "Среднее", "vocational": "Среднее спец.", "higher": "Высшее", "studying": "Студент/ка"},
    "uz": {"secondary": "O'rta", "vocational": "O'rta maxsus", "higher": "Oliy", "studying": "Talaba"},
}
_REL_LABELS = {
    "ru": {"practicing": "🕌 Практикующий/ая", "moderate": "☪️ Умеренный/ая", "secular": "🌐 Светский/ая"},
    "uz": {"practicing": "🕌 Amaliyotchi", "moderate": "☪️ Mo'tadil", "secular": "🌐 Dunyoviy"},
}
_MAR_LABELS = {
    "ru": {"never_married": "💍 Не был(а) в браке", "divorced": "💔 Разведён/а", "widowed": "🖤 Вдовец/Вдова"},
    "uz": {"never_married": "💍 Turmush qurmagan", "divorced": "💔 Ajrashgan", "widowed": "🖤 Beva"},
}


async def _show_summary(msg_or_cb, state: FSMContext, is_callback: bool = False):
    """Показать резюме анкеты с кнопками «Опубликовать» / «Сделать ярче»."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    L = lang if lang in ("ru", "uz") else "ru"
    ptype = data.get("profile_type", "son")

    name = data.get("name", "—")
    birth_year = data.get("birth_year")
    age = (datetime.now().year - birth_year) if birth_year else "?"
    city = data.get("city", "—")

    edu_raw = data.get("education", "")
    edu = _EDU_LABELS.get(L, _EDU_LABELS["ru"]).get(edu_raw, "—")
    uni = data.get("university_info")
    if edu_raw == "studying" and uni:
        # Студент + детали → показываем только детали
        edu = uni
    elif uni:
        edu += f", {uni}"

    work = occupation_label(data.get("occupation"), L)
    rel = _REL_LABELS.get(L, _REL_LABELS["ru"]).get(data.get("religiosity", ""), "—")
    mar = _MAR_LABELS.get(L, _MAR_LABELS["ru"]).get(data.get("marital_status", ""), "—")

    emoji = "👦" if ptype == "son" else "👧"

    if L == "uz":
        summary = (
            f"━━━━━━━━━━━━━━━\n"
            f"✅ <b>Anketa to'ldirildi!</b>\n\n"
            f"{emoji} {name} · {age} yosh\n"
            f"🏙 {city}\n"
            f"🎓 {edu}\n"
            f"💼 {work}\n"
            f"{rel}\n"
            f"{mar}\n\n"
            f"Keyingi qadam:"
        )
    else:
        summary = (
            f"━━━━━━━━━━━━━━━\n"
            f"✅ <b>Анкета заполнена!</b>\n\n"
            f"{emoji} {name} · {age} лет\n"
            f"🏙 {city}\n"
            f"🎓 {edu}\n"
            f"💼 {work}\n"
            f"{rel}\n"
            f"{mar}\n\n"
            f"Что делаем дальше?"
        )

    kb = anketa_finish_kb(lang)

    if is_callback:
        await msg_or_cb.message.edit_text(summary, reply_markup=kb)
        await msg_or_cb.answer()
    else:
        await msg_or_cb.answer(summary, reply_markup=kb)

    await state.set_state(RequirementStates.summary)


# ── «✨ Сделать анкету ярче» ──
@router.callback_query(F.data == "profile:enhance", RequirementStates.summary)
async def profile_enhance(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")

    if lang == "uz":
        text = (
            "✨ <b>Anketani boyiting</b>\n\n"
            "Qo'shimcha ma'lumotlar qo'shing —\n"
            "va anketangiz boshqalardan ajralib turadi:\n\n"
            "👨‍👩‍👧 Oila haqida\n"
            "🌸 Xarakter va qiziqishlar\n"
            "🏡 Turar joy va avtomobil\n"
            "📞 Kontaktlar\n\n"
            "Taxminan 2 daqiqa vaqt oladi 🕐"
        )
    else:
        text = (
            "✨ <b>Сделайте анкету ярче</b>\n\n"
            "Добавьте детали — и ваша анкета\n"
            "будет выделяться среди остальных:\n\n"
            "👨‍👩‍👧 О семье\n"
            "🌸 Характер и увлечения\n"
            "🏡 Жильё и автомобиль\n"
            "📞 Контакты\n\n"
            "Займёт около 2 минут 🕐"
        )

    await callback.message.edit_text(text, reply_markup=enhance_or_publish_kb(lang))
    await callback.answer()


# ── «🔙 Назад» с экрана срока VIP → вернуть на экран выбора тарифа ──
@router.callback_query(F.data == "profile:back_to_tariff")
async def back_to_tariff(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()

    from bot.handlers.questionnaire import build_card
    from bot.keyboards.inline import tariff_kb
    card = build_card(data, lang)

    if lang == "uz":
        tariff_text = (
            "📋 Joylash turi:\n\n"
            "⭐ VIP anketa — ko'proq ko'rishlar,\n"
            "qidirishda birinchi ko'rinadi.\n\n"
            "📋 Oddiy anketa — bepul."
        )
    else:
        tariff_text = (
            "📋 Тип размещения:\n\n"
            "⭐ VIP анкета — больше просмотров,\n"
            "показывается первой в поиске.\n\n"
            "📋 Обычная анкета — бесплатно."
        )

    SEP = "\n\n━━━━━━━━━━━━\n\n"
    full = (card + SEP + tariff_text) if card else tariff_text

    try:
        await callback.message.edit_text(full, reply_markup=tariff_kb(lang))
    except Exception:
        await callback.message.answer(full, reply_markup=tariff_kb(lang))
    await state.set_state(TariffStates.choose)
    await callback.answer()


# ── «← Назад» из экрана summary → вернуть на тариф ──
@router.callback_query(F.data == "profile:back", RequirementStates.summary)
async def profile_back(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()

    from bot.handlers.questionnaire import build_card, SEP
    card = build_card(data, lang)

    if lang == "uz":
        tariff_text = (
            "📋 Joylashtirish turi:\n\n"
            "⭐ VIP anketa — ko'proq e'tibor,\n"
            "qidirishda birinchi ko'rinadi.\n\n"
            "📋 Oddiy anketa — bepul."
        )
    else:
        tariff_text = (
            "📋 Тип размещения:\n\n"
            "⭐ VIP анкета — больше просмотров,\n"
            "показывается первой в поиске.\n\n"
            "📋 Обычная анкета — бесплатно."
        )

    full_text = (card + SEP + tariff_text) if card else tariff_text
    from bot.keyboards.inline import tariff_kb
    await callback.message.edit_text(full_text, reply_markup=tariff_kb(lang))
    await state.set_state(TariffStates.choose)
    await callback.answer()


# ── «← Назад» из экрана enhance → вернуть на summary ──
@router.callback_query(F.data == "profile:back_enhance", RequirementStates.summary)
async def profile_back_enhance(callback: CallbackQuery, state: FSMContext):
    await _show_summary(callback, state, is_callback=True)


# ── «👁 Посмотреть анкету» — предпросмотр карточки перед публикацией ──
@router.callback_query(F.data == "profile:preview", RequirementStates.summary)
async def profile_preview(callback: CallbackQuery, state: FSMContext):
    from bot.handlers.questionnaire import build_card
    data = await state.get_data()
    lang = data.get("lang", "ru")

    card = build_card(data, lang)

    if lang == "uz":
        header = "👁 <b>Anketangiz shunday ko'rinadi:</b>\n\n"
        footer = "\n\n🔒 Kontakt · manzil · foto — to'lovdan keyin"
        buttons = [
            [InlineKeyboardButton(text="🚀 Moderatorga yuborish", callback_data="profile:publish")],
            [InlineKeyboardButton(text="✨ Anketani boyitish", callback_data="profile:enhance")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="profile:back_enhance")],
        ]
    else:
        header = "👁 <b>Вот как выглядит ваша анкета:</b>\n\n"
        footer = "\n\n🔒 Контакты · адрес · фото — только после оплаты"
        buttons = [
            [InlineKeyboardButton(text="🚀 Отправить на публикацию", callback_data="profile:publish")],
            [InlineKeyboardButton(text="✨ Сделать анкету ярче", callback_data="profile:enhance")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="profile:back_enhance")],
        ]

    preview_text = header + (card or "—") + footer
    await callback.message.edit_text(
        preview_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML",
    )
    await callback.answer()


# ── «✏️ Дополнить сейчас» (legacy) — сначала публикуем, потом Этап 2 ──
@router.callback_query(F.data == "profile:extend_now", RequirementStates.summary)
async def profile_extend_now(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    """Legacy-хендлер (не используется после обновления, но оставлен для совместимости)."""
    profile, display_id = await _save_profile(callback, state, session, bot)
    if not profile:
        return

    data = await state.get_data()
    lang = data.get("lang", "ru")
    await state.update_data(ext_profile_id=profile.id)

    await callback.message.edit_text(
        t("ext_housing", lang),
        reply_markup=add_nav(housing_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    from bot.states import QuestionnaireStates
    await state.set_state(QuestionnaireStates.ext_housing)
    await callback.answer()


# ── «🚀 Опубликовать как есть» (profile:confirm с экрана enhance_intro) ──
@router.callback_query(F.data == "profile:confirm", RequirementStates.summary)
async def profile_confirm_summary(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    """Публикация без Этапа 2 — сохраняем профиль и показываем успех."""
    await publish_profile(callback, state, session, bot)


# ── «🚀 Опубликовать» с финального экрана Этапа 2 ──
@router.callback_query(F.data == "profile:confirm")
async def profile_confirm_after_ext(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    """Публикация после Этапа 2 — сохраняем профиль со всеми данными Этапа 2."""
    from bot.states import QuestionnaireStates
    current = await state.get_state()
    if current != QuestionnaireStates.ext_confirm.state:
        # Неожиданный стейт — просто публикуем
        await publish_profile(callback, state, session, bot)
        return

    # Сохраняем профиль с данными Этапа 1 + Этапа 2 (они все в FSM state)
    profile, display_id = await _save_profile(callback, state, session, bot)
    if not profile:
        return

    # Обновляем профиль доп. полями из Этапа 2, которых нет в _save_profile
    data = await state.get_data()
    lang = data.get("lang", "ru")

    def safe_enum(enum_cls, val):
        if val is None:
            return None
        try:
            return enum_cls(val)
        except (ValueError, KeyError):
            return None

    updated = False
    if data.get("housing") and not profile.housing:
        profile.housing = safe_enum(Housing, data["housing"])
        updated = True
    if data.get("parent_housing_type") and not profile.parent_housing_type:
        profile.parent_housing_type = safe_enum(ParentHousing, data["parent_housing_type"])
        updated = True
    if data.get("car") and not profile.car:
        profile.car = safe_enum(CarStatus, data["car"])
        updated = True
    if data.get("father_occupation") and not profile.father_occupation:
        profile.father_occupation = data["father_occupation"]
        updated = True
    if data.get("mother_occupation") and not profile.mother_occupation:
        profile.mother_occupation = data["mother_occupation"]
        updated = True
    if data.get("brothers_count") is not None and not profile.brothers_count:
        profile.brothers_count = data["brothers_count"]
        updated = True
    if data.get("sisters_count") is not None and not profile.sisters_count:
        profile.sisters_count = data["sisters_count"]
        updated = True
    if data.get("family_position") and not profile.family_position:
        profile.family_position = safe_enum(FamilyPosition, data["family_position"])
        updated = True
    if data.get("character_hobbies") and not getattr(profile, "character_hobbies", None):
        profile.character_hobbies = data["character_hobbies"]
        updated = True
    if data.get("health_notes") and not getattr(profile, "health_notes", None):
        profile.health_notes = data["health_notes"]
        updated = True
    if data.get("ideal_family_life") and not getattr(profile, "ideal_family_life", None):
        profile.ideal_family_life = data["ideal_family_life"]
        updated = True
    if data.get("parent_telegram") and not getattr(profile, "parent_telegram", None):
        profile.parent_telegram = data["parent_telegram"]
        updated = True
    if data.get("candidate_telegram") and not getattr(profile, "candidate_telegram", None):
        profile.candidate_telegram = data["candidate_telegram"]
        updated = True
    if data.get("parent_phone") and not getattr(profile, "parent_phone", None):
        try:
            profile.parent_phone = data["parent_phone"]
        except Exception:
            pass
        updated = True
    if data.get("address") and not profile.address:
        profile.address = data["address"]
        updated = True

    if updated:
        await session.commit()

    # Показываем финальный экран «опубликовано»
    if lang == "uz":
        submitted_text = (
            f"🎉 <b>Anketa yuborildi!</b>\n\n"
            f"🔖 #{display_id}\n\n"
            f"Moderator 24 soat ichida tekshiradi\n"
            f"va nashr etadi 🤝"
        )
    else:
        submitted_text = (
            f"🎉 <b>Анкета отправлена!</b>\n\n"
            f"🔖 #{display_id}\n\n"
            f"Модератор проверит в течение\n"
            f"24 часов и опубликует 🤝"
        )

    await callback.message.edit_text(submitted_text, reply_markup=main_menu_kb(lang, callback.from_user.id))
    await state.clear()
    await callback.answer()


# ── «🚀 Отправить на публикацию» ──
@router.callback_query(F.data == "profile:publish", RequirementStates.summary)
async def publish_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    """Сохраняем и публикуем анкету."""
    profile, display_id = await _save_profile(callback, state, session, bot)
    if not profile:
        return

    data = await state.get_data()
    lang = data.get("lang", "ru")

    # Сохраняем profile_id на случай «Дополнить позже»
    await state.update_data(ext_profile_id=profile.id)

    if lang == "uz":
        submitted_text = (
            f"🎉 <b>Anketa yuborildi!</b>\n\n"
            f"🔖 #{display_id}\n\n"
            f"Moderator 24 soat ichida tekshiradi\n"
            f"va nashr etadi 🤝\n\n"
            f"Kutayotganda — anketangizni\n"
            f"boyitishingiz mumkin 👇"
        )
    else:
        submitted_text = (
            f"🎉 <b>Анкета отправлена!</b>\n\n"
            f"🔖 #{display_id}\n\n"
            f"Модератор проверит в течение\n"
            f"24 часов и опубликует 🤝\n\n"
            f"Пока ждёте — можете\n"
            f"сделать анкету ярче 👇"
        )

    await callback.message.edit_text(submitted_text, reply_markup=after_publish_kb(lang))
    await state.set_state(RequirementStates.confirm)
    await callback.answer()


# ── «✨ Дополнить анкету» после публикации ──
@router.callback_query(F.data == "after:extend", RequirementStates.confirm)
async def after_extend(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile_id = data.get("ext_profile_id")

    if not profile_id:
        await callback.message.edit_text(
            t("main_menu", lang), reply_markup=main_menu_kb(lang, callback.from_user.id))
        await state.clear()
        await callback.answer()
        return

    await callback.message.edit_text(
        t("ext_housing", lang),
        reply_markup=add_nav(housing_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    from bot.states import QuestionnaireStates
    await state.set_state(QuestionnaireStates.ext_housing)
    await callback.answer()


# ══════════════════════════════════════
# Общая функция сохранения профиля
# ══════════════════════════════════════

async def _save_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    """Создать Profile + Requirement в БД, уведомить модераторов. Возвращает (profile, display_id)."""
    data = await state.get_data()

    # Если уже сохранён — не дублировать
    if data.get("ext_profile_id"):
        profile = await session.get(Profile, data["ext_profile_id"])
        if profile:
            return profile, profile.display_id

    lang = data.get("lang", "ru")
    ptype = ProfileType(data.get("profile_type", "son"))
    display_id = await generate_display_id(session, ptype)

    def safe_enum(enum_cls, val):
        if val is None:
            return None
        try:
            return enum_cls(val)
        except (ValueError, KeyError):
            return None

    profile = Profile(
        user_id=callback.from_user.id,
        profile_type=ptype,
        status=ProfileStatus.PENDING,
        display_id=display_id,
        anketa_lang=lang,
        name=data.get("name"),
        birth_year=data.get("birth_year"),
        height_cm=data.get("height_cm"),
        weight_kg=data.get("weight_kg"),
        body_type=data.get("body_type"),
        education=safe_enum(Education, data.get("education")),
        university_info=data.get("university_info"),
        occupation=data.get("occupation"),
        housing=safe_enum(Housing, data.get("housing")),
        parent_housing_type=safe_enum(ParentHousing, data.get("parent_housing_type")),
        car=safe_enum(CarStatus, data.get("car")),
        city=data.get("city"),
        city_code=data.get("city_code"),
        country=data.get("country"),
        district=data.get("district"),
        address=data.get("address"),
        residence_status=safe_enum(ResidenceStatus, data.get("residence_status")),
        search_scope=safe_enum(SearchScope, data.get("search_scope")),
        preferred_city=data.get("preferred_city"),
        preferred_district=data.get("preferred_district"),
        preferred_country=data.get("preferred_country"),
        family_region=data.get("family_region"),
        nationality=data.get("nationality"),
        father_occupation=data.get("father_occupation"),
        mother_occupation=data.get("mother_occupation"),
        brothers_count=data.get("brothers_count", 0),
        sisters_count=data.get("sisters_count", 0),
        family_position=safe_enum(FamilyPosition, data.get("family_position")),
        religiosity=safe_enum(Religiosity, data.get("religiosity")),
        marital_status=safe_enum(MaritalStatus, data.get("marital_status")),
        children_status=safe_enum(ChildrenStatus, data.get("children_status")),
        health_notes=data.get("health_notes"),
        character_hobbies=data.get("character_hobbies"),
        ideal_family_life=data.get("ideal_family_life"),
        important_qualities=data.get("important_qualities"),
        five_year_plans=data.get("five_year_plans"),
        photo_type=safe_enum(PhotoType, data.get("photo_type")) or PhotoType.NONE,
        photo_file_id=data.get("photo_file_id"),
        parent_phone=data.get("parent_phone"),
        parent_telegram=data.get("parent_telegram"),
        candidate_telegram=data.get("candidate_telegram"),
        location_lat=data.get("location_lat"),
        location_lon=data.get("location_lon"),
        location_link=data.get("location_link"),
        is_active=data.get("is_active", True),
    )

    if data.get("is_vip"):
        vip_days = data.get("vip_days", 30)
        profile.vip_status = VipStatus.ACTIVE
        profile.vip_expires_at = datetime.now() + timedelta(days=vip_days)

    session.add(profile)
    await session.flush()

    requirement = Requirement(
        profile_id=profile.id,
        age_from=data.get("req_age_from"),
        age_to=data.get("req_age_to"),
        education=data.get("req_education"),
        residence=data.get("req_residence"),
        nationality=data.get("req_nationality"),
        religiosity=data.get("req_religiosity"),
        marital_status=data.get("req_marital_status"),
        children=data.get("req_children"),
        car_required=data.get("req_car"),
        housing_required=data.get("req_housing"),
        job_required=data.get("req_job"),
        other_wishes=data.get("req_other"),
    )
    session.add(requirement)
    await session.commit()

    await state.update_data(ext_profile_id=profile.id)

    # Уведомляем модераторов
    from bot.config import get_all_moderator_ids
    mod_text = format_full_anketa(profile, lang="ru")
    for mod_id in get_all_moderator_ids():
        try:
            await bot.send_message(mod_id, mod_text, reply_markup=mod_review_kb(profile.id))
            if profile.photo_file_id:
                await bot.send_photo(mod_id, profile.photo_file_id)
        except Exception:
            pass

    return profile, display_id


@router.callback_query(F.data == "profile:cancel", RequirementStates.confirm)
async def cancel_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = (await state.get_data()).get("lang", "ru")
    await state.clear()
    await callback.message.edit_text(t("main_menu", lang), reply_markup=main_menu_kb(lang))
    await callback.answer()
