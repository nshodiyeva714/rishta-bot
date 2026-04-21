"""Анкета — ЭТАП 1: Быстрый старт (10 вопросов).

Порядок: Имя(1) → Год рождения+Рост(2) → Фото(3) → Телосложение(4) →
         Национальность(5) → Город(6) → Образование(7) → Занятость(8) →
         Религиозность(9) → Семейное положение+дети(10) → Завершение
"""

from datetime import datetime

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext

from bot.states import QuestionnaireStates, TariffStates
from bot.texts import t
from bot.utils.helpers import occupation_label, nationality_label
from bot.keyboards.inline import (
    education_kb, nationality_kb, nationality_more_kb, religiosity_kb,
    marital_kb, children_kb, photo_type_kb,
    confirm_age_kb, skip_kb,
    back_step_kb, skip_back_kb, add_nav, body_type_kb, occupation_kb,
    anketa_finish_kb, city_kb, city_more_kb, uz_regions_kb,
)

router = Router()

SEP = "\n\n━━━━━━━━━━━━━\n\n"


# ══════════════════════════════════════
# Утилиты
# ══════════════════════════════════════

def progress_bar(current: int, total: int) -> str:
    """Прогресс-бар для вопросов анкеты."""
    filled = current
    empty = total - filled
    bar = "▓" * filled + "░" * empty
    pct = round(current / total * 100)
    return f"{bar}  {pct}%"


def build_card(data: dict, lang: str = "ru") -> str:
    """Строит накопленную карточку из заполненных данных."""
    lines = []
    L = lang if lang in ("ru", "uz") else "ru"

    # Имя + возраст + рост
    name = data.get("name")
    age = data.get("age")
    height = data.get("height_cm")
    header = []
    if name:
        header.append(name)
    if age:
        header.append(f"{age} {'лет' if L == 'ru' else 'yosh'}")
    if height:
        header.append(f"{height} {'см' if L == 'ru' else 'sm'}")
    if header:
        lines.append("👤 " + " · ".join(header))

    # Фото
    pt = data.get("photo_type")
    if pt and pt != "none":
        photo_map = {
            "ru": {"regular": "📸 Фото загружено", "closed_face": "📸 Фото (закрытое лицо)", "silhouette": "📸 Силуэт"},
            "uz": {"regular": "📸 Foto yuklangan", "closed_face": "📸 Foto (yuz yopiq)", "silhouette": "📸 Siluet"},
        }
        lines.append(photo_map[L].get(pt, f"📸 {pt}"))

    # Телосложение
    body_map = {
        "ru": {"slim": "Стройный/ая", "average": "Среднее", "athletic": "Спортивный/ая", "full": "Плотный/ая"},
        "uz": {"slim": "Ozg'in", "average": "O'rtacha", "athletic": "Sportchilarga xos", "full": "To'ladan kelgan"},
    }
    body = data.get("body_type")
    if body:
        lines.append(body_map[L].get(body, body))

    # Национальность
    nat = data.get("nationality")
    if nat:
        lines.append(f"{'Нац.' if L == 'ru' else 'Millat'}: {nationality_label(nat, L)}")

    # Город + район
    city = data.get("city")
    if city:
        district = data.get("district")
        if district:
            lines.append(f"📍 {city}, {district}")
        else:
            lines.append(f"📍 {city}")

    # Образование
    edu_map = {
        "ru": {"secondary": "Среднее", "vocational": "Среднее спец.", "higher": "Высшее", "studying": "Студент/ка"},
        "uz": {"secondary": "O'rta", "vocational": "O'rta maxsus", "higher": "Oliy", "studying": "Talaba"},
    }
    edu = data.get("education")
    if edu:
        edu_label = edu_map[L].get(edu, edu)
        uni = data.get("university_info")
        if edu == "studying" and uni:
            # Студент + детали → показываем только "ВУЗ, курс" без слова "Студент/ка"
            edu_label = uni
        elif uni:
            edu_label += f", {uni}"
        lines.append(f"🎓 {edu_label}")

    # Занятость
    occ = data.get("occupation")
    if occ and occ != "—":
        lines.append(f"💼 {occupation_label(occ, L)}")

    # Религиозность
    rel_map = {
        "ru": {"practicing": "🕌 Практикующий/ая", "moderate": "☪️ Умеренный/ая", "secular": "🌐 Светский/ая"},
        "uz": {"practicing": "🕌 Amaliyotchi", "moderate": "☪️ Mo'tadil", "secular": "🌐 Dunyoviy"},
    }
    rel = data.get("religiosity")
    if rel:
        lines.append(rel_map[L].get(rel, rel))

    # Семейное положение
    mar_map = {
        "ru": {"never_married": "Не был(а) в браке", "divorced": "Разведён/а", "widowed": "Вдовец/Вдова"},
        "uz": {"never_married": "Turmush qurmagan", "divorced": "Ajrashgan", "widowed": "Beva"},
    }
    mar = data.get("marital_status")
    if mar:
        lines.append(f"💍 {mar_map[L].get(mar, mar)}")

    # Дети (показываем только если marital != never_married)
    ch = data.get("children_status")
    if mar and mar != "never_married" and ch:
        if ch == "yes_with_me":
            lines.append("👨\u200d👧 Есть дети (живут со мной)" if L == "ru"
                         else "👨\u200d👧 Bolalari bor (men bilan)")
        elif ch == "yes_with_ex":
            lines.append("👩\u200d👧 Есть дети (с бывш. супруг.)" if L == "ru"
                         else "👩\u200d👧 Bolalari bor (sobiq turmush o'rtog'im bilan)")
        elif ch == "no":
            lines.append("👶 Детей нет" if L == "ru" else "👶 Bolalari yo'q")

    # Телефон родителей
    phone = data.get("parent_phone")
    if phone:
        lines.append(f"📞 {phone}")

    # Telegram родителей и кандидата
    parent_tg = data.get("parent_telegram")
    if parent_tg:
        lines.append(f"📱 {parent_tg}")

    candidate_tg = data.get("candidate_telegram")
    if candidate_tg:
        lines.append(f"💬 {candidate_tg}")

    if not lines:
        return ""

    header_line = "📋 Анкета:" if L == "ru" else "📋 Anketa:"
    return header_line + "\n" + "\n".join(lines)


