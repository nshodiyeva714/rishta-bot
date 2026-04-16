"""Анкета — ЭТАП 1: Быстрый старт (10 вопросов).

Порядок: Имя → Год рождения → Рост → Вес → Национальность →
         Город → Образование → Работа → Религиозность →
         Семейное положение+дети → [Фото] → [Телефон] → Тариф
"""

import re
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import QuestionnaireStates, TariffStates
from bot.texts import t
from bot.keyboards.inline import (
    education_kb, nationality_kb, religiosity_kb,
    marital_kb, children_kb, skip_kb, photo_type_kb,
    confirm_age_kb, back_kb, tariff_kb, work_choice_kb,
)

router = Router()


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
    await callback.message.edit_text(t("q1", lang, child=child))
    await state.set_state(QuestionnaireStates.q1_name)
    await callback.answer()


# ── 1. Имя ──
@router.message(QuestionnaireStates.q1_name)
async def q1_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("q2", lang))
    await state.set_state(QuestionnaireStates.q2_birth_year)


# ── 2. Год рождения ──
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
        t("q2_confirm", lang, age=age_text(age, lang)),
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


# ── 3. Рост ──
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


# ── 4. Вес ──
@router.message(QuestionnaireStates.q4_weight)
async def q4_weight(message: Message, state: FSMContext):
    lang = await _lang(state)
    text = message.text.strip()
    if not text.isdigit() or not (30 <= int(text) <= 200):
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(weight_kg=int(text))
    # → 5. Национальность
    await message.answer(t("q12", lang), reply_markup=nationality_kb(lang))
    await state.set_state(QuestionnaireStates.q12_nationality)


