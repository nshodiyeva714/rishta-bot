"""Анкета — ЭТАП 1: Быстрый старт (10 вопросов).

Порядок: Имя(1) → Год рождения+Рост(2) → Фото(3) → Телосложение(4) →
         Национальность(5) → Город(6) → Образование(7) → Занятость(8) →
         Религиозность(9) → Семейное положение+дети(10) → Завершение
"""

from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.states import QuestionnaireStates, TariffStates
from bot.texts import t
from bot.keyboards.inline import (
    education_kb, nationality_kb, religiosity_kb,
    marital_kb, children_kb, photo_type_kb,
    confirm_age_kb, tariff_kb, skip_kb,
    back_step_kb, add_nav, body_type_kb, occupation_kb,
    anketa_finish_kb, city_kb,
)

router = Router()

SEP = "\n\n━━━━━━━━━━━━━\n\n"


# ══════════════════════════════════════
# Утилиты
# ══════════════════════════════════════

def progress_bar(current: int, total: int) -> str:
    """Прогресс-бар для вопросов анкеты."""
    filled = round(current / total * 10)
    empty = 10 - filled
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
        "uz": {"slim": "Ozg'in", "average": "O'rtacha", "athletic": "Sportcha", "full": "To'liq"},
    }
    body = data.get("body_type")
    if body:
        lines.append(body_map[L].get(body, body))

    # Национальность
    nat_map = {
        "ru": {"uzbek": "Узбек", "russian": "Русский", "korean": "Кореец", "tajik": "Таджик", "kazakh": "Казах", "other": "Другая"},
        "uz": {"uzbek": "O'zbek", "russian": "Rus", "korean": "Koreys", "tajik": "Tojik", "kazakh": "Qozoq", "other": "Boshqa"},
    }
    nat = data.get("nationality")
    if nat:
        nat_label = nat_map[L].get(nat, nat)
        lines.append(f"{'Нац.' if L == 'ru' else 'Millat'}: {nat_label}")

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
        if uni:
            edu_label += f", {uni}"
        lines.append(f"🎓 {edu_label}")

    # Занятость
    occ = data.get("occupation")
    occ_type = data.get("occupation_type")
    if occ and occ not in ("—",):
        occ_type_map = {
            "ru": {"student": "Студент", "housewife": "Домохозяйка", "works": "Работает", "business": "Свой бизнес", "other": "Другое"},
            "uz": {"student": "Talaba", "housewife": "Uy bekasi", "works": "Ishlaydi", "business": "O'z biznesi", "other": "Boshqa"},
        }
        if occ_type in ("student", "housewife"):
            lines.append(f"💼 {occ_type_map[L].get(occ_type, occ)}")
        else:
            lines.append(f"💼 {occ}")

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

    # Дети
    ch = data.get("children_status")
    if ch and ch != "no" and mar and mar != "never_married":
        lines.append("👶 Есть дети" if L == "ru" else "👶 Farzand bor")
    elif ch == "no" and mar and mar != "never_married":
        lines.append("👶 Детей нет" if L == "ru" else "👶 Farzand yo'q")

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
    bar = progress_bar(1, 10)
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
    bar = progress_bar(2, 10)
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
    bar = progress_bar(2, 10)
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
    if not text.isdigit() or not (100 <= int(text) <= 250):
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
    bar = progress_bar(3, 10)
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
        await callback.message.edit_text(t("q21_closed_face_hint", lang))
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q21_photo_upload)
    else:
        await callback.message.edit_text(t("q21_upload", lang))
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
    bar = progress_bar(4, 10)
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
    bar = progress_bar(5, 10)
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
@router.callback_query(F.data.startswith("nat:"), QuestionnaireStates.q12_nationality)
async def q5_nationality(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(nationality=value)
    lang = await _lang(state)
    data = await state.get_data()
    # → 6. Город (кнопки)
    bar = progress_bar(6, 10)
    q_text = t("q6_city", lang, bar=bar)
    full_text = _with_card(data, lang, q_text)
    await callback.message.edit_text(
        full_text,
        reply_markup=add_nav(city_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
    )
    await state.update_data(last_bot_msg=callback.message.message_id)
    await state.set_state(QuestionnaireStates.q6_city)
    await callback.answer()


# ── 6. Город (кнопки) ──
_CITY_NAMES = {
    "ru": {
        "tashkent": "Ташкент", "samarkand": "Самарканд",
        "fergana": "Фергана", "bukhara": "Бухара",
        "namangan": "Наманган", "andijan": "Андижан",
        "nukus": "Нукус", "other": "Другой город",
        "abroad": "За рубежом",
    },
    "uz": {
        "tashkent": "Toshkent", "samarkand": "Samarqand",
        "fergana": "Farg'ona", "bukhara": "Buxoro",
        "namangan": "Namangan", "andijan": "Andijon",
        "nukus": "Nukus", "other": "Boshqa shahar",
        "abroad": "Chet elda",
    },
}


@router.callback_query(F.data.startswith("city:"), QuestionnaireStates.q6_city)
async def q6_city_selected(callback: CallbackQuery, state: FSMContext):
    city_code = callback.data.split(":")[1]
    lang = await _lang(state)
    L = lang if lang in ("ru", "uz") else "ru"
    city_name = _CITY_NAMES[L].get(city_code, city_code)

    await state.update_data(city_code=city_code, city=city_name)

    if city_code == "abroad":
        # «За рубежом» → ввод страны и города текстом
        data = await state.get_data()
        bar = progress_bar(6, 10)
        if lang == "uz":
            q_text = (f"6/10-savol\n{bar}\n\n"
                      f"🌍 Davlat va shaharni kiriting:\n"
                      f"(masalan: Rossiya, Moskva)")
        else:
            q_text = (f"Вопрос 6/10\n{bar}\n\n"
                      f"🌍 Укажите страну и город:\n"
                      f"(например: Россия, Москва)")
        full_text = _with_card(data, lang, q_text)
        await callback.message.edit_text(full_text, reply_markup=back_step_kb(lang))
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q6_district)
    elif city_code == "other":
        # «Другой» → ввод названия города текстом
        data = await state.get_data()
        bar = progress_bar(6, 10)
        if lang == "uz":
            q_text = f"6/10-savol\n{bar}\n\nShahar nomini kiriting:"
        else:
            q_text = f"Вопрос 6/10\n{bar}\n\nВведите название города:"
        full_text = _with_card(data, lang, q_text)
        await callback.message.edit_text(full_text, reply_markup=back_step_kb(lang))
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q6_district)
    else:
        # Обычный город → спросить район
        data = await state.get_data()
        bar = progress_bar(6, 10)
        if lang == "uz":
            q_text = (f"6/10-savol\n{bar}\n\n"
                      f"Tanlandi: {city_name}\n\n"
                      f"Tuman (ixtiyoriy):\n"
                      f"(masalan: Yunusobod, Chilonzor)")
        else:
            q_text = (f"Вопрос 6/10\n{bar}\n\n"
                      f"Выбран: {city_name}\n\n"
                      f"Район (необязательно):\n"
                      f"(например: Юнусабад, Чиланзар)")
        full_text = _with_card(data, lang, q_text)
        await callback.message.edit_text(
            full_text,
            reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
        )
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q6_district)
    await callback.answer()