def _with_card(data: dict, lang: str, question_text: str) -> str:
    """Объединяет карточку + разделитель + вопрос."""
    card = build_card(data, lang)
    if card:
        return card + SEP + question_text
    return question_text


async def _delete_old(message: Message, state: FSMContext):
    """Удаляет набранный текст пользователя и предыдущее сообщение бота."""
    try:
        await message.delete()
    except Exception:
        pass
    data = await state.get_data()
    old_id = data.get("last_bot_msg")
    if old_id:
        try:
            await message.bot.delete_message(message.chat.id, old_id)
        except Exception:
            pass


async def _lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "ru")


async def _child_label(state: FSMContext) -> str:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    ptype = data.get("profile_type", "son")
    return t("son", lang) if ptype == "son" else t("daughter", lang)


async def _ptype(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("profile_type", "son")


async def _gendered_key(state: FSMContext, base_key: str) -> str:
    ptype = await _ptype(state)
    return f"{base_key}_{ptype}"


# ══════════════════════════════════════
# ЭТАП 1 — Быстрый старт (10 вопросов)
# ══════════════════════════════════════

# ── Старт анкеты ──
@router.callback_query(F.data == "quest:start")
async def quest_start(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    child = await _child_label(state)
    bar = progress_bar(1, 14)
    await callback.message.edit_text(
        t("q1", lang, child=child, bar=bar),
    )
    await state.update_data(last_bot_msg=callback.message.message_id)
    await state.set_state(QuestionnaireStates.q1_name)
    await callback.answer()


# ── 1. Имя ──
@router.message(QuestionnaireStates.q1_name)
async def q1_name(message: Message, state: FSMContext):
    await _delete_old(message, state)
    await state.update_data(name=message.text.strip())
    lang = await _lang(state)
    data = await state.get_data()
    bar = progress_bar(2, 14)
    q_text = t("q2", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    sent = await message.answer(full_text, reply_markup=back_step_kb(lang))
    await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q2_birth_year)


# ── 2A. Год рождения ──
@router.message(QuestionnaireStates.q2_birth_year)
async def q2_birth_year(message: Message, state: FSMContext):
    await _delete_old(message, state)
    lang = await _lang(state)
    text = message.text.strip()
    if not text.isdigit():
        err = "⚠️ Raqam kiriting" if lang == "uz" else "⚠️ Введите число"
        sent = await message.answer(err)
        await state.update_data(last_bot_msg=sent.message_id)
        return
    year = int(text)
    age = datetime.now().year - year
    if age < 18 or age > 60:
        err = ("⚠️ Yosh 18 dan 60 gacha bo'lishi kerak." if lang == "uz"
               else "⚠️ Возраст должен быть от 18 до 60 лет.")
        sent = await message.answer(err)
        await state.update_data(last_bot_msg=sent.message_id)
        return
    await state.update_data(birth_year=year, age=age)
    data = await state.get_data()
    bar = progress_bar(2, 14)
    q_text = t("q2_height", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    sent = await message.answer(full_text, reply_markup=back_step_kb(lang))
    await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q3_height)


# ── 2C. Рост ──
@router.message(QuestionnaireStates.q3_height)
async def q3_height(message: Message, state: FSMContext):
    await _delete_old(message, state)
    lang = await _lang(state)
    text = message.text.strip()
    if not text.isdigit() or not (140 <= int(text) <= 220):
        err = ("⚠️ Bo'yni to'g'ri kiriting (140–220 sm)" if lang == "uz"
               else "⚠️ Введите корректный рост (140–220 см)")
        sent = await message.answer(err)
        await state.update_data(last_bot_msg=sent.message_id)
        return
    await state.update_data(height_cm=int(text))
    # → 3. Фото с мотивацией
    await _ask_photo(message, state, lang)


# ── 3. Фото с мотивацией ──
async def _ask_photo(message_or_callback, state: FSMContext, lang: str):
    """Показать вопрос 3 — фото с мотивационным текстом."""
    data = await state.get_data()
    bar = progress_bar(3, 14)
    q_text = t("q3_photo", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    kb = add_nav(photo_type_kb(lang).inline_keyboard, lang, "back_step", show_main=False)

    if hasattr(message_or_callback, "message"):
        await message_or_callback.message.edit_text(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=message_or_callback.message.message_id)
    else:
        sent = await message_or_callback.answer(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q21_photo_type)


# ── 3. Обработка выбора типа фото ──
@router.callback_query(F.data.startswith("photo:"), QuestionnaireStates.q21_photo_type)
async def photo_type(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(photo_type=value)
    lang = await _lang(state)

    if value == "none":
        # Без фото → сразу к телосложению (вопрос 4)
        await _ask_body_type(callback, state, lang)
    elif value == "closed_face":
        await callback.message.edit_text(t("q21_closed_face_hint", lang), reply_markup=back_step_kb(lang))
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q21_photo_upload)
    else:
        await callback.message.edit_text(t("q21_upload", lang), reply_markup=back_step_kb(lang))
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q21_photo_upload)
    await callback.answer()


@router.message(QuestionnaireStates.q21_photo_upload, F.photo)
async def photo_upload(message: Message, state: FSMContext):
    await _delete_old(message, state)
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    lang = await _lang(state)
    # → 4. Телосложение
    await _ask_body_type(message, state, lang)


@router.message(QuestionnaireStates.q21_photo_upload)
async def photo_upload_invalid(message: Message, state: FSMContext):
    await _delete_old(message, state)
    lang = await _lang(state)
    sent = await message.answer(t("q21_upload", lang))
    await state.update_data(last_bot_msg=sent.message_id)


# ── 4. Телосложение ──
async def _ask_body_type(message_or_callback, state: FSMContext, lang: str):
    """Показать вопрос 4 — телосложение."""
    data = await state.get_data()
    bar = progress_bar(4, 14)
    q_text = t("q4_body_type", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    gender = data.get("profile_type", "son")
    kb = add_nav(body_type_kb(lang, gender).inline_keyboard, lang, "back_step", show_main=False)

    if hasattr(message_or_callback, "message"):
        await message_or_callback.message.edit_text(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=message_or_callback.message.message_id)
    else:
        sent = await message_or_callback.answer(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q4_body_type)


@router.callback_query(F.data.startswith("body:"), QuestionnaireStates.q4_body_type)
async def q4_body_type(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(body_type=value)
    lang = await _lang(state)
    data = await state.get_data()
    # → 5. Национальность
    bar = progress_bar(5, 14)
    q_text = t("q12", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    await callback.message.edit_text(
        full_text,
        reply_markup=add_nav(nationality_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
    )
    await state.update_data(last_bot_msg=callback.message.message_id)
    await state.set_state(QuestionnaireStates.q12_nationality)
    await callback.answer()


# ── 5. Национальность ──
async def _advance_after_nationality(callback_or_message, state: FSMContext, lang: str) -> None:
    """После выбора/ввода национальности — переход к шагу «Город»."""
    data = await state.get_data()
    bar = progress_bar(6, 14)
    q_text = t("q6_city", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    kb = add_nav(city_kb(lang).inline_keyboard, lang, "back_step", show_main=False)
    if hasattr(callback_or_message, "message"):
        await callback_or_message.message.edit_text(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=callback_or_message.message.message_id)
    else:
        sent = await callback_or_message.answer(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q6_city)


@router.callback_query(F.data.startswith("nat:"), QuestionnaireStates.q12_nationality)
async def q5_nationality(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    lang = await _lang(state)

    if value == "more":
        await callback.message.edit_reply_markup(reply_markup=nationality_more_kb(lang))
        await callback.answer()
        return
    if value == "back":
        await callback.message.edit_reply_markup(
            reply_markup=add_nav(nationality_kb(lang).inline_keyboard, lang, "back_step", show_main=False)
        )
        await callback.answer()
        return
    if value == "custom":
        prompt = "✍️ Введите национальность:" if lang != "uz" else "✍️ Millatingizni kiriting:"
        await callback.message.edit_text(prompt)
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q12_nationality_custom)
        await callback.answer()
        return

    await state.update_data(nationality=value)
    await _advance_after_nationality(callback, state, lang)
    await callback.answer()


@router.message(QuestionnaireStates.q12_nationality_custom)
async def q5_nationality_custom(message: Message, state: FSMContext):
    await _delete_old(message, state)
    nat = (message.text or "").strip()[:50]
    if not nat:
        return
    await state.update_data(nationality=nat)
    lang = await _lang(state)
    await _advance_after_nationality(message, state, lang)


# ── 6. Страна/Область/Район — двухуровневая навигация ──
# Страны (первый уровень)
_CITY_NAMES = {
    "ru": {
        "uzbekistan":   "Узбекистан",
        "usa":          "🇺🇸 США",
        "russia":       "🇷🇺 Россия",
        "kazakhstan":   "🇰🇿 Казахстан",
        "kyrgyzstan":   "🇰🇬 Кыргызстан",
        "tajikistan":   "🇹🇯 Таджикистан",
        "turkmenistan": "🇹🇲 Туркменистан",
        "europe":       "🌍 Европа",
        "other":        "🌏 Другая страна",
    },
    "uz": {
        "uzbekistan":   "O'zbekiston",
        "usa":          "🇺🇸 AQSH",
        "russia":       "🇷🇺 Rossiya",
        "kazakhstan":   "🇰🇿 Qozog'iston",
        "kyrgyzstan":   "🇰🇬 Qirg'iziston",
        "tajikistan":   "🇹🇯 Tojikiston",
        "turkmenistan": "🇹🇲 Turkmaniston",
        "europe":       "🌍 Yevropa",
        "other":        "🌏 Boshqa mamlakat",
    },
}

# Области Узбекистана (второй уровень)
_REGION_NAMES = {
    "ru": {
        "tashkent":        "Ташкент",
        "tashkent_region": "Ташкентская область",
        "samarkand":       "Самарканд",
        "fergana":         "Фергана",
        "andijan":         "Андижан",
        "namangan":        "Наманган",
        "bukhara":         "Бухара",
        "kashkadarya":     "Кашкадарья",
        "surkhandarya":    "Сурхандарья",
        "khorezm":         "Хорезм",
        "karakalpakstan":  "Каракалпакстан",
        "jizzakh":         "Джизак",
        "sirdarya":        "Сырдарья",
    },
    "uz": {
        "tashkent":        "Toshkent",
        "tashkent_region": "Toshkent viloyati",
        "samarkand":       "Samarqand",
        "fergana":         "Farg'ona",
        "andijan":         "Andijon",
        "namangan":        "Namangan",
        "bukhara":         "Buxoro",
        "kashkadarya":     "Qashqadaryo",
        "surkhandarya":    "Surxondaryo",
        "khorezm":         "Xorazm",
        "karakalpakstan":  "Qoraqalpog'iston",
        "jizzakh":         "Jizzax",
        "sirdarya":        "Sirdaryo",
    },
}

# Коды областей УЗ (для которых спрашиваем район)
_UZ_REGION_CODES = set(_REGION_NAMES["ru"].keys())


# ── Навигация подменю «Ещё страны» — ДОЛЖНЫ быть выше broad city:* handler ──

@router.callback_query(F.data == "city:more", QuestionnaireStates.q6_city)
async def q6_city_show_more(callback: CallbackQuery, state: FSMContext):
    """Показать подменю «Ещё страны» — меняем только клавиатуру карточки."""
    lang = await _lang(state)
    # show_back=False/show_main=False → без дубля «Назад» из add_nav.
    # Единственная «🔙 Назад» — из самой city_more_kb (callback city:back_main).
    kb = add_nav(
        city_more_kb(lang).inline_keyboard,
        lang, "back_step",
        show_back=False, show_main=False,
    )
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data == "city:back_main", QuestionnaireStates.q6_city)
async def q6_city_back_main(callback: CallbackQuery, state: FSMContext):
    """Вернуть основной список стран из подменю «Ещё страны»."""
    lang = await _lang(state)
    kb = add_nav(city_kb(lang).inline_keyboard, lang, "back_step", show_main=False)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb)
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("city:"), QuestionnaireStates.q6_city)
async def q6_city_selected(callback: CallbackQuery, state: FSMContext):
    """Шаг 1: выбор страны."""
    city_code = callback.data.split(":")[1]
    lang = await _lang(state)
    L = lang if lang in ("ru", "uz") else "ru"

    if city_code == "uzbekistan":
        # Узбекистан → показать подменю из 13 областей
        data = await state.get_data()
        bar = progress_bar(6, 14)
        if lang == "uz":
            q_text = f"🏡 6/14-savol\n{bar}\n\n🇺🇿 Viloyatni tanlang:"
        else:
            q_text = f"🏡 Вопрос 6/14\n{bar}\n\n🇺🇿 Выберите область:"
        full_text = _with_card(data, lang, q_text)
        await callback.message.edit_text(full_text, reply_markup=uz_regions_kb(lang))
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q6_region)
    else:
        # Зарубежная страна → сохраняем, район не нужен, сразу к образованию
        city_name = _CITY_NAMES[L].get(city_code, city_code)
        await state.update_data(
            city_code=city_code,
            city=city_name,
            district="",
            country=city_code,
        )
        await _goto_education_after_city(callback, state, lang)
    await callback.answer()


@router.callback_query(F.data == "city_back", QuestionnaireStates.q6_region)
async def q6_city_back(callback: CallbackQuery, state: FSMContext):
    """Возврат из подменю областей к выбору страны."""
    lang = await _lang(state)
    data = await state.get_data()
    bar = progress_bar(6, 14)
    q_text = t("q6_city", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    await callback.message.edit_text(
        full_text,
        reply_markup=add_nav(city_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
    )
    await state.update_data(last_bot_msg=callback.message.message_id)
    await state.set_state(QuestionnaireStates.q6_city)
    await callback.answer()


@router.callback_query(F.data.startswith("region:"), QuestionnaireStates.q6_region)
async def q6_region_selected(callback: CallbackQuery, state: FSMContext):
    """Шаг 2: выбор области УЗ → спрашиваем район."""
    region_code = callback.data.split(":")[1]
    lang = await _lang(state)
    L = lang if lang in ("ru", "uz") else "ru"
    region_name = _REGION_NAMES[L].get(region_code, region_code)

    await state.update_data(
        city_code=region_code,
        city=region_name,
        country="uzbekistan",
    )

    data = await state.get_data()
    bar = progress_bar(6, 14)
    if lang == "uz":
        q_text = (f"🏡 6/14-savol\n{bar}\n\n"
                  f"Tanlandi: {region_name}\n\n"
                  f"Tuman:\n"
                  f"(masalan: Yunusobod, Chilonzor)")
    else:
        q_text = (f"🏡 Вопрос 6/14\n{bar}\n\n"
                  f"Выбрано: {region_name}\n\n"
                  f"Район:\n"
                  f"(например: Юнусабад, Чиланзар)")
    full_text = _with_card(data, lang, q_text)
    await callback.message.edit_text(
        full_text,
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
    )
    await state.update_data(last_bot_msg=callback.message.message_id)
    await state.set_state(QuestionnaireStates.q6_district)
    await callback.answer()


async def _goto_education_after_city(callback: CallbackQuery, state: FSMContext, lang: str):
    """Переход на вопрос об образовании (после выбора зарубежной страны)."""
    data = await state.get_data()
    bar = progress_bar(7, 14)
    q_text = t("q5", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    await callback.message.edit_text(
        full_text,
        reply_markup=add_nav(education_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
    )
    await state.update_data(last_bot_msg=callback.message.message_id)
    await state.set_state(QuestionnaireStates.q5_education)
    await callback.answer()


# ── 6b. Район текстом ──
@router.message(QuestionnaireStates.q6_district)
async def q6_district_entered(message: Message, state: FSMContext):
    await _delete_old(message, state)
    lang = await _lang(state)
    text_input = message.text.strip()
    await state.update_data(district=text_input)

    data = await state.get_data()
    # → 7. Образование
    bar = progress_bar(7, 14)
    q_text = t("q5", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    sent = await message.answer(
        full_text,
        reply_markup=add_nav(education_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
    )
    await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q5_education)


# ── 6b. Пропустить район ──
@router.callback_query(F.data == "skip", QuestionnaireStates.q6_district)
async def q6_district_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await state.update_data(district="")
    data = await state.get_data()
    # → 7. Образование
    bar = progress_bar(7, 14)
    q_text = t("q5", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    await callback.message.edit_text(
        full_text,
        reply_markup=add_nav(education_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
    )
    await state.update_data(last_bot_msg=callback.message.message_id)
    await state.set_state(QuestionnaireStates.q5_education)
    await callback.answer()


# ── 7. Образование ──
@router.callback_query(F.data.startswith("edu:"), QuestionnaireStates.q5_education)
async def q7_education(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(education=value)
    lang = await _lang(state)

    if value == "studying":
        data = await state.get_data()
        card = build_card(data, lang)
        q_text = t("q5_university", lang)
        full_text = (card + SEP + q_text) if card else q_text
        await callback.message.edit_text(full_text, reply_markup=back_step_kb(lang))
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q5_university)
    else:
        # → 8. Занятость (кнопки)
        await _ask_occupation(callback, state, lang)
    await callback.answer()


@router.message(QuestionnaireStates.q5_university)
async def q7_university(message: Message, state: FSMContext):
    await _delete_old(message, state)
    await state.update_data(university_info=message.text.strip())
    lang = await _lang(state)
    # Студент → пропускаем занятость → 9. Религиозность
    await state.update_data(occupation_type="student", occupation="student")
    await _ask_religion(message, state, lang)


# ── 8. Занятость (кнопки) ──
async def _ask_occupation(message_or_callback, state: FSMContext, lang: str):
    """Показать вопрос 8 — занятость с кнопками."""
    data = await state.get_data()
    bar = progress_bar(8, 14)
    gender = data.get("profile_type", "son")
    q_text = t("q8_occupation", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    kb = add_nav(occupation_kb(lang, gender).inline_keyboard, lang, "back_step", show_main=False)

    if hasattr(message_or_callback, "message"):
        await message_or_callback.message.edit_text(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=message_or_callback.message.message_id)
    else:
        sent = await message_or_callback.answer(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q6_work_choice)


@router.callback_query(F.data.startswith("occ:"), QuestionnaireStates.q6_work_choice)
async def q8_occupation_choice(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]
    lang = await _lang(state)
    # Любой выбор → сохраняем и сразу к вопросу о религиозности
    await state.update_data(occupation_type=choice, occupation=choice)
    await _ask_religion(callback, state, lang)
    await callback.answer()


# Legacy handlers for old work:specify / work:skip callbacks
@router.callback_query(F.data == "work:specify", QuestionnaireStates.q6_work_choice)
async def q8_work_specify(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await state.update_data(occupation_type="works")
    data = await state.get_data()
    bar = progress_bar(8, 14)
    q_text = t("q8_occupation_detail", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    await callback.message.edit_text(full_text, reply_markup=back_step_kb(lang))
    await state.update_data(last_bot_msg=callback.message.message_id)
    await state.set_state(QuestionnaireStates.q6_occupation)
    await callback.answer()


@router.callback_query(F.data == "work:skip", QuestionnaireStates.q6_work_choice)
async def q8_work_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await state.update_data(occupation="—")
    await _ask_religion(callback, state, lang)
    await callback.answer()


@router.message(QuestionnaireStates.q6_occupation)
async def q8_occupation_detail(message: Message, state: FSMContext):
    await _delete_old(message, state)
    await state.update_data(occupation=message.text.strip())
    lang = await _lang(state)
    # → 9. Религиозность
    await _ask_religion(message, state, lang)


# ── 9. Религиозность ──
async def _ask_religion(message_or_callback, state: FSMContext, lang: str):
    """Показать вопрос 9 — религиозность."""
    data = await state.get_data()
    bar = progress_bar(9, 14)
    q_text = t("q16", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    kb = add_nav(religiosity_kb(lang).inline_keyboard, lang, "back_step", show_main=False)

    if hasattr(message_or_callback, "message"):
        await message_or_callback.message.edit_text(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=message_or_callback.message.message_id)
    else:
        sent = await message_or_callback.answer(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q16_religiosity)


@router.callback_query(F.data.startswith("rel:"), QuestionnaireStates.q16_religiosity)
async def q9_religiosity(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(religiosity=value)
    lang = await _lang(state)
    data = await state.get_data()
    is_male = data.get("profile_type") == "son"
    # → 10. Семейное положение
    bar = progress_bar(10, 14)
    q_text = t("q_marital_status", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    await callback.message.edit_text(
        full_text,
        reply_markup=add_nav(marital_kb(lang, is_male).inline_keyboard, lang, "back_step", show_main=False),
    )
    await state.update_data(last_bot_msg=callback.message.message_id)
    await state.set_state(QuestionnaireStates.q_marital_status)
    await callback.answer()


# ── 10. Семейное положение ──
@router.callback_query(F.data.startswith("mar:"), QuestionnaireStates.q_marital_status)
async def q10_marital_status(callback: CallbackQuery, state: FSMContext):
    marital = callback.data.split(":")[1]  # never_married / divorced / widowed
    await state.update_data(marital_status=marital)
    lang = await _lang(state)

    if marital == "never_married":
        # Не был(а) в браке → детей нет → переход к блоку контактов
        await state.update_data(children_status="no")
        await _ask_parent_phone(callback, state)
    else:
        # Разведён/а или Вдовец/Вдова → спросить про детей
        data = await state.get_data()
        is_son = data.get("profile_type") == "son"
        card = build_card(data, lang)
        q_text = t("q_children", lang)
        full_text = (card + SEP + q_text) if card else q_text
        await callback.message.edit_text(
            full_text,
            reply_markup=add_nav(children_kb(lang, is_son).inline_keyboard, lang, "back_step", show_main=False),
        )
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q_children)
    await callback.answer()


# ── 10b. Дети (только если разведён/вдовец) ──
@router.callback_query(F.data.startswith("child:"), QuestionnaireStates.q_children)
async def q10_children(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    children_map = {"no": "no", "me": "yes_with_me", "ex": "yes_with_ex"}
    await state.update_data(children_status=children_map.get(value, value))
    # → 11. Телефон родителей
    await _ask_parent_phone(callback, state)
    await callback.answer()


# ══════════════════════════════════════
# Блок контактов (Q11-Q13) — обязательный
# ══════════════════════════════════════

async def _ask_parent_phone(message_or_callback, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = progress_bar(11, 14)
    q_text = t("q_parent_phone", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    kb = skip_back_kb(lang)

    if hasattr(message_or_callback, "message"):
        try:
            await message_or_callback.message.edit_text(full_text, reply_markup=kb)
            await state.update_data(last_bot_msg=message_or_callback.message.message_id)
        except Exception:
            sent = await message_or_callback.message.answer(full_text, reply_markup=kb)
            await state.update_data(last_bot_msg=sent.message_id)
    else:
        sent = await message_or_callback.answer(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q11_parent_phone)


@router.message(QuestionnaireStates.q11_parent_phone)
async def q11_parent_phone(message: Message, state: FSMContext):
    await _delete_old(message, state)
    lang = await _lang(state)
    raw = (message.text or "").strip()
    digits = "".join(c for c in raw if c.isdigit())

    phone = None
    if raw.startswith("+"):
        # Международный E.164: + и 7-15 цифр
        if 7 <= len(digits) <= 15:
            phone = f"+{digits}"
    else:
        # Без «+» — только UZ-шорткаты (обратная совместимость)
        if len(digits) == 9:
            phone = f"+998{digits}"
        elif len(digits) == 12 and digits.startswith("998"):
            phone = f"+{digits}"

    if phone is None:
        sent = await message.answer(t("q_phone_invalid", lang), reply_markup=skip_back_kb(lang))
        await state.update_data(last_bot_msg=sent.message_id)
        return

    await state.update_data(parent_phone=phone)
    await _ask_parent_telegram(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.q11_parent_phone)
async def q11_parent_phone_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parent_phone=None)
    await _ask_parent_telegram(callback, state)
    await callback.answer()


async def _ask_parent_telegram(message_or_callback, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = progress_bar(12, 14)
    q_text = t("q_parent_telegram", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    kb = skip_back_kb(lang)

    if hasattr(message_or_callback, "message"):
        try:
            await message_or_callback.message.edit_text(full_text, reply_markup=kb)
            await state.update_data(last_bot_msg=message_or_callback.message.message_id)
        except Exception:
            sent = await message_or_callback.message.answer(full_text, reply_markup=kb)
            await state.update_data(last_bot_msg=sent.message_id)
    else:
        sent = await message_or_callback.answer(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q12_parent_telegram)


@router.message(QuestionnaireStates.q12_parent_telegram)
async def q12_parent_telegram(message: Message, state: FSMContext):
    await _delete_old(message, state)
    tg = (message.text or "").strip()
    if tg and not tg.startswith("@"):
        tg = f"@{tg}"
    await state.update_data(parent_telegram=tg or None)
    await _ask_candidate_telegram(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.q12_parent_telegram)
async def q12_parent_telegram_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parent_telegram=None)
    await _ask_candidate_telegram(callback, state)
    await callback.answer()


async def _ask_candidate_telegram(message_or_callback, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = progress_bar(13, 14)
    q_text = t("q_candidate_telegram", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    kb = skip_back_kb(lang)

    if hasattr(message_or_callback, "message"):
        try:
            await message_or_callback.message.edit_text(full_text, reply_markup=kb)
            await state.update_data(last_bot_msg=message_or_callback.message.message_id)
        except Exception:
            sent = await message_or_callback.message.answer(full_text, reply_markup=kb)
            await state.update_data(last_bot_msg=sent.message_id)
    else:
        sent = await message_or_callback.answer(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q13_candidate_telegram)


async def _validate_contacts_and_continue(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    if (not data.get("parent_phone")
            and not data.get("parent_telegram")
            and not data.get("candidate_telegram")):
        # хотя бы один контакт обязателен — возврат на Q11 (телефон)
        if hasattr(m_or_cb, "answer") and callable(getattr(m_or_cb, "answer", None)) and hasattr(m_or_cb, "id"):
            try:
                await m_or_cb.answer(t("q_at_least_one_contact", lang), show_alert=True)
            except Exception:
                pass
        else:
            try:
                await m_or_cb.answer(t("q_at_least_one_contact", lang))
            except Exception:
                pass
        await _ask_parent_phone(m_or_cb, state)
        return
    await _ask_address(m_or_cb, state)


async def _show_stage1_complete_from(m_or_cb, state: FSMContext):
    """Обёртка: _show_stage1_complete принимает CallbackQuery, но финиш может прийти из Message."""
    from bot.handlers.tariff import _show_summary
    if hasattr(m_or_cb, "message") and hasattr(m_or_cb, "id"):
        await _show_summary(m_or_cb, state, is_callback=True)
    else:
        await _show_summary(m_or_cb, state, is_callback=False)


@router.message(QuestionnaireStates.q13_candidate_telegram)
async def q13_candidate_telegram(message: Message, state: FSMContext):
    await _delete_old(message, state)
    tg = (message.text or "").strip()
    if tg and not tg.startswith("@"):
        tg = f"@{tg}"
    await state.update_data(candidate_telegram=tg or None)
    await _validate_contacts_and_continue(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.q13_candidate_telegram)
async def q13_candidate_telegram_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(candidate_telegram=None)
    await _validate_contacts_and_continue(callback, state)
    await callback.answer()


# ══════════════════════════════════════
# БЛОК 14: АДРЕС (text / geolocation / link / skip)
# ══════════════════════════════════════

async def _ask_address(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = progress_bar(14, 14)

    if lang == "uz":
        body = f"🏠 14/14-savol\n{bar}\n\nManzil yoki geolokatsiya:"
        opts = [
            ("🏠 Manzilni yozish", "addr:text"),
            ("📍 Geolokatsiya yuborish", "addr:geo"),
            ("🗺 Xarita havolasi", "addr:link"),
            ("⏭ O'tkazib yuborish", "addr:skip"),
        ]
    else:
        body = f"🏠 Вопрос 14/14\n{bar}\n\nАдрес или геолокация:"
        opts = [
            ("🏠 Написать адрес", "addr:text"),
            ("📍 Отправить геолокацию", "addr:geo"),
            ("🗺 Ссылка на карту", "addr:link"),
            ("⏭ Пропустить", "addr:skip"),
        ]

    full_text = _with_card(data, lang, body)
    kb_rows = [[InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts]
    kb = add_nav(kb_rows, lang, "back_step", show_main=False)

    if hasattr(m_or_cb, "message") and hasattr(m_or_cb, "id"):
        try:
            await m_or_cb.message.edit_text(full_text, reply_markup=kb)
            await state.update_data(last_bot_msg=m_or_cb.message.message_id)
        except Exception:
            sent = await m_or_cb.message.answer(full_text, reply_markup=kb)
            await state.update_data(last_bot_msg=sent.message_id)
    else:
        sent = await m_or_cb.answer(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)
    await state.set_state(QuestionnaireStates.q14_address)


@router.callback_query(F.data.startswith("addr:"), QuestionnaireStates.q14_address)
async def q14_address_choice(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("addr:", "")
    lang = await _lang(state)

    # skip → сразу финальный экран
    if choice == "skip":
        await _show_stage1_complete_from(callback, state)
        await callback.answer()
        return

    # Удаляем окно выбора
    try:
        await callback.message.delete()
    except Exception:
        pass
    await state.update_data(last_bot_msg=None)

    if choice == "text":
        text = "Ko'cha/mahalla nomini kiriting:" if lang == "uz" else "Введите улицу/махаллю:"
        sent = await callback.message.answer(text, reply_markup=skip_back_kb(lang))
        await state.update_data(last_bot_msg=sent.message_id)
        await state.set_state(QuestionnaireStates.q14_address_text)
    elif choice == "geo":
        # known limitation: reply-keyboard для геоточки не совмещается с inline-Назад
        geo_label = "📍 Geolokatsiya yuborish" if lang == "uz" else "📍 Отправить геолокацию"
        title = "📍 Geolokatsiya:" if lang == "uz" else "📍 Геолокация:"
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=geo_label, request_location=True)]],
            resize_keyboard=True, one_time_keyboard=True,
        )
        sent = await callback.message.answer(title, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)
        await state.set_state(QuestionnaireStates.q14_location)
    elif choice == "link":
        text = "🗺 Google Maps yoki 2GIS havolasini kiriting:" if lang == "uz" else "🗺 Вставьте ссылку Google Maps или 2GIS:"
        sent = await callback.message.answer(text, reply_markup=skip_back_kb(lang))
        await state.update_data(last_bot_msg=sent.message_id)
        await state.set_state(QuestionnaireStates.q14_address_link)

    await callback.answer()


@router.message(QuestionnaireStates.q14_address_text)
async def q14_address_text(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    try:
        await message.delete()
    except Exception:
        pass
    await _show_stage1_complete_from(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.q14_address_text)
async def q14_address_text_skip(callback: CallbackQuery, state: FSMContext):
    await _show_stage1_complete_from(callback, state)
    await callback.answer()


@router.message(QuestionnaireStates.q14_location)
async def q14_location(message: Message, state: FSMContext):
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        await state.update_data(
            location_lat=lat,
            location_lon=lon,
            location_link=f"https://maps.google.com/?q={lat},{lon}",
        )
    # Удаляем сообщение пользователя с геолокацией
    try:
        await message.delete()
    except Exception:
        pass
    # Убираем reply-клавиатуру одноразовым сообщением, которое тут же удаляем
    try:
        tmp = await message.answer("✓", reply_markup=ReplyKeyboardRemove())
        await tmp.delete()
    except Exception:
        pass
    # Удаляем старое сообщение бота
    data = await state.get_data()
    last_id = data.get("last_bot_msg")
    if last_id:
        try:
            await message.bot.delete_message(message.chat.id, last_id)
        except Exception:
            pass
        await state.update_data(last_bot_msg=None)
    await _show_stage1_complete_from(message, state)


@router.message(QuestionnaireStates.q14_address_link)
async def q14_address_link(message: Message, state: FSMContext):
    await state.update_data(location_link=message.text.strip())
    try:
        await message.delete()
    except Exception:
        pass
    await _show_stage1_complete_from(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.q14_address_link)
async def q14_address_link_skip(callback: CallbackQuery, state: FSMContext):
    await _show_stage1_complete_from(callback, state)
    await callback.answer()


# ══════════════════════════════════════
# Экран завершения Этапа 1
# ══════════════════════════════════════

async def _show_stage1_complete(callback: CallbackQuery, state: FSMContext):
    """После последнего вопроса — показать резюме анкеты (экран выбора тарифа удалён)."""
    from bot.handlers.tariff import _show_summary
    await _show_summary(callback, state, is_callback=True)


# ══════════════════════════════════════
# Кнопка «Назад»
# ══════════════════════════════════════

@router.callback_query(F.data == "back_step")
async def back_step(callback: CallbackQuery, state: FSMContext):
    """Возврат к предыдущему шагу."""
    current = await state.get_state()
    lang = await _lang(state)
    child = await _child_label(state)
    data = await state.get_data()
    is_male = data.get("profile_type") == "son"
    gender = data.get("profile_type", "son")

    # Определяем куда вернуться из stage1_complete
    marital = data.get("marital_status")
    if marital and marital != "never_married":
        complete_back = ("q_children", QuestionnaireStates.q_children,
                         lambda: add_nav(children_kb(lang, is_male).inline_keyboard, lang, "back_step", show_main=False))
    else:
        complete_back = ("q_marital_status", QuestionnaireStates.q_marital_status,
                         lambda: add_nav(marital_kb(lang, is_male).inline_keyboard, lang, "back_step", show_main=False))

    # Определяем куда вернуться из q16_religiosity
    edu = data.get("education")
    if edu == "studying":
        religion_back = ("q5_university", QuestionnaireStates.q5_university, None)
    else:
        religion_back = ("q8_occupation", QuestionnaireStates.q6_work_choice,
                         lambda: add_nav(occupation_kb(lang, gender).inline_keyboard, lang, "back_step", show_main=False))

    back_map = {
        QuestionnaireStates.q2_birth_year.state: (
            "q1", QuestionnaireStates.q1_name, None,
            lambda l, c: t("q1", l, child=c, bar=progress_bar(1, 14))
        ),
        QuestionnaireStates.q3_height.state: (
            "q2", QuestionnaireStates.q2_birth_year, None,
            lambda l, c: _with_card(data, l, t("q2", l, bar=progress_bar(2, 14)))
        ),
        QuestionnaireStates.q21_photo_type.state: (
            "q2_height", QuestionnaireStates.q3_height, None,
            lambda l, c: _with_card(data, l, t("q2_height", l, bar=progress_bar(2, 14)))
        ),
        QuestionnaireStates.q21_photo_upload.state: (
            "q3_photo", QuestionnaireStates.q21_photo_type,
            lambda: add_nav(photo_type_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q3_photo", l, bar=progress_bar(3, 14)))
        ),
        QuestionnaireStates.q4_body_type.state: (
            "q3_photo", QuestionnaireStates.q21_photo_type,
            lambda: add_nav(photo_type_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q3_photo", l, bar=progress_bar(3, 14)))
        ),
        QuestionnaireStates.q12_nationality.state: (
            "q4_body_type", QuestionnaireStates.q4_body_type,
            lambda: add_nav(body_type_kb(lang, gender).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q4_body_type", l, bar=progress_bar(4, 14)))
        ),
        QuestionnaireStates.q6_city.state: (
            "q12", QuestionnaireStates.q12_nationality,
            lambda: add_nav(nationality_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q12", l, bar=progress_bar(5, 14)))
        ),
        QuestionnaireStates.q6_region.state: (
            "q6_city", QuestionnaireStates.q6_city,
            lambda: add_nav(city_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q6_city", l, bar=progress_bar(6, 14)))
        ),
        QuestionnaireStates.q6_district.state: (
            "q6_city", QuestionnaireStates.q6_region,
            lambda: uz_regions_kb(lang),
            lambda l, c: _with_card(
                data, l,
                (f"🏡 6/14-savol\n{progress_bar(6, 14)}\n\n🇺🇿 Viloyatni tanlang:"
                 if l == "uz" else
                 f"🏡 Вопрос 6/14\n{progress_bar(6, 14)}\n\n🇺🇿 Выберите область:"),
            ),
        ),
        QuestionnaireStates.q5_education.state: (
            "q6_city", QuestionnaireStates.q6_city,
            lambda: add_nav(city_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q6_city", l, bar=progress_bar(6, 14)))
        ),
        QuestionnaireStates.q5_university.state: (
            "q5", QuestionnaireStates.q5_education,
            lambda: add_nav(education_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q5", l, bar=progress_bar(7, 14)))
        ),
        QuestionnaireStates.q6_work_choice.state: (
            "q5", QuestionnaireStates.q5_education,
            lambda: add_nav(education_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q5", l, bar=progress_bar(7, 14)))
        ),
        QuestionnaireStates.q6_occupation.state: (
            "q8_occupation", QuestionnaireStates.q6_work_choice,
            lambda: add_nav(occupation_kb(lang, gender).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q8_occupation", l, bar=progress_bar(8, 14)))
        ),
        QuestionnaireStates.q16_religiosity.state: (
            religion_back[0], religion_back[1], religion_back[2],
            lambda l, c: _with_card(data, l, t(religion_back[0], l, bar=progress_bar(8 if edu != "studying" else 7, 14)))
        ),
        QuestionnaireStates.q_marital_status.state: (
            "q16", QuestionnaireStates.q16_religiosity,
            lambda: add_nav(religiosity_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q16", l, bar=progress_bar(9, 14)))
        ),
        QuestionnaireStates.q_children.state: (
            "q_marital_status", QuestionnaireStates.q_marital_status,
            lambda: add_nav(marital_kb(lang, is_male).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q_marital_status", l, bar=progress_bar(10, 14)))
        ),
        QuestionnaireStates.q11_parent_phone.state: (
            complete_back[0], complete_back[1], complete_back[2],
            lambda l, c: _with_card(data, l, t(complete_back[0], l, bar=progress_bar(10, 14)))
        ),
        QuestionnaireStates.q12_parent_telegram.state: (
            "q_parent_phone", QuestionnaireStates.q11_parent_phone, None,
            lambda l, c: _with_card(data, l, t("q_parent_phone", l, bar=progress_bar(11, 14)))
        ),
        QuestionnaireStates.q13_candidate_telegram.state: (
            "q_parent_telegram", QuestionnaireStates.q12_parent_telegram,
            lambda: skip_back_kb(lang),
            lambda l, c: _with_card(data, l, t("q_parent_telegram", l, bar=progress_bar(12, 14)))
        ),
        QuestionnaireStates.q14_address.state: (
            "q_candidate_telegram", QuestionnaireStates.q13_candidate_telegram,
            lambda: skip_back_kb(lang),
            lambda l, c: _with_card(data, l, t("q_candidate_telegram", l, bar=progress_bar(13, 14)))
        ),
        # q14_address_text / q14_location / q14_address_link / stage1_complete →
        # возврат к _ask_address (экрану выбора text/geo/link/skip).
        # Обрабатывается ДО back_map.get() через спец-ветку ниже.
    }

    # Спец-ветка: возврат к экрану выбора адреса из его под-экранов (text/geo/link)
    # и из stage1_complete. _ask_address собирает свою inline-kb с addr:*,
    # что не вписывается в унифицированный рендер back_map.
    q14_return_to_address = {
        QuestionnaireStates.q14_address_text.state,
        QuestionnaireStates.q14_location.state,
        QuestionnaireStates.q14_address_link.state,
        QuestionnaireStates.stage1_complete.state,
    }
    if current in q14_return_to_address:
        await _ask_address(callback, state)
        await callback.answer("🔙")
        return

    entry = back_map.get(current)
    if entry:
        text_key, prev_state, kb_func, text_func = entry
        if text_func:
            msg_text = text_func(lang, child)
        else:
            msg_text = t(text_key, lang, child=child, bar=progress_bar(1, 14))
        if kb_func:
            kb = kb_func()
        else:
            kb = back_step_kb(lang)
        try:
            await callback.message.edit_text(msg_text, reply_markup=kb)
            await state.update_data(last_bot_msg=callback.message.message_id)
        except Exception:
            sent = await callback.message.answer(msg_text, reply_markup=kb)
            await state.update_data(last_bot_msg=sent.message_id)
        await state.set_state(prev_state)
    await callback.answer("🔙")
