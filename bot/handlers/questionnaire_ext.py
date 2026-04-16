"""Анкета — ЭТАП 2: Расширенный профиль.

Порядок: Жильё → Машина → Адрес → Геолокация →
         Отец → Мать → Братья → Сёстры → Место в семье →
         Здоровье → Характер → Идеальная семья →
         Качества → Планы → Telegram родителей →
         Telegram кандидата → Статус → Подтверждение
"""

import logging

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import QuestionnaireStates
from bot.texts import t
from bot.keyboards.inline import (
    housing_kb, parent_housing_kb, car_kb, skip_kb,
    family_position_kb, back_kb, main_menu_kb,
    add_nav, nav_kb,
)
from bot.db.models import (
    Profile, ProfileStatus, User,
    Housing, ParentHousing, CarStatus, FamilyPosition,
)

logger = logging.getLogger(__name__)

router = Router()


async def _get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


async def _get_profile(session: AsyncSession, profile_id: int, user_id: int):
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == user_id:
        return profile
    return None


async def _lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "ru")


# ══════════════════════════════════════
# ЭТАП 2 — Расширенный профиль
# ══════════════════════════════════════

# ── 1. Жильё ──
@router.callback_query(F.data.startswith("housing:"), QuestionnaireStates.ext_housing)
async def ext_housing(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(housing=value)
    lang = await _lang(state)

    if value == "with_parents":
        await callback.message.edit_text(
            t("ext_housing_parent", lang),
            reply_markup=add_nav(parent_housing_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
        )
        await state.set_state(QuestionnaireStates.ext_housing_parent)
    else:
        await callback.message.edit_text(
            t("ext_car", lang),
            reply_markup=add_nav(car_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
        )
        await state.set_state(QuestionnaireStates.ext_car)
    await callback.answer()


# ── 1b. Тип жилья родителей ──
@router.callback_query(F.data.startswith("phousing:"), QuestionnaireStates.ext_housing_parent)
async def ext_housing_parent(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(parent_housing_type=value)
    lang = await _lang(state)
    await callback.message.edit_text(
        t("ext_car", lang),
        reply_markup=add_nav(car_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_car)
    await callback.answer()


# ── 2. Машина ──
@router.callback_query(F.data.startswith("car:"), QuestionnaireStates.ext_car)
async def ext_car(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(car=value)
    lang = await _lang(state)
    await callback.message.edit_text(t("ext_address", lang), reply_markup=back_kb(lang))
    await state.set_state(QuestionnaireStates.ext_address)
    await callback.answer()


# ── 3. Адрес ──
@router.message(QuestionnaireStates.ext_address)
async def ext_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("ext_family_region", lang), reply_markup=back_kb(lang))
    await state.set_state(QuestionnaireStates.ext_family_region)


# ── 4. Регион семьи ──
@router.message(QuestionnaireStates.ext_family_region)
async def ext_family_region(message: Message, state: FSMContext):
    await state.update_data(family_region=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("ext_father", lang), reply_markup=back_kb(lang))
    await state.set_state(QuestionnaireStates.ext_father)


# ── 5. Отец ──
@router.message(QuestionnaireStates.ext_father)
async def ext_father(message: Message, state: FSMContext):
    await state.update_data(father_occupation=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("ext_mother", lang), reply_markup=back_kb(lang))
    await state.set_state(QuestionnaireStates.ext_mother)


# ── 6. Мать ──
@router.message(QuestionnaireStates.ext_mother)
async def ext_mother(message: Message, state: FSMContext):
    await state.update_data(mother_occupation=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("ext_brothers", lang), reply_markup=back_kb(lang))
    await state.set_state(QuestionnaireStates.ext_brothers)


# ── 7. Братья ──
@router.message(QuestionnaireStates.ext_brothers)
async def ext_brothers(message: Message, state: FSMContext):
    lang = await _lang(state)
    text = message.text.strip()
    if not text.isdigit() or int(text) > 20:
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(brothers_count=int(text))
    await message.answer(t("ext_sisters", lang), reply_markup=back_kb(lang))
    await state.set_state(QuestionnaireStates.ext_sisters)


# ── 8. Сёстры ──
@router.message(QuestionnaireStates.ext_sisters)
async def ext_sisters(message: Message, state: FSMContext):
    lang = await _lang(state)
    text = message.text.strip()
    if not text.isdigit() or int(text) > 20:
        await message.answer(t("invalid_number", lang))
        return
    await state.update_data(sisters_count=int(text))
    await message.answer(
        t("ext_position", lang),
        reply_markup=add_nav(family_position_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_position)


# ── 9. Место в семье ──
@router.callback_query(F.data.startswith("fpos:"), QuestionnaireStates.ext_position)
async def ext_position(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":")[1]
    await state.update_data(family_position=value)
    lang = await _lang(state)
    await callback.message.edit_text(
        t("ext_health", lang),
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_health)
    await callback.answer()


# ── 10. Здоровье ──
@router.message(QuestionnaireStates.ext_health)
async def ext_health(message: Message, state: FSMContext):
    await state.update_data(health_notes=message.text.strip())
    lang = await _lang(state)
    await message.answer(t("ext_character", lang), reply_markup=back_kb(lang))
    await state.set_state(QuestionnaireStates.ext_character)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_health)
async def ext_health_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(t("ext_character", lang), reply_markup=back_kb(lang))
    await state.set_state(QuestionnaireStates.ext_character)
    await callback.answer()


# ── 11. Характер ──
@router.message(QuestionnaireStates.ext_character)
async def ext_character(message: Message, state: FSMContext):
    await state.update_data(character_hobbies=message.text.strip())
    lang = await _lang(state)
    await message.answer(
        t("ext_ideal_family", lang),
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_ideal_family)


# ── 12. Идеальная семья ──
@router.message(QuestionnaireStates.ext_ideal_family)
async def ext_ideal_family(message: Message, state: FSMContext):
    await state.update_data(ideal_family_life=message.text.strip())
    lang = await _lang(state)
    await message.answer(
        t("ext_qualities", lang),
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_qualities)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_ideal_family)
async def ext_ideal_family_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(
        t("ext_qualities", lang),
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_qualities)
    await callback.answer()


# ── 13. Качества ──
@router.message(QuestionnaireStates.ext_qualities)
async def ext_qualities(message: Message, state: FSMContext):
    await state.update_data(important_qualities=message.text.strip())
    lang = await _lang(state)
    await message.answer(
        t("ext_plans", lang),
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_plans)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_qualities)
async def ext_qualities_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(
        t("ext_plans", lang),
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_plans)
    await callback.answer()


# ── 14. Планы ──
@router.message(QuestionnaireStates.ext_plans)
async def ext_plans(message: Message, state: FSMContext):
    await state.update_data(five_year_plans=message.text.strip())
    lang = await _lang(state)
    await message.answer(
        t("ext_parent_telegram", lang),
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_parent_telegram)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_plans)
async def ext_plans_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await callback.message.edit_text(
        t("ext_parent_telegram", lang),
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_parent_telegram)
    await callback.answer()


# ── 15. Telegram родителей ──
@router.message(QuestionnaireStates.ext_parent_telegram)
async def ext_parent_telegram(message: Message, state: FSMContext):
    tg = message.text.strip()
    if not tg.startswith("@"):
        tg = f"@{tg}"
    await state.update_data(parent_telegram=tg)
    lang = await _lang(state)
    data = await state.get_data()
    ptype = data.get("profile_type", "son")
    child = t("son", lang) if ptype == "son" else t("daughter", lang)
    await message.answer(
        t("ext_candidate_telegram", lang, child=child),
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_candidate_telegram)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_parent_telegram)
async def ext_parent_tg_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    ptype = data.get("profile_type", "son")
    child = t("son", lang) if ptype == "son" else t("daughter", lang)
    await callback.message.edit_text(
        t("ext_candidate_telegram", lang, child=child),
        reply_markup=add_nav(skip_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_candidate_telegram)
    await callback.answer()


# ── 16. Telegram кандидата ──
@router.message(QuestionnaireStates.ext_candidate_telegram)
async def ext_candidate_telegram(message: Message, state: FSMContext):
    tg = message.text.strip()
    if not tg.startswith("@"):
        tg = f"@{tg}"
    await state.update_data(candidate_telegram=tg)
    lang = await _lang(state)
    await _show_ext_confirm(message, state, lang)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_candidate_telegram)
async def ext_candidate_tg_skip(callback: CallbackQuery, state: FSMContext):
    lang = await _lang(state)
    await _show_ext_confirm(callback.message, state, lang, edit=True)
    await callback.answer()


# ── Подтверждение расширенного профиля ──
async def _show_ext_confirm(message, state: FSMContext, lang: str, edit: bool = False):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Сохранить" if lang == "ru" else "✅ Saqlash",
            callback_data="ext_confirm:save",
        )],
        [InlineKeyboardButton(
            text="❌ Отменить" if lang == "ru" else "❌ Bekor qilish",
            callback_data="ext_confirm:cancel",
        )],
        *nav_kb(lang, "back:menu"),
    ])
    text = t("ext_confirm", lang)
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)
    await state.set_state(QuestionnaireStates.ext_confirm)


