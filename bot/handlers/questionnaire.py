"""Шаг 5А/5Б — Анкета (25 вопросов)."""

import re
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import QuestionnaireStates, TariffStates
from bot.texts import t
from bot.keyboards.inline import (
    education_kb, housing_kb, parent_housing_kb, car_kb,
    search_scope_kb, city_kb, diaspora_country_kb,
    region_kb, nationality_kb, family_position_kb,
    religiosity_kb, marital_kb, children_kb,
    skip_kb, photo_type_kb, profile_status_kb,
    location_kb, location_reply_kb, confirm_age_kb, back_kb,
    tariff_kb,
)

router = Router()


# ── Вспомогательная функция для получения языка ──
async def _lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "ru")


async def _child_label(state: FSMContext) -> str:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    ptype = data.get("profile_type", "son")
    return t("son", lang) if ptype == "son" else t("daughter", lang)


# ── Старт анкеты ──
@router.callback_query(F.data == "quest:start")
async def quest_start(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    child = await _child_label(state)
    await callback.message.edit_text(t("q1", lang, child=child))
    await state.set_state(QuestionnaireStates.q1_name)
    await callback.answer()


# ── Q1: Имя ──
@router.message(QuestionnaireStates.q1_name)
async def q1_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q2", lang))
    await state.set_state(QuestionnaireStates.q2_birth_year)


# ── Q2: Год рождения ──
@router.message(QuestionnaireStates.q2_birth_year)
async def q2_birth_year(message: Message, state: FSMContext):
    lang = await _lang(state)
    text = message.text.strip()
    if not text.isdigit() or not (1950 <= int(text) <= 2008):
        await message.answer(t("invalid_year", lang))
        return
    year = int(text)
    age = datetime.now().year - year
    await state.update_data(birth_year=year)
    from bot.utils.helpers import age_text
    await message.answer(
        t("q2_confirm", lang, age=age_text(age)),
        reply_markup=confirm_age_kb(lang),
    )
    await state.set_state(QuestionnaireStates.q2_confirm_age)


@router.callback_query(F.data == "age:confirm", QuestionnaireStates.q2_confirm_age)
async def q2_confirm(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q3", lang))
    await state.set_state(QuestionnaireStates.q3_height)
    await callback.answer()


@router.callback_query(F.data == "age:fix", QuestionnaireStates.q2_confirm_age)
async def q2_fix(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q2", lang))
    await state.set_state(QuestionnaireStates.q2_birth_year)
    await callback.answer()


# ── Q3: Рост ──
@router.message(QuestionnaireStates.q3_height)
async def q3_height(message: Message, state: FSMContext):
    lang = await _lang(state)
    text = message.text.strip()
    if not text.isdigit() or not (100 <= int(text) <= 250):
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(height_cm=int(text))
    await message.answer(t("q4", lang))
    await state.set_state(QuestionnaireStates.q4_weight)


# ── Q4: Вес ──
@router.message(QuestionnaireStates.q4_weight)
async def q4_weight(message: Message, state: FSMContext):
    lang = await _lang(state)
    text = message.text.strip()
    if not text.isdigit() or not (30 <= int(text) <= 200):
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(weight_kg=int(text))
    await message.answer(t("q5", lang), reply_markup=education_kb(lang))
    await state.set_state(QuestionnaireStates.q5_education)


# ── Q5: Образование ──
@router.callback_query(F.data.startswith("edu:"), QuestionnaireStates.q5_education)
async def q5_education(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(education=value)
    lang = await _lang(state)

    if value == "studying":
        await callback.message.edit_text(t("q5_university", lang))
        await state.set_state(QuestionnaireStates.q5_university)
    else:
        await callback.message.edit_text(t("q6", lang))
        await state.set_state(QuestionnaireStates.q6_occupation)
    await callback.answer()


@router.message(QuestionnaireStates.q5_university)
async def q5_university(message: Message, state: FSMContext):
    await state.update_data(university_info=message.text.strip())
    lang = await _lang(state)
    # Если учится — пропускаем Q6 (работа), переходим к Q7
    await message.answer(t("q7", lang), reply_markup=housing_kb(lang))
    await state.set_state(QuestionnaireStates.q7_housing)


# ── Q6: Работа ──
@router.message(QuestionnaireStates.q6_occupation)
async def q6_occupation(message: Message, state: FSMContext):
    await state.update_data(occupation=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q7", lang), reply_markup=housing_kb(lang))
    await state.set_state(QuestionnaireStates.q7_housing)


# ── Q7: Жилищные условия ──
@router.callback_query(F.data.startswith("housing:"), QuestionnaireStates.q7_housing)
async def q7_housing(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(housing=value)
    lang = await _lang(state)

    if value == "with_parents":
        await callback.message.edit_text(t("q7_parent_housing", lang), reply_markup=parent_housing_kb(lang))
        await state.set_state(QuestionnaireStates.q7_parent_housing)
    else:
        await callback.message.edit_text(t("q8", lang), reply_markup=car_kb(lang))
        await state.set_state(QuestionnaireStates.q8_car)
    await callback.answer()


@router.callback_query(F.data.startswith("phousing:"), QuestionnaireStates.q7_parent_housing)
async def q7_parent_housing(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(parent_housing_type=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("q8", lang), reply_markup=car_kb(lang))
    await state.set_state(QuestionnaireStates.q8_car)
    await callback.answer()


# ── Q8: Автомобиль ──
@router.callback_query(F.data.startswith("car:"), QuestionnaireStates.q8_car)
async def q8_car(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(car=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("q9_city_district", lang))
    await state.set_state(QuestionnaireStates.q9_city_district)
    await callback.answer()


# ── Q9: Город и район (merged) ──
@router.message(QuestionnaireStates.q9_city_district)
async def q9_city_district(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q9_address", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q9_address)


# ── Q10: Адрес ──
@router.message(QuestionnaireStates.q9_address)
async def q9_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q10b", lang), reply_markup=search_scope_kb(lang))
    await state.set_state(QuestionnaireStates.q10b_search_scope)


@router.callback_query(F.data == "skip", QuestionnaireStates.q9_address)
async def q9_address_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q10b", lang), reply_markup=search_scope_kb(lang))
    await state.set_state(QuestionnaireStates.q10b_search_scope)
    await callback.answer()


# ── Q10Б: Travel Mode ──
@router.callback_query(F.data.startswith("scope:"), QuestionnaireStates.q10b_search_scope)
async def q10b_scope(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(search_scope=value)
    lang = await _lang(state)

    if value == "uzbekistan_only":
        await callback.message.edit_text(t("q10b_city", lang), reply_markup=city_kb(lang))
        await state.set_state(QuestionnaireStates.q10b_preferred_city)
    elif value == "diaspora":
        await callback.message.edit_text(t("q10b_country", lang), reply_markup=diaspora_country_kb(lang))
        await state.set_state(QuestionnaireStates.q10b_preferred_country)
    else:
        # Везде — переходим к Q11
        await callback.message.edit_text(t("q11", lang), reply_markup=region_kb(lang))
        await state.set_state(QuestionnaireStates.q11_family_region)
    await callback.answer()


@router.callback_query(F.data.startswith("city:"), QuestionnaireStates.q10b_preferred_city)
async def q10b_city(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(preferred_city=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("q10b_district", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q10b_preferred_district)
    await callback.answer()


@router.message(QuestionnaireStates.q10b_preferred_district)
async def q10b_district_text(message: Message, state: FSMContext):
    await state.update_data(preferred_district=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q11", lang), reply_markup=region_kb(lang))
    await state.set_state(QuestionnaireStates.q11_family_region)


@router.callback_query(F.data == "skip", QuestionnaireStates.q10b_preferred_district)
async def q10b_district_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q11", lang), reply_markup=region_kb(lang))
    await state.set_state(QuestionnaireStates.q11_family_region)
    await callback.answer()


@router.callback_query(F.data.startswith("dcountry:"), QuestionnaireStates.q10b_preferred_country)
async def q10b_country(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(preferred_country=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("q11", lang), reply_markup=region_kb(lang))
    await state.set_state(QuestionnaireStates.q11_family_region)
    await callback.answer()


# ── Q11: Регион семьи ──
@router.callback_query(F.data.startswith("city:"), QuestionnaireStates.q11_family_region)
async def q11_region(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(family_region=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("q12", lang), reply_markup=nationality_kb(lang))
    await state.set_state(QuestionnaireStates.q12_nationality)
    await callback.answer()


# ── Q12: Национальность ──
@router.callback_query(F.data.startswith("nat:"), QuestionnaireStates.q12_nationality)
async def q12_nationality(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(nationality=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("q13", lang))
    await state.set_state(QuestionnaireStates.q13_father)
    await callback.answer()


# ── Q13: Отец ──
@router.message(QuestionnaireStates.q13_father)
async def q13_father(message: Message, state: FSMContext):
    await state.update_data(father_occupation=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q14", lang))
    await state.set_state(QuestionnaireStates.q14_mother)


# ── Q14: Мать ──
@router.message(QuestionnaireStates.q14_mother)
async def q14_mother(message: Message, state: FSMContext):
    await state.update_data(mother_occupation=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q15_brothers", lang))
    await state.set_state(QuestionnaireStates.q15_brothers)


# ── Q15: Братья, сёстры, место ──
@router.message(QuestionnaireStates.q15_brothers)
async def q15_brothers(message: Message, state: FSMContext):
    lang = await _lang(state)
    text = message.text.strip()
    if not text.isdigit():
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(brothers_count=int(text))
    await message.answer(t("q15_sisters", lang))
    await state.set_state(QuestionnaireStates.q15_sisters)


@router.message(QuestionnaireStates.q15_sisters)
async def q15_sisters(message: Message, state: FSMContext):
    lang = await _lang(state)
    text = message.text.strip()
    if not text.isdigit():
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(sisters_count=int(text))
    await message.answer(t("q15_position", lang), reply_markup=family_position_kb(lang))
    await state.set_state(QuestionnaireStates.q15_position)


@router.callback_query(F.data.startswith("fpos:"), QuestionnaireStates.q15_position)
async def q15_position(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(family_position=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("q16", lang), reply_markup=religiosity_kb(lang))
    await state.set_state(QuestionnaireStates.q16_religiosity)
    await callback.answer()


# ── Q16: Религиозность ──
@router.callback_query(F.data.startswith("rel:"), QuestionnaireStates.q16_religiosity)
async def q16_religiosity(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(religiosity=value)
    lang = await _lang(state)
    data = await state.get_data()
    is_male = data.get("profile_type") == "son"
    await callback.message.edit_text(t("q17", lang), reply_markup=marital_kb(lang, is_male))
    await state.set_state(QuestionnaireStates.q17_marital)
    await callback.answer()


# ── Q17: Семейное положение ──
@router.callback_query(F.data.startswith("mar:"), QuestionnaireStates.q17_marital)
async def q17_marital(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(marital_status=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("q18", lang), reply_markup=children_kb(lang))
    await state.set_state(QuestionnaireStates.q18_children)
    await callback.answer()


# ── Q18: Дети ──
@router.callback_query(F.data.startswith("child:"), QuestionnaireStates.q18_children)
async def q18_children(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(children_status=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("q19", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q19_health)
    await callback.answer()


# ── Q20: Здоровье ──
@router.message(QuestionnaireStates.q19_health)
async def q19_health(message: Message, state: FSMContext):
    await state.update_data(health_notes=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q20", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q20_character)


@router.callback_query(F.data == "skip", QuestionnaireStates.q19_health)
async def q19_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q20", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q20_character)
    await callback.answer()


# ── Q21: Характер ──
@router.message(QuestionnaireStates.q20_character)
async def q20_character(message: Message, state: FSMContext):
    await state.update_data(character_hobbies=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q20a_intro", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q20a_ideal_family)


@router.callback_query(F.data == "skip", QuestionnaireStates.q20_character)
async def q20_character_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q20a_intro", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q20a_ideal_family)
    await callback.answer()


# ── Q20А: Совместимость (3 вопроса) ──
@router.message(QuestionnaireStates.q20a_ideal_family)
async def q20a_ideal(message: Message, state: FSMContext):
    await state.update_data(ideal_family_life=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q20a_qualities", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q20a_qualities)


@router.callback_query(F.data == "skip", QuestionnaireStates.q20a_ideal_family)
async def q20a_ideal_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q20a_qualities", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q20a_qualities)
    await callback.answer()


@router.message(QuestionnaireStates.q20a_qualities)
async def q20a_qualities(message: Message, state: FSMContext):
    await state.update_data(important_qualities=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q20a_plans", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q20a_plans)


@router.callback_query(F.data == "skip", QuestionnaireStates.q20a_qualities)
async def q20a_qualities_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q20a_plans", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q20a_plans)
    await callback.answer()


@router.message(QuestionnaireStates.q20a_plans)
async def q20a_plans(message: Message, state: FSMContext):
    await state.update_data(five_year_plans=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q21", lang), reply_markup=photo_type_kb(lang))
    await state.set_state(QuestionnaireStates.q21_photo_type)


@router.callback_query(F.data == "skip", QuestionnaireStates.q20a_plans)
async def q20a_plans_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q21", lang), reply_markup=photo_type_kb(lang))
    await state.set_state(QuestionnaireStates.q21_photo_type)
    await callback.answer()


# ── Q21: Фото ──
@router.callback_query(F.data.startswith("photo:"), QuestionnaireStates.q21_photo_type)
async def q21_photo_type(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(photo_type=value)
    lang = await _lang(state)

    if value == "none":
        # Без фото — переходим к контактам
        await callback.message.edit_text(t("q22_phone", lang), reply_markup=skip_kb(lang))
        await state.set_state(QuestionnaireStates.q22_parent_phone)
    elif value == "closed_face":
        await callback.message.edit_text(t("q21_closed_face_hint", lang))
        await state.set_state(QuestionnaireStates.q21_photo_upload)
    else:
        await callback.message.edit_text(t("q21_upload", lang))
        await state.set_state(QuestionnaireStates.q21_photo_upload)
    await callback.answer()


@router.message(QuestionnaireStates.q21_photo_upload, F.photo)
async def q21_photo_upload(message: Message, state: FSMContext):
    photo = message.photo[-1]  # наибольшее разрешение
    await state.update_data(photo_file_id=photo.file_id)
    lang = await _lang(state)
    await message.answer(t("q22_phone", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q22_parent_phone)


@router.message(QuestionnaireStates.q21_photo_upload)
async def q21_photo_upload_invalid(message: Message, state: FSMContext):
    lang = await _lang(state)
    await message.answer(t("q21_upload", lang))


# ── Вспомогательная функция для форматирования телефона ──
def format_phone(text: str) -> str:
    digits = ''.join(filter(str.isdigit, text))
    if len(digits) == 9:
        return f"+998{digits}"
    elif len(digits) == 12 and digits.startswith("998"):
        return f"+{digits}"
    return text


# ── Q23: Контакты ──
@router.message(QuestionnaireStates.q22_parent_phone)
async def q22_phone(message: Message, state: FSMContext):
    lang = await _lang(state)
    phone = format_phone(message.text.strip())
    await state.update_data(parent_phone=phone)
    await message.answer(t("q22_parent_tg", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q22_parent_telegram)


@router.callback_query(F.data == "skip", QuestionnaireStates.q22_parent_phone)
async def q22_phone_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q22_parent_tg", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q22_parent_telegram)
    await callback.answer()


@router.message(QuestionnaireStates.q22_parent_telegram)
async def q22_parent_tg(message: Message, state: FSMContext):
    await state.update_data(parent_telegram=message.text.strip())
    lang = await _lang(state)
    data = await state.get_data()
    ptype = data.get("profile_type", "son")
    child = t("son_nom", lang) if ptype == "son" else t("daughter_nom", lang)
    await message.answer(t("q22_candidate_tg", lang, child=child), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q22_candidate_telegram)


@router.callback_query(F.data == "skip", QuestionnaireStates.q22_parent_telegram)
async def q22_parent_tg_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    ptype = data.get("profile_type", "son")
    child = t("son_nom", lang) if ptype == "son" else t("daughter_nom", lang)
    await callback.message.edit_text(t("q22_candidate_tg", lang, child=child), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q22_candidate_telegram)
    await callback.answer()


@router.message(QuestionnaireStates.q22_candidate_telegram)
async def q22_candidate_tg(message: Message, state: FSMContext):
    await state.update_data(candidate_telegram=message.text.strip())
    lang = await _lang(state)
    # Показываем ReplyKeyboard с кнопкой геолокации + InlineKeyboard с альтернативами
    from aiogram.types import ReplyKeyboardRemove
    await message.answer(t("q22_location", lang), reply_markup=location_reply_kb(lang))
    await state.set_state(QuestionnaireStates.q22_location)


@router.callback_query(F.data == "skip", QuestionnaireStates.q22_candidate_telegram)
async def q22_candidate_tg_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.answer(t("q22_location", lang), reply_markup=location_reply_kb(lang))
    await state.set_state(QuestionnaireStates.q22_location)
    await callback.answer()


# ── Q22: Геолокация ──
@router.message(QuestionnaireStates.q22_location, F.location)
async def q22_loc_geo(message: Message, state: FSMContext):
    from aiogram.types import ReplyKeyboardRemove
    await state.update_data(
        location_lat=message.location.latitude,
        location_lon=message.location.longitude,
    )
    lang = await _lang(state)
    await message.answer("📍", reply_markup=ReplyKeyboardRemove())
    await message.answer(t("q23", lang), reply_markup=profile_status_kb(lang))
    await state.set_state(QuestionnaireStates.q23_status)


@router.message(QuestionnaireStates.q22_location)
async def q22_loc_text(message: Message, state: FSMContext):
    from aiogram.types import ReplyKeyboardRemove
    text = message.text.strip()
    lang = await _lang(state)

    # Кнопка "Пропустить" из ReplyKeyboard
    skip_labels = [t("btn_skip", "ru"), t("btn_skip", "uz")]
    if text in skip_labels:
        await message.answer("👌", reply_markup=ReplyKeyboardRemove())
        await message.answer(t("q23", lang), reply_markup=profile_status_kb(lang))
        await state.set_state(QuestionnaireStates.q23_status)
        return

    await state.update_data(location_link=text)
    await message.answer("✅", reply_markup=ReplyKeyboardRemove())
    await message.answer(t("q23", lang), reply_markup=profile_status_kb(lang))
    await state.set_state(QuestionnaireStates.q23_status)


# ── Q23: Статус ──
@router.callback_query(F.data.startswith("status:"), QuestionnaireStates.q23_status)
async def q23_status(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    is_active = value == "active"
    await state.update_data(is_active=is_active)
    lang = await _lang(state)

    # Переходим к выбору тарифа (Шаг 6)
    await callback.message.edit_text(t("tariff", lang), reply_markup=tariff_kb(lang))
    await state.set_state(TariffStates.choose)
    await callback.answer()