# ── 6b. Район текстом ──
@router.message(QuestionnaireStates.q6_district)
async def q6_district_entered(message: Message, state: FSMContext):
    await _delete_old(message, state)
    lang = await _lang(state)
    text_input = message.text.strip()
    data = await state.get_data()

    # «Другой» или «За рубежом» → текст = город, без района
    if data.get("city_code") in ("other", "abroad"):
        await state.update_data(city=text_input, district="")
    else:
        await state.update_data(district=text_input)

    data = await state.get_data()
    # → 7. Образование
    bar = progress_bar(7, 10)
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
    bar = progress_bar(7, 10)
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
    bar = progress_bar(8, 10)
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

    if choice in ("works", "business", "other"):
        # Спросить подробнее
        await state.update_data(occupation_type=choice)
        data = await state.get_data()
        bar = progress_bar(8, 10)
        q_text = t("q8_occupation_detail", lang, bar=bar)
        full_text = _with_card(data, lang, q_text)
        await callback.message.edit_text(full_text, reply_markup=back_step_kb(lang))
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q6_occupation)
    else:
        # student / housewife → сохранить и перейти к религиозности
        await state.update_data(occupation_type=choice, occupation=choice)
        await _ask_religion(callback, state, lang)
    await callback.answer()


# Legacy handlers for old work:specify / work:skip callbacks
@router.callback_query(F.data == "work:specify", QuestionnaireStates.q6_work_choice)
async def q8_work_specify(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await state.update_data(occupation_type="works")
    data = await state.get_data()
    bar = progress_bar(8, 10)
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
    bar = progress_bar(9, 10)
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
    bar = progress_bar(10, 10)
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
        # Не был(а) в браке → детей нет → завершение Этапа 1
        await state.update_data(children_status="no")
        await _show_stage1_complete(callback, state)
    else:
        # Разведён/а или Вдовец/Вдова → спросить про детей
        data = await state.get_data()
        card = build_card(data, lang)
        q_text = t("q_children", lang)
        full_text = (card + SEP + q_text) if card else q_text
        await callback.message.edit_text(
            full_text,
            reply_markup=add_nav(children_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
        )
        await state.update_data(last_bot_msg=callback.message.message_id)
        await state.set_state(QuestionnaireStates.q_children)
    await callback.answer()


# ── 10b. Дети (только если разведён/вдовец) ──
@router.callback_query(F.data.startswith("child:"), QuestionnaireStates.q_children)
async def q10_children(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    children_map = {"no": "no", "yes": "yes_with_me"}
    await state.update_data(children_status=children_map.get(value, value))
    # → Завершение Этапа 1
    await _show_stage1_complete(callback, state)
    await callback.answer()


# ══════════════════════════════════════
# Экран завершения Этапа 1
# ══════════════════════════════════════

async def _show_stage1_complete(callback: CallbackQuery, state: FSMContext):
    """Показать экран завершения Этапа 1 — полная карточка + кнопки."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    name = data.get("name", "—")
    age = data.get("age", "?")

    card = build_card(data, lang)
    finish_text = t("stage1_complete", lang, name=name, age=age)
    full_text = (card + SEP + finish_text) if card else finish_text

    kb = anketa_finish_kb(lang)

    try:
        await callback.message.edit_text(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=callback.message.message_id)
    except Exception:
        sent = await callback.message.answer(full_text, reply_markup=kb)
        await state.update_data(last_bot_msg=sent.message_id)

    await state.set_state(QuestionnaireStates.stage1_complete)


# ── Кнопки на экране завершения Этапа 1 ──
@router.callback_query(F.data == "profile:publish", QuestionnaireStates.stage1_complete)
async def stage1_publish(callback: CallbackQuery, state: FSMContext):
    """Отправить на публикацию → переход к тарифу."""
    lang = await _lang(state)
    await callback.message.edit_text(t("tariff", lang), reply_markup=tariff_kb(lang))
    await state.set_state(TariffStates.choose)
    await callback.answer()


@router.callback_query(F.data == "profile:enhance", QuestionnaireStates.stage1_complete)
async def stage1_enhance(callback: CallbackQuery, state: FSMContext):
    """Сделать анкету ярче → переход к тарифу, затем Этап 2."""
    lang = await _lang(state)
    await state.update_data(want_enhance=True)
    await callback.message.edit_text(t("tariff", lang), reply_markup=tariff_kb(lang))
    await state.set_state(TariffStates.choose)
    await callback.answer()


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
                         lambda: add_nav(children_kb(lang).inline_keyboard, lang, "back_step", show_main=False))
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
            lambda l, c: t("q1", l, child=c, bar=progress_bar(1, 10))
        ),
        QuestionnaireStates.q3_height.state: (
            "q2", QuestionnaireStates.q2_birth_year, None,
            lambda l, c: _with_card(data, l, t("q2", l, bar=progress_bar(2, 10)))
        ),
        QuestionnaireStates.q21_photo_type.state: (
            "q2_height", QuestionnaireStates.q3_height, None,
            lambda l, c: _with_card(data, l, t("q2_height", l, bar=progress_bar(2, 10)))
        ),
        QuestionnaireStates.q4_body_type.state: (
            "q3_photo", QuestionnaireStates.q21_photo_type,
            lambda: add_nav(photo_type_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q3_photo", l, bar=progress_bar(3, 10)))
        ),
        QuestionnaireStates.q12_nationality.state: (
            "q4_body_type", QuestionnaireStates.q4_body_type,
            lambda: add_nav(body_type_kb(lang, gender).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q4_body_type", l, bar=progress_bar(4, 10)))
        ),
        QuestionnaireStates.q6_city.state: (
            "q12", QuestionnaireStates.q12_nationality,
            lambda: add_nav(nationality_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q12", l, bar=progress_bar(5, 10)))
        ),
        QuestionnaireStates.q6_district.state: (
            "q6_city", QuestionnaireStates.q6_city,
            lambda: add_nav(city_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q6_city", l, bar=progress_bar(6, 10)))
        ),
        QuestionnaireStates.q5_education.state: (
            "q6_city", QuestionnaireStates.q6_city,
            lambda: add_nav(city_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q6_city", l, bar=progress_bar(6, 10)))
        ),
        QuestionnaireStates.q5_university.state: (
            "q5", QuestionnaireStates.q5_education,
            lambda: add_nav(education_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q5", l, bar=progress_bar(7, 10)))
        ),
        QuestionnaireStates.q6_work_choice.state: (
            "q5", QuestionnaireStates.q5_education,
            lambda: add_nav(education_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q5", l, bar=progress_bar(7, 10)))
        ),
        QuestionnaireStates.q6_occupation.state: (
            "q8_occupation", QuestionnaireStates.q6_work_choice,
            lambda: add_nav(occupation_kb(lang, gender).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q8_occupation", l, bar=progress_bar(8, 10)))
        ),
        QuestionnaireStates.q16_religiosity.state: (
            religion_back[0], religion_back[1], religion_back[2],
            lambda l, c: _with_card(data, l, t(religion_back[0], l, bar=progress_bar(8 if edu != "studying" else 7, 10)))
        ),
        QuestionnaireStates.q_marital_status.state: (
            "q16", QuestionnaireStates.q16_religiosity,
            lambda: add_nav(religiosity_kb(lang).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q16", l, bar=progress_bar(9, 10)))
        ),
        QuestionnaireStates.q_children.state: (
            "q_marital_status", QuestionnaireStates.q_marital_status,
            lambda: add_nav(marital_kb(lang, is_male).inline_keyboard, lang, "back_step", show_main=False),
            lambda l, c: _with_card(data, l, t("q_marital_status", l, bar=progress_bar(10, 10)))
        ),
        QuestionnaireStates.stage1_complete.state: (
            complete_back[0], complete_back[1], complete_back[2],
            lambda l, c: _with_card(data, l, t(complete_back[0], l, bar=progress_bar(10, 10)))
        ),
    }

    entry = back_map.get(current)
    if entry:
        text_key, prev_state, kb_func, text_func = entry
        if text_func:
            msg_text = text_func(lang, child)
        else:
            msg_text = t(text_key, lang, child=child, bar=progress_bar(1, 10))
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