# ── 5. Национальность ──
@router.callback_query(F.data.startswith("nat:"), QuestionnaireStates.q12_nationality)
async def q5_nationality(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(nationality=value)
    lang = await _lang(state)
    # → 6. Город
    await callback.message.edit_text(t("q9_city_district", lang))
    await state.set_state(QuestionnaireStates.q9_city_district)
    await callback.answer()


# ── 6. Город и район ──
@router.message(QuestionnaireStates.q9_city_district)
async def q6_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    lang = await _lang(state)
    # → 7. Образование
    await message.answer(t("q5", lang), reply_markup=education_kb(lang))
    await state.set_state(QuestionnaireStates.q5_education)


# ── 7. Образование ──
@router.callback_query(F.data.startswith("edu:"), QuestionnaireStates.q5_education)
async def q7_education(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(education=value)
    lang = await _lang(state)

    if value == "studying":
        await callback.message.edit_text(t("q5_university", lang))
        await state.set_state(QuestionnaireStates.q5_university)
    else:
        # → 8. Работа
        gkey = await _gendered_key(state, "q6_choice")
        await callback.message.edit_text(t(gkey, lang), reply_markup=work_choice_kb(lang))
        await state.set_state(QuestionnaireStates.q6_work_choice)
    await callback.answer()


@router.message(QuestionnaireStates.q5_university)
async def q7_university(message: Message, state: FSMContext):
    await state.update_data(university_info=message.text.strip())
    lang = await _lang(state)
    # Если учится — пропускаем работу → 9. Религиозность
    await message.answer(t("q16", lang), reply_markup=religiosity_kb(lang))
    await state.set_state(QuestionnaireStates.q16_religiosity)


# ── 8. Работа ──
@router.callback_query(F.data == "work:specify", QuestionnaireStates.q6_work_choice)
async def q8_work_specify(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("q6", lang))
    await state.set_state(QuestionnaireStates.q6_occupation)
    await callback.answer()


@router.callback_query(F.data == "work:skip", QuestionnaireStates.q6_work_choice)
async def q8_work_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await state.update_data(occupation="—")
    # → 9. Религиозность
    await callback.message.edit_text(t("q16", lang), reply_markup=religiosity_kb(lang))
    await state.set_state(QuestionnaireStates.q16_religiosity)
    await callback.answer()


@router.message(QuestionnaireStates.q6_occupation)
async def q8_occupation(message: Message, state: FSMContext):
    await state.update_data(occupation=message.text.strip())
    lang = await _lang(state)
    # → 9. Религиозность
    await message.answer(t("q16", lang), reply_markup=religiosity_kb(lang))
    await state.set_state(QuestionnaireStates.q16_religiosity)


# ── 9. Религиозность ──
@router.callback_query(F.data.startswith("rel:"), QuestionnaireStates.q16_religiosity)
async def q9_religiosity(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(religiosity=value)
    lang = await _lang(state)
    data = await state.get_data()
    is_male = data.get("profile_type") == "son"
    # → 10. Семейное положение (3 кнопки)
    await callback.message.edit_text(
        t("q_marital_status", lang),
        reply_markup=marital_kb(lang, is_male),
    )
    await state.set_state(QuestionnaireStates.q_marital_status)
    await callback.answer()


# ── 10. Семейное положение (Шаг 1) ──
@router.callback_query(F.data.startswith("mar:"), QuestionnaireStates.q_marital_status)
async def q10_marital_status(callback: CallbackQuery, state: FSMContext):
    marital = callback.data.split(":")[1]  # never_married / divorced / widowed
    await state.update_data(marital_status=marital)
    lang = await _lang(state)

    if marital == "never_married":
        # Не был(а) в браке → детей нет автоматически → сразу к фото
        await state.update_data(children_status="no")
        await callback.message.edit_text(
            t("q_photo_optional", lang),
            reply_markup=photo_type_kb(lang),
        )
        await state.set_state(QuestionnaireStates.q21_photo_type)
    else:
        # Разведён/а или Вдовец/Вдова → спросить про детей
        await callback.message.edit_text(
            t("q_children", lang),
            reply_markup=children_kb(lang),
        )
        await state.set_state(QuestionnaireStates.q_children)
    await callback.answer()


# ── 10b. Дети (только если разведён/вдовец) ──
@router.callback_query(F.data.startswith("child:"), QuestionnaireStates.q_children)
async def q10_children(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]  # no / yes
    children_map = {"no": "no", "yes": "yes_with_me"}
    await state.update_data(children_status=children_map.get(value, value))
    lang = await _lang(state)
    # → Фото (необязательно)
    await callback.message.edit_text(
        t("q_photo_optional", lang),
        reply_markup=photo_type_kb(lang),
    )
    await state.set_state(QuestionnaireStates.q21_photo_type)
    await callback.answer()


# ── Фото (необязательно) ──
@router.callback_query(F.data.startswith("photo:"), QuestionnaireStates.q21_photo_type)
async def photo_type(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(photo_type=value)
    lang = await _lang(state)

    if value == "none":
        # → Телефон
        await callback.message.edit_text(t("q_phone_optional", lang), reply_markup=skip_kb(lang))
        await state.set_state(QuestionnaireStates.q22_parent_phone)
    elif value == "closed_face":
        await callback.message.edit_text(t("q21_closed_face_hint", lang))
        await state.set_state(QuestionnaireStates.q21_photo_upload)
    else:
        await callback.message.edit_text(t("q21_upload", lang))
        await state.set_state(QuestionnaireStates.q21_photo_upload)
    await callback.answer()


@router.message(QuestionnaireStates.q21_photo_upload, F.photo)
async def photo_upload(message: Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo_file_id=photo.file_id)
    lang = await _lang(state)
    # → Телефон
    await message.answer(t("q_phone_optional", lang), reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.q22_parent_phone)


@router.message(QuestionnaireStates.q21_photo_upload)
async def photo_upload_invalid(message: Message, state: FSMContext):
    lang = await _lang(state)
    await message.answer(t("q21_upload", lang))


# ── Телефон (необязательно) ──
def format_phone(text: str) -> str:
    digits = ''.join(filter(str.isdigit, text))
    if len(digits) == 9:
        return f"+998{digits}"
    elif len(digits) == 12 and digits.startswith("998"):
        return f"+{digits}"
    return text


@router.message(QuestionnaireStates.q22_parent_phone)
async def phone_input(message: Message, state: FSMContext):
    lang = await _lang(state)
    phone = format_phone(message.text.strip())
    await state.update_data(parent_phone=phone)
    # → Тариф
    await message.answer(t("tariff", lang), reply_markup=tariff_kb(lang))
    await state.set_state(TariffStates.choose)


@router.callback_query(F.data == "skip", QuestionnaireStates.q22_parent_phone)
async def phone_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    # → Тариф
    await callback.message.edit_text(t("tariff", lang), reply_markup=tariff_kb(lang))
    await state.set_state(TariffStates.choose)
    await callback.answer()


# ── Кнопка «Назад» ──
@router.callback_query(F.data == "back_step")
async def back_step(callback: CallbackQuery, state: FSMContext):
    """Простой возврат к предыдущему шагу."""
    current = await state.get_state()
    lang = await _lang(state)
    child = await _child_label(state)
    data = await state.get_data()
    is_male = data.get("profile_type") == "son"

    back_map = {
        QuestionnaireStates.q2_birth_year.state: ("q1", QuestionnaireStates.q1_name, None),
        QuestionnaireStates.q3_height.state: ("q2", QuestionnaireStates.q2_birth_year, None),
        QuestionnaireStates.q4_weight.state: ("q3", QuestionnaireStates.q3_height, None),
        QuestionnaireStates.q12_nationality.state: ("q4", QuestionnaireStates.q4_weight, None),
        QuestionnaireStates.q9_city_district.state: ("q12", QuestionnaireStates.q12_nationality, "nationality_kb"),
        QuestionnaireStates.q5_education.state: ("q9_city_district", QuestionnaireStates.q9_city_district, None),
        QuestionnaireStates.q6_work_choice.state: ("q5", QuestionnaireStates.q5_education, "education_kb"),
        QuestionnaireStates.q16_religiosity.state: ("q6_choice", QuestionnaireStates.q6_work_choice, "work_choice_kb"),
        QuestionnaireStates.q_marital_status.state: ("q16", QuestionnaireStates.q16_religiosity, "religiosity_kb"),
        QuestionnaireStates.q_children.state: ("q_marital_status", QuestionnaireStates.q_marital_status, "marital_kb"),
        QuestionnaireStates.q21_photo_type.state: ("q_marital_status", QuestionnaireStates.q_marital_status, "marital_kb"),
        QuestionnaireStates.q22_parent_phone.state: ("q_photo_optional", QuestionnaireStates.q21_photo_type, "photo_type_kb"),
    }

    kb_map = {
        "nationality_kb": lambda: nationality_kb(lang),
        "education_kb": lambda: education_kb(lang),
        "work_choice_kb": lambda: work_choice_kb(lang),
        "religiosity_kb": lambda: religiosity_kb(lang),
        "marital_kb": lambda: marital_kb(lang, is_male),
        "photo_type_kb": lambda: photo_type_kb(lang),
    }

    entry = back_map.get(current)
    if entry:
        text_key, prev_state, kb_name = entry
        msg_text = t(text_key, lang, child=child)
        kb = kb_map[kb_name]() if kb_name else None
        if kb:
            await callback.message.edit_text(msg_text, reply_markup=kb)
        else:
            await callback.message.edit_text(msg_text)
        await state.set_state(prev_state)
    await callback.answer("🔙")