@router.callback_query(F.data == "ext_confirm:save", QuestionnaireStates.ext_confirm)
async def ext_confirm_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession, bot: Bot):
    """Сохраняем расширенные данные в профиль."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile_id = data.get("ext_profile_id")

    if not profile_id:
        await callback.answer("⛔")
        await state.clear()
        return

    profile = await _get_profile(session, profile_id, callback.from_user.id)
    if not profile:
        await callback.answer("⛔")
        await state.clear()
        return

    # Безопасное преобразование enum
    def safe_enum(enum_cls, val):
        if val is None:
            return None
        try:
            return enum_cls(val)
        except (ValueError, KeyError):
            return None

    # Обновляем только заполненные поля
    if data.get("housing"):
        profile.housing = safe_enum(Housing, data["housing"])
    if data.get("parent_housing_type"):
        profile.parent_housing_type = safe_enum(ParentHousing, data["parent_housing_type"])
    if data.get("car"):
        profile.car = safe_enum(CarStatus, data["car"])
    if data.get("address"):
        profile.address = data["address"]
    if data.get("family_region"):
        profile.family_region = data["family_region"]
    if data.get("father_occupation"):
        profile.father_occupation = data["father_occupation"]
    if data.get("mother_occupation"):
        profile.mother_occupation = data["mother_occupation"]
    if data.get("brothers_count") is not None:
        profile.brothers_count = data["brothers_count"]
    if data.get("sisters_count") is not None:
        profile.sisters_count = data["sisters_count"]
    if data.get("family_position"):
        profile.family_position = safe_enum(FamilyPosition, data["family_position"])
    if data.get("health_notes"):
        profile.health_notes = data["health_notes"]
    if data.get("character_hobbies"):
        profile.character_hobbies = data["character_hobbies"]
    if data.get("ideal_family_life"):
        profile.ideal_family_life = data["ideal_family_life"]
    if data.get("important_qualities"):
        profile.important_qualities = data["important_qualities"]
    if data.get("five_year_plans"):
        profile.five_year_plans = data["five_year_plans"]
    if data.get("parent_telegram"):
        profile.parent_telegram = data["parent_telegram"]
    if data.get("candidate_telegram"):
        profile.candidate_telegram = data["candidate_telegram"]

    await session.commit()

    display_id = profile.display_id or "—"

    # Уведомляем модераторов об обновлении
    from bot.config import get_all_moderator_ids
    from bot.utils.helpers import format_full_anketa
    from bot.keyboards.inline import mod_review_kb

    mod_text = (
        f"📝 <b>АНКЕТА ДОПОЛНЕНА</b>\n"
        f"🔖 {display_id}\n\n"
    ) + format_full_anketa(profile, lang="ru")

    for mod_id in get_all_moderator_ids():
        try:
            await bot.send_message(mod_id, mod_text, reply_markup=mod_review_kb(profile.id))
        except Exception:
            pass

    # Успех
    if lang == "uz":
        text = (
            f"✅ <b>Anketa to'ldirildi!</b>\n\n"
            f"🔖 {display_id}\n\n"
            f"Qo'shimcha ma'lumotlar saqlandi.\n"
            f"Anketangiz endi to'liqroq ko'rinadi ⭐\n\n"
            f"Ko'proq oilalar sizni ko'radi! 👀"
        )
    else:
        text = (
            f"✅ <b>Анкета дополнена!</b>\n\n"
            f"🔖 {display_id}\n\n"
            f"Дополнительные данные сохранены.\n"
            f"Ваша анкета теперь полнее ⭐\n\n"
            f"Больше семей увидят вас! 👀"
        )

    await callback.message.edit_text(text, reply_markup=main_menu_kb(lang, callback.from_user.id))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "ext_confirm:cancel", QuestionnaireStates.ext_confirm)
async def ext_confirm_cancel(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = await _get_lang(session, callback.from_user.id)
    await state.clear()
    if lang == "uz":
        text = "❌ Bekor qilindi. Ma'lumotlar saqlanmadi."
    else:
        text = "❌ Отменено. Данные не сохранены."
    await callback.message.edit_text(text, reply_markup=main_menu_kb(lang, callback.from_user.id))
    await callback.answer()
