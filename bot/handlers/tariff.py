"""Шаг 6 — Тариф, Шаг 7 — Требования, Шаг 8 — Подтверждение анкеты."""

from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
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
    req_nationality_kb,
    req_religiosity_kb, req_marital_kb, req_children_kb,
    req_car_kb, req_housing_kb, req_job_kb,
    skip_kb, confirm_profile_kb, main_menu_kb,
    mod_review_kb,
)
from bot.utils.helpers import generate_display_id, age_text, calculate_age
from bot.config import config

router = Router()


async def _lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "ru")


# ── Шаг 6: Тариф ──
@router.callback_query(F.data.startswith("tariff:"), TariffStates.choose)
async def choose_tariff(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    is_vip = value == "vip"
    await state.update_data(is_vip=is_vip)
    lang = await _lang(state)

    # Переходим к требованиям (Шаг 7)
    await callback.message.edit_text(t("req_intro", lang) + "\n\n" + t("req_age", lang), reply_markup=req_age_kb(lang))
    await state.set_state(RequirementStates.age)
    await callback.answer()


# ── Шаг 7: Требования ──
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
    await callback.message.edit_text(t("req_education", lang), reply_markup=req_education_kb(lang))
    await state.set_state(RequirementStates.education)
    await callback.answer()


@router.callback_query(F.data.startswith("reqedu:"), RequirementStates.education)
async def req_education(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_education=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("req_residence", lang), reply_markup=req_residence_simple_kb(lang))
    await state.set_state(RequirementStates.residence)
    await callback.answer()


@router.callback_query(F.data.startswith("rres_"), RequirementStates.residence)
async def req_residence(callback: CallbackQuery, state: FSMContext):
    value = callback.data
    lang = await _lang(state)

    if value == "rres_uzb":
        # Show regions keyboard
        await callback.message.edit_text(t("req_residence_region", lang), reply_markup=req_residence_regions_kb(lang))
        await state.set_state(RequirementStates.residence_city)
        await callback.answer()
        return
    elif value == "rres_other":
        await state.update_data(req_residence="other")
    else:  # rres_skip
        await state.update_data(req_residence="")

    await callback.message.edit_text(t("req_nationality", lang), reply_markup=req_nationality_kb(lang))
    await state.set_state(RequirementStates.nationality)
    await callback.answer()


@router.callback_query(F.data.startswith("rregion_"), RequirementStates.residence_city)
async def req_residence_region(callback: CallbackQuery, state: FSMContext):
    region = callback.data.replace("rregion_", "")
    if region == "any":
        await state.update_data(req_residence="uzbekistan")
    else:
        await state.update_data(req_residence=region)
    lang = await _lang(state)
    await callback.message.edit_text(t("req_nationality", lang), reply_markup=req_nationality_kb(lang))
    await state.set_state(RequirementStates.nationality)
    await callback.answer()


@router.callback_query(F.data.startswith("reqnat:"), RequirementStates.nationality)
async def req_nationality(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_nationality=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("req_religiosity", lang), reply_markup=req_religiosity_kb(lang))
    await state.set_state(RequirementStates.religiosity)
    await callback.answer()


@router.callback_query(F.data.startswith("reqrel:"), RequirementStates.religiosity)
async def req_religiosity(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_religiosity=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("req_marital", lang), reply_markup=req_marital_kb(lang))
    await state.set_state(RequirementStates.marital_status)
    await callback.answer()


@router.callback_query(F.data.startswith("reqmar:"), RequirementStates.marital_status)
async def req_marital(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_marital_status=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("req_children", lang), reply_markup=req_children_kb(lang))
    await state.set_state(RequirementStates.children)
    await callback.answer()


@router.callback_query(F.data.startswith("reqchild:"), RequirementStates.children)
async def req_children(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_children=value)
    lang = await _lang(state)
    data = await state.get_data()

    # Для анкеты дочери — дополнительные вопросы
    if data.get("profile_type") == "daughter":
        await callback.message.edit_text(t("req_car", lang), reply_markup=req_car_kb(lang))
        await state.set_state(RequirementStates.car_required)
    else:
        await callback.message.edit_text(t("req_other", lang), reply_markup=skip_kb(lang))
        await state.set_state(RequirementStates.other_wishes)
    await callback.answer()


# Дополнительные требования для дочери
@router.callback_query(F.data.startswith("reqcar:"), RequirementStates.car_required)
async def req_car(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_car=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("req_housing", lang), reply_markup=req_housing_kb(lang))
    await state.set_state(RequirementStates.housing_required)
    await callback.answer()


@router.callback_query(F.data.startswith("reqhouse:"), RequirementStates.housing_required)
async def req_housing(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_housing=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("req_job", lang), reply_markup=req_job_kb(lang))
    await state.set_state(RequirementStates.job_required)
    await callback.answer()


@router.callback_query(F.data.startswith("reqjob:"), RequirementStates.job_required)
async def req_job(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(req_job=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("req_other", lang), reply_markup=skip_kb(lang))
    await state.set_state(RequirementStates.other_wishes)
    await callback.answer()


@router.message(RequirementStates.other_wishes)
async def req_other_wishes(message: Message, state: FSMContext):
    await state.update_data(req_other=message.text.strip())
    lang = await _lang(state)
    confirm_text = "✅ Подтвердить анкету?" if lang == "ru" else "✅ Anketani tasdiqlaysizmi?"
    await message.answer(confirm_text, reply_markup=confirm_profile_kb(lang))
    await state.set_state(RequirementStates.confirm)


@router.callback_query(F.data == "skip", RequirementStates.other_wishes)
async def req_other_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    confirm_text = "✅ Подтвердить анкету?" if lang == "ru" else "✅ Anketani tasdiqlaysizmi?"
    await callback.message.edit_text(confirm_text, reply_markup=confirm_profile_kb(lang))
    await state.set_state(RequirementStates.confirm)
    await callback.answer()


# ── Шаг 8: Подтверждение — создаём анкету в БД ──
@router.callback_query(F.data == "profile:confirm", RequirementStates.confirm)
async def confirm_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    ptype = ProfileType(data.get("profile_type", "son"))

    display_id = await generate_display_id(session, ptype)

    # Безопасное преобразование enum-значений
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
        name=data.get("name"),
        birth_year=data.get("birth_year"),
        height_cm=data.get("height_cm"),
        weight_kg=data.get("weight_kg"),
        education=safe_enum(Education, data.get("education")),
        university_info=data.get("university_info"),
        occupation=data.get("occupation"),
        housing=safe_enum(Housing, data.get("housing")),
        parent_housing_type=safe_enum(ParentHousing, data.get("parent_housing_type")),
        car=safe_enum(CarStatus, data.get("car")),
        city=data.get("city"),
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

    # VIP
    if data.get("is_vip"):
        profile.vip_status = VipStatus.ACTIVE
        profile.vip_expires_at = datetime.now() + timedelta(days=30)

    session.add(profile)
    await session.flush()

    # Создаём требования
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

    # Отправляем пользователю подтверждение
    await callback.message.edit_text(t("profile_submitted", lang, display_id=display_id))

    # Шаг 9 — уведомляем модератора
    if config.moderator_chat_id:
        age = calculate_age(profile.birth_year) if profile.birth_year else "?"
        icon = "👧" if ptype == ProfileType.DAUGHTER else "👦"
        vip = "⭐ Да" if profile.vip_status == VipStatus.ACTIVE else "Нет"
        photo_status = "есть" if profile.photo_file_id else "нет"
        if profile.photo_type and profile.photo_type != PhotoType.NONE and profile.photo_type != PhotoType.REGULAR:
            photo_status += f" ({profile.photo_type.value})"

        mod_text = t("mod_new_profile", "ru",
            display_id=display_id,
            icon=icon,
            name=profile.name or "—",
            age=age_text(age) if isinstance(age, int) else age,
            city=profile.city or "—",
            district=profile.district or "—",
            phone=profile.parent_phone or "—",
            vip=vip,
            photo=photo_status,
        )

        try:
            msg = await bot.send_message(
                config.moderator_chat_id,
                mod_text,
                reply_markup=mod_review_kb(profile.id),
            )
            # Если есть фото — отправляем его модератору
            if profile.photo_file_id:
                await bot.send_photo(config.moderator_chat_id, profile.photo_file_id)
        except Exception:
            pass  # Модератор недоступен — не блокируем пользователя

    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "profile:cancel", RequirementStates.confirm)
async def cancel_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = (await state.get_data()).get("lang", "ru")
    await state.clear()
    await callback.message.edit_text(t("main_menu", lang), reply_markup=main_menu_kb(lang))
    await callback.answer()
