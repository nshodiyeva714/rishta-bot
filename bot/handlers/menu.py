"""Шаг 2 — Главное меню, Шаг 3 — О платформе, Шаг 4 — Мои заявки."""

import logging
import re
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    User, Profile, ProfileStatus, VipStatus, ContactRequest, Favorite,
    ProfileType, MaritalStatus, ChildrenStatus, PhotoType,
)
from bot.utils.helpers import format_full_anketa
from bot.states import ModeratorContactStates, FeedbackSuggestionStates, EditProfileStates
from bot.texts import t
from bot.keyboards.inline import (
    main_menu_kb, _full_menu_kb, back_kb, back_main_kb, my_profile_kb,
    quest_start_kb, contact_moderator_kb, vip_duration_kb,
    choose_moderator_kb, search_submenu_kb, create_submenu_kb,
    edit_profile_kb, edit_education_kb, edit_religiosity_kb,
    edit_marital_kb, edit_nationality_kb, nav_kb, add_nav,
)
from bot.utils.helpers import age_text, calculate_age
from bot.config import config, get_all_moderator_ids

logger = logging.getLogger(__name__)

router = Router()


async def get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


async def _safe_edit(callback: CallbackQuery, text: str, reply_markup=None):
    """Безопасная отправка — edit или answer если edit не удался."""
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await callback.message.answer(text, reply_markup=reply_markup)


async def show_main_menu(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    await _safe_edit(
        callback,
        t("main_menu", lang),
        reply_markup=main_menu_kb(lang, callback.from_user.id),
    )


@router.callback_query(F.data == "back:menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    await show_main_menu(callback, session)
    await callback.answer()


@router.callback_query(F.data == "menu:main")
async def menu_main_compat(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Совместимость: старая кнопка '🏠 Главное меню' → полное меню."""
    await state.clear()
    await show_main_menu(callback, session)
    await callback.answer()


@router.callback_query(F.data == "menu:about")
async def about_platform(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 3 — О платформе с живой статистикой."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)

    # Живая статистика
    from sqlalchemy import func
    from bot.db.models import Feedback, FeedbackResult
    from datetime import datetime

    total_result = await session.execute(
        select(func.count(Profile.id)).where(Profile.status == ProfileStatus.PUBLISHED)
    )
    total_ankety = total_result.scalar() or 0

    nikoh_result = await session.execute(
        select(func.count(Feedback.id)).where(Feedback.result == FeedbackResult.NIKOH)
    )
    total_nikoh = nikoh_result.scalar() or 0

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    views_result = await session.execute(
        select(func.coalesce(func.sum(Profile.views_count), 0)).where(
            Profile.status == ProfileStatus.PUBLISHED
        )
    )
    total_views = views_result.scalar() or 0

    if lang == "uz":
        text = (
            f"ℹ️ <b>RISHTA HAQIDA</b>\n\n"
            f"O'zbekistondagi birinchi raqamli\n"
            f"sovchilik platformasi 🇺🇿\n\n"
            f"📊 <b>Bugungi holat:</b>\n"
            f"👥 Faol anketalar: <b>{total_ankety}</b>\n"
            f"💍 Nikohlar: <b>{total_nikoh}</b>\n"
            f"👀 Jami ko'rishlar: <b>{total_views}</b>\n\n"
            f"✅ Har bir anketa shaxsan tekshiriladi\n"
            f"✅ To'liq maxfiylik\n"
            f"✅ Kontakt faqat to'lovdan keyin\n"
            f"✅ Moderator yordam beradi\n"
            f"🔒 Foto skrinshotdan himoyalangan\n\n"
            f"📢 @Rishta_uz | 💬 @Rishta_chat"
        )
    else:
        text = (
            f"ℹ️ <b>О RISHTA</b>\n\n"
            f"Первая цифровая платформа\n"
            f"для сватовства в Узбекистане 🇺🇿\n\n"
            f"📊 <b>Сейчас на платформе:</b>\n"
            f"👥 Активных анкет: <b>{total_ankety}</b>\n"
            f"💍 Никохов состоялось: <b>{total_nikoh}</b>\n"
            f"👀 Просмотров всего: <b>{total_views}</b>\n\n"
            f"✅ Каждая анкета проверяется лично\n"
            f"✅ Полная конфиденциальность\n"
            f"✅ Контакт только после оплаты\n"
            f"✅ Модератор сопровождает процесс\n"
            f"🔒 Фото защищены от скриншотов\n\n"
            f"📢 @Rishta_uz | 💬 @Rishta_chat"
        )

    await _safe_edit(callback, text, reply_markup=back_main_kb(lang))
    await callback.answer()


@router.callback_query(F.data == "menu:my")
async def my_applications(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 4 — Мои заявки: статистика + полная анкета + управление."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    user_id = callback.from_user.id

    result = await session.execute(
        select(Profile).where(
            Profile.user_id == user_id,
            Profile.status != ProfileStatus.DELETED,
        ).order_by(Profile.created_at.desc())
    )
    profile = result.scalars().first()

    if not profile:
        if lang == "uz":
            text = (
                "📋 Sizda hozircha anketa yo'q.\n\n"
                "Anketa yaratib qidiruvni boshlang!"
            )
        else:
            text = (
                "📋 У вас пока нет анкеты.\n\n"
                "Создайте анкету чтобы начать поиск!"
            )
        from bot.keyboards.inline import create_submenu_kb
        await _safe_edit(callback, text, reply_markup=create_submenu_kb(lang))
        await callback.answer()
        return

    # ── Статистика ──
    from sqlalchemy import func as sqlfunc

    fav_result = await session.execute(
        select(sqlfunc.count(Favorite.id)).where(Favorite.profile_id == profile.id)
    )
    fav_count = fav_result.scalar() or 0

    req_result = await session.execute(
        select(sqlfunc.count(ContactRequest.id)).where(
            ContactRequest.target_profile_id == profile.id
        )
    )
    req_count = req_result.scalar() or 0

    views = profile.views_count or 0
    display_id = profile.display_id or "—"
    vip_active = profile.vip_status == VipStatus.ACTIVE

    status_map_ru = {
        ProfileStatus.DRAFT: "📝 Черновик",
        ProfileStatus.PENDING: "⏳ На проверке",
        ProfileStatus.PUBLISHED: "✅ Опубликована",
        ProfileStatus.REJECTED: "❌ Отклонена",
        ProfileStatus.PAUSED: "⏸ На паузе",
    }
    status_map_uz = {
        ProfileStatus.DRAFT: "📝 Qoralama",
        ProfileStatus.PENDING: "⏳ Tekshiruvda",
        ProfileStatus.PUBLISHED: "✅ Nashr etilgan",
        ProfileStatus.REJECTED: "❌ Rad etilgan",
        ProfileStatus.PAUSED: "⏸ Pauzada",
    }

    s_map = status_map_uz if lang == "uz" else status_map_ru
    status_label = s_map.get(profile.status, "—")
    vip_label = "⭐ VIP" if vip_active else ("📋 Oddiy" if lang == "uz" else "📋 Обычная")

    if lang == "uz":
        stats = (
            f"🗂 <b>Mening anketam</b>\n\n"
            f"🔖 #{display_id}\n"
            f"Holat: {status_label}  {vip_label}\n\n"
            f"👁 Ko'rishlar: <b>{views}</b>\n"
            f"❤️ Tanlanganlar: <b>{fav_count}</b>\n"
            f"💬 Kontakt so'rovlari: <b>{req_count}</b>"
        )
    else:
        stats = (
            f"🗂 <b>Моя анкета</b>\n\n"
            f"🔖 #{display_id}\n"
            f"Статус: {status_label}  {vip_label}\n\n"
            f"👁 Просмотров: <b>{views}</b>\n"
            f"❤️ В избранном: <b>{fav_count}</b>\n"
            f"💬 Запросов контакта: <b>{req_count}</b>"
        )

    # ── Полная анкета ──
    anketa_text = format_full_anketa(profile, lang=lang)

    full_text = stats + "\n\n━━━━━━━━━━━━━━━\n\n" + anketa_text

    # Telegram ограничение — 4096 символов
    if len(full_text) > 4000:
        full_text = full_text[:3997] + "..."

    is_active = profile.status == ProfileStatus.PUBLISHED and profile.is_active
    await _safe_edit(callback, full_text, reply_markup=my_profile_kb(profile.id, lang, is_active))
    await callback.answer()


@router.callback_query(F.data.startswith("mypause:"))
async def pause_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.PAUSED
        profile.is_active = False
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer("⏸ Анкета поставлена на паузу" if lang == "ru" else "⏸ Anketa pauzaga qo'yildi")
    # Обновляем экран «Мои заявки»
    await my_applications(callback, state, session)


@router.callback_query(F.data.startswith("myactivate:"))
async def activate_profile(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.PUBLISHED
        profile.is_active = True
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer("🟢 Анкета активирована" if lang == "ru" else "🟢 Anketa faollashtirildi")
    await my_applications(callback, state, session)


@router.callback_query(F.data.startswith("myedit:"))
async def edit_profile_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Показать меню редактирования — список полей."""
    await state.clear()
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    lang = await get_lang(session, callback.from_user.id)

    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    await state.update_data(edit_profile_id=profile_id)
    await _safe_edit(callback, t("edit_menu_title", lang), reply_markup=edit_profile_kb(profile_id, lang))
    await callback.answer()


# ─── Обработчики кнопок edit:field:profile_id ───

async def _start_edit_field(callback: CallbackQuery, state: FSMContext, session: AsyncSession,
                            field_state, prompt_key: str):
    """Общая логика: показать промпт и перейти в FSM-состояние."""
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await state.set_state(field_state)
    await _safe_edit(callback, t(prompt_key, lang), reply_markup=back_kb(lang))
    await callback.answer()


async def _finish_edit(message_or_cb, state: FSMContext, session: AsyncSession, lang: str):
    """Вернуться в меню редактирования после сохранения."""
    data = await state.get_data()
    profile_id = data.get("edit_profile_id")
    await state.clear()

    if isinstance(message_or_cb, Message):
        await message_or_cb.answer(
            t("edit_saved", lang) + "\n\n" + t("edit_menu_title", lang),
            reply_markup=edit_profile_kb(profile_id, lang),
        )
    else:
        await _safe_edit(
            message_or_cb,
            t("edit_saved", lang) + "\n\n" + t("edit_menu_title", lang),
            reply_markup=edit_profile_kb(profile_id, lang),
        )


# ── Имя ──
@router.callback_query(F.data.startswith("edit:name:"))
async def edit_name_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.name, "edit_name_prompt")


@router.message(EditProfileStates.name)
async def edit_name_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    name = message.text.strip()[:100] if message.text else None
    if not name:
        await message.answer(t("edit_name_prompt", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.name = name
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Год рождения ──
@router.callback_query(F.data.startswith("edit:birth_year:"))
async def edit_birth_year_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.birth_year, "edit_birth_year_prompt")


@router.message(EditProfileStates.birth_year)
async def edit_birth_year_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if not text.isdigit() or not (1960 <= int(text) <= 2008):
        await message.answer(t("invalid_year", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.birth_year = int(text)
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Рост / Вес ──
@router.callback_query(F.data.startswith("edit:height_weight:"))
async def edit_hw_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.height_weight, "edit_height_weight_prompt")


@router.message(EditProfileStates.height_weight)
async def edit_hw_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    parts = (message.text or "").strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await message.answer(t("edit_height_weight_prompt", lang))
        return
    h, w = int(parts[0]), int(parts[1])
    if not (100 <= h <= 250) or not (30 <= w <= 200):
        await message.answer(t("edit_height_weight_prompt", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.height_cm = h
        profile.weight_kg = w
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Национальность ──
@router.callback_query(F.data.startswith("edit:nationality:"))
async def edit_nationality_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await _safe_edit(callback, t("q12", lang), reply_markup=edit_nationality_kb(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("editnat:"))
async def edit_nationality_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    nat = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == callback.from_user.id:
        profile.nationality = nat
        await session.commit()
    await _finish_edit(callback, state, session, lang)


# ── Город ──
@router.callback_query(F.data.startswith("edit:city:"))
async def edit_city_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.city, "edit_city_prompt")


@router.message(EditProfileStates.city)
async def edit_city_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if not text:
        await message.answer(t("edit_city_prompt", lang))
        return
    parts = [p.strip() for p in text.split(",")]
    city = parts[0][:100]
    district = parts[1][:100] if len(parts) > 1 else ""
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.city = city
        profile.district = district
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Образование ──
@router.callback_query(F.data.startswith("edit:education:"))
async def edit_education_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await _safe_edit(callback, t("q5", lang), reply_markup=edit_education_kb(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("editedu:"))
async def edit_education_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    from bot.db.models import Education
    val = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == callback.from_user.id:
        profile.education = Education(val)
        await session.commit()
    await _finish_edit(callback, state, session, lang)


# ── Работа ──
@router.callback_query(F.data.startswith("edit:occupation:"))
async def edit_occupation_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.occupation, "edit_occupation_prompt")


@router.message(EditProfileStates.occupation)
async def edit_occupation_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    if not text:
        await message.answer(t("edit_occupation_prompt", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.occupation = text[:500]
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Религиозность ──
@router.callback_query(F.data.startswith("edit:religiosity:"))
async def edit_religiosity_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    await _safe_edit(callback, t("q16", lang), reply_markup=edit_religiosity_kb(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("editrel:"))
async def edit_religiosity_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    from bot.db.models import Religiosity
    val = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == callback.from_user.id:
        profile.religiosity = Religiosity(val)
        await session.commit()
    await _finish_edit(callback, state, session, lang)


# ── Семейное положение ──
@router.callback_query(F.data.startswith("edit:marital:"))
async def edit_marital_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    profile_id = int(callback.data.split(":")[-1])
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(edit_profile_id=profile_id, lang=lang)
    profile = await session.get(Profile, profile_id)
    is_male = profile.profile_type == ProfileType.SON if profile else True
    await _safe_edit(callback, t("q_marital_status", lang), reply_markup=edit_marital_kb(lang, is_male))
    await callback.answer()


@router.callback_query(F.data.startswith("editmar:"))
async def edit_marital_save(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    val = callback.data.split(":")[1]
    data = await state.get_data()
    lang = data.get("lang", "ru")
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == callback.from_user.id:
        profile.marital_status = MaritalStatus(val)
        if val == "never_married":
            profile.children_status = ChildrenStatus.NO
        await session.commit()
    await _finish_edit(callback, state, session, lang)


# ── Фото ──
@router.callback_query(F.data.startswith("edit:photo:"))
async def edit_photo_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.photo, "edit_photo_prompt")


@router.message(EditProfileStates.photo)
async def edit_photo_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    if not message.photo:
        await message.answer(t("edit_photo_prompt", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.photo_file_id = message.photo[-1].file_id
        profile.photo_type = PhotoType.REGULAR
        await session.commit()
    await _finish_edit(message, state, session, lang)


# ── Телефон ──
@router.callback_query(F.data.startswith("edit:phone:"))
async def edit_phone_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await _start_edit_field(callback, state, session, EditProfileStates.phone, "edit_phone_prompt")


@router.message(EditProfileStates.phone)
async def edit_phone_save(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = (message.text or "").strip()
    # Нормализуем номер
    digits = re.sub(r"[^\d]", "", text)
    if len(digits) == 9:
        digits = "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        phone = "+" + digits
    else:
        await message.answer(t("invalid_phone", lang))
        return
    profile = await session.get(Profile, data["edit_profile_id"])
    if profile and profile.user_id == message.from_user.id:
        profile.parent_phone = phone
        await session.commit()
    await _finish_edit(message, state, session, lang)


@router.callback_query(F.data.startswith("myvip:"))
async def upgrade_to_vip(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Переход на VIP — показываем выбор срока с ценами."""
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    lang = await get_lang(session, callback.from_user.id)

    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    if profile.vip_status == VipStatus.ACTIVE:
        expires = ""
        if profile.vip_expires_at:
            expires = profile.vip_expires_at.strftime("%d.%m.%Y")
        msg = f"⭐ VIP активен до {expires}" if lang == "ru" else f"⭐ VIP {expires} gacha faol"
        await callback.answer(msg, show_alert=True)
        return

    # Определяем регион для цен
    region = "uzb"
    if profile.residence_status:
        res = profile.residence_status.value
        if res in ("usa", "europe", "citizenship_other", "other_country"):
            region = "usa"
        elif res == "cis":
            region = "sng"

    await state.update_data(vip_profile_id=profile_id, vip_region=region)

    text = (
        f"⭐ <b>VIP анкета</b>\n\n"
        f"🔖 Анкета: {profile.display_id or '—'}\n\n"
        f"Ваша анкета будет:\n"
        f"• Показываться первой в поиске\n"
        f"• Выделена значком ⭐\n"
        f"• Привлекать больше внимания\n\n"
        f"Выберите срок:"
    ) if lang == "ru" else (
        f"⭐ <b>VIP anketa</b>\n\n"
        f"🔖 Anketa: {profile.display_id or '—'}\n\n"
        f"Anketangiz:\n"
        f"• Qidirishda birinchi ko'rinadi\n"
        f"• ⭐ belgisi bilan ajratiladi\n"
        f"• Ko'proq e'tibor tortadi\n\n"
        f"Muddatni tanlang:"
    )

    await _safe_edit(callback, text, reply_markup=vip_duration_kb(lang, region))
    await callback.answer()


@router.callback_query(F.data.startswith("vip_dur:"))
async def vip_duration_selected(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пользователь выбрал срок VIP — направляем к модератору для оплаты."""
    days = int(callback.data.split(":")[1])
    lang = await get_lang(session, callback.from_user.id)
    data = await state.get_data()
    profile_id = data.get("vip_profile_id")
    region = data.get("vip_region", "uzb")

    from bot.config import VIP_PRICES_UZB, VIP_PRICES_USD, VIP_PRICES_SNG, VIP_DURATION_LABELS

    prices = {"uzb": VIP_PRICES_UZB, "sng": VIP_PRICES_SNG, "usa": VIP_PRICES_USD}.get(region, VIP_PRICES_UZB)
    price = prices.get(str(days), 0)

    days_label = VIP_DURATION_LABELS.get(days, {}).get(lang, f"{days}")

    if region == "usa":
        price_str = f"${price // 100}"
    else:
        price_str = f"{price:,} сум".replace(",", " ")

    from bot.config import config
    moderator = config.moderator_tashkent

    profile = await session.get(Profile, profile_id) if profile_id else None
    display_id = profile.display_id if profile else "—"

    text = (
        f"⭐ <b>VIP — {days_label}</b>\n\n"
        f"🔖 Анкета: {display_id}\n"
        f"💰 Стоимость: <b>{price_str}</b>\n\n"
        f"Для оплаты свяжитесь с модератором:\n{moderator}"
    ) if lang == "ru" else (
        f"⭐ <b>VIP — {days_label}</b>\n\n"
        f"🔖 Anketa: {display_id}\n"
        f"💰 Narxi: <b>{price_str}</b>\n\n"
        f"To'lov uchun moderator bilan bog'laning:\n{moderator}"
    )

    await _safe_edit(callback, text, reply_markup=back_main_kb(lang, "menu:my"))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("mydelete:"))
async def delete_confirm(callback: CallbackQuery, session: AsyncSession):
    """Подтверждение удаления анкеты."""
    profile_id = callback.data.split(":")[1]
    lang = await get_lang(session, callback.from_user.id)

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    if lang == "uz":
        text = "⚠️ Anketani o'chirishni tasdiqlaysizmi?\nBu amalni ortga qaytarib bo'lmaydi!"
    else:
        text = "⚠️ Вы уверены что хотите удалить анкету?\nЭто действие нельзя отменить!"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✅ Да, удалить" if lang == "ru" else "✅ Ha, o'chirish",
            callback_data=f"mydelete_yes:{profile_id}",
        )],
        [InlineKeyboardButton(
            text="❌ Отмена" if lang == "ru" else "❌ Bekor qilish",
            callback_data="menu:my",
        )],
    ])
    await _safe_edit(callback, text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("mydelete_yes:"))
async def delete_execute(callback: CallbackQuery, session: AsyncSession):
    """Фактическое удаление анкеты."""
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.DELETED
        profile.is_active = False
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    text = "✅ Анкета удалена." if lang == "ru" else "✅ Anketa o'chirildi."
    await _safe_edit(callback, text, reply_markup=main_menu_kb(lang, callback.from_user.id))
    await callback.answer()


# ── Напоминания (Шаг 18) ──
@router.callback_query(F.data.startswith("remind:"))
async def handle_reminder(callback: CallbackQuery, session: AsyncSession):
    parts = callback.data.split(":")
    action = parts[1]
    profile_id = int(parts[2])
    profile = await session.get(Profile, profile_id)

    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    lang = await get_lang(session, callback.from_user.id)

    if action == "keep":
        await callback.answer("✅ Анкета остаётся активной" if lang == "ru" else "✅ Anketa faol qoladi")
    elif action == "pause":
        profile.status = ProfileStatus.PAUSED
        profile.is_active = False
        await session.commit()
        await callback.answer("⏸ Анкета на паузе" if lang == "ru" else "⏸ Anketa pauzada")
    elif action == "delete":
        profile.status = ProfileStatus.DELETED
        profile.is_active = False
        await session.commit()
        await callback.answer("🗑 Анкета удалена" if lang == "ru" else "🗑 Anketa o'chirildi")
    elif action == "edit":
        await callback.answer("✏️ Свяжитесь с модератором для обновления" if lang == "ru" else "✏️ Yangilash uchun moderator bilan bog'laning")

    await callback.message.edit_text(callback.message.text + f"\n\n→ {action.upper()}")


@router.callback_query(F.data == "menu:moderator")
async def contact_moderator_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Связаться с модератором — выбор из двух."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await _safe_edit(
        callback,
        t("choose_moderator", lang),
        reply_markup=choose_moderator_kb(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:search_sub")
async def search_submenu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подменю: Найти кандидата → невестку / жениха."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await _safe_edit(callback, t("submenu_search", lang), reply_markup=search_submenu_kb(lang))
    await callback.answer()


@router.callback_query(F.data.in_({"menu:search_bride", "menu:search_groom"}))
async def search_redirect(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Поиск невестки / жениха → гостевой поиск (или стандартный если есть анкета)."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)

    result = await session.execute(
        select(Profile).where(
            Profile.user_id == callback.from_user.id,
            Profile.status != ProfileStatus.DELETED,
        ).limit(1)
    )
    my_profile = result.scalar_one_or_none()

    if my_profile:
        from bot.keyboards.inline import search_mode_kb
        await _safe_edit(callback, t("search_title", lang), reply_markup=search_mode_kb(lang))
        await callback.answer()
        return

    # Нет анкеты — запускаем гостевой поиск сразу по выбранному полу
    # menu:search_bride → ищем невестку (daughter)
    # menu:search_groom → ищем жениха (son)
    search_type = ProfileType.DAUGHTER if callback.data == "menu:search_bride" else ProfileType.SON
    await state.update_data(
        search_filters={},
        search_offset=0,
        search_type=search_type.value,
        is_guest=True,
    )
    from bot.handlers.search import _show_search_results
    await _show_search_results(callback, session, state, lang)


@router.callback_query(F.data == "menu:create_sub")
async def create_submenu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Подменю: Создать анкету → сына / дочери."""
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await _safe_edit(callback, t("submenu_create", lang), reply_markup=create_submenu_kb(lang))
    await callback.answer()


@router.callback_query(F.data == "menu:son")
async def start_son_quest(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 5А — Всегда начинаем заполнение анкеты сына."""
    logger.info(f"menu:son от user {callback.from_user.id}")
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(lang=lang, profile_type="son")
    await _safe_edit(
        callback,
        t("quest_son_intro", lang),
        reply_markup=quest_start_kb(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:daughter")
async def start_daughter_quest(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 5Б — Всегда начинаем заполнение анкеты дочери."""
    logger.info(f"menu:daughter от user {callback.from_user.id}")
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(lang=lang, profile_type="daughter")
    await _safe_edit(
        callback,
        t("quest_daughter_intro", lang),
        reply_markup=quest_start_kb(lang),
    )
    await callback.answer()


# ── Написать модератору ──
@router.callback_query(F.data == "mod:write")
async def mod_write_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    prompt = "✍️ Напишите ваше сообщение модератору:" if lang == "ru" else "✍️ Moderatorga xabaringizni yozing:"
    await _safe_edit(callback, prompt, reply_markup=back_main_kb(lang))
    await state.set_state(ModeratorContactStates.awaiting_message)
    await callback.answer()


@router.message(ModeratorContactStates.awaiting_message)
async def mod_write_forward(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    from bot.config import config
    lang = await get_lang(session, message.from_user.id)

    if not config.moderator_chat_id:
        err = "⚠️ Модератор временно недоступен." if lang == "ru" else "⚠️ Moderator vaqtincha mavjud emas."
        await message.answer(err)
        await state.clear()
        return

    # Находим анкету пользователя
    result = await session.execute(
        select(Profile).where(Profile.user_id == message.from_user.id).limit(1)
    )
    profile = result.scalar_one_or_none()
    display_id = profile.display_id if profile else "—"

    header = (
        f"📩 <b>СООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ</b>\n\n"
        f"👤 @{message.from_user.username or '—'} (ID: {message.from_user.id})\n"
        f"🔖 Анкета: {display_id}\n"
        f"━━━━━━━━━━━━━━━\n"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    reply_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ Ответить", callback_data=f"modreply:{message.from_user.id}")],
    ])

    for mod_id in get_all_moderator_ids():
        try:
            await bot.send_message(mod_id, header + (message.text or ""), reply_markup=reply_kb)
            if message.photo:
                await bot.send_photo(mod_id, message.photo[-1].file_id)
            if message.document:
                await bot.send_document(mod_id, message.document.file_id)
            if message.voice:
                await bot.send_voice(mod_id, message.voice.file_id)
            if message.video:
                await bot.send_video(mod_id, message.video.file_id)
        except Exception:
            pass

    ok = "✅ Сообщение отправлено модератору. Ожидайте ответа." if lang == "ru" else "✅ Xabar moderatorga yuborildi. Javobni kuting."
    await message.answer(ok, reply_markup=main_menu_kb(lang, message.from_user.id))
    await state.clear()


# ── Обратная связь / Предложения ──

@router.callback_query(F.data == "menu:feedback")
async def user_feedback_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    lang = await get_lang(session, callback.from_user.id)
    await _safe_edit(
        callback,
        t("user_feedback_prompt", lang),
        reply_markup=back_main_kb(lang),
    )
    await state.set_state(FeedbackSuggestionStates.awaiting_text)
    await callback.answer()


@router.message(FeedbackSuggestionStates.awaiting_text)
async def user_feedback_receive(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    lang = await get_lang(session, message.from_user.id)
    user = message.from_user

    # Находим анкету пользователя
    result = await session.execute(
        select(Profile).where(Profile.user_id == user.id).limit(1)
    )
    profile = result.scalar_one_or_none()
    display_id = profile.display_id if profile else "—"

    mod_text = (
        f"💡 <b>НОВОЕ ПРЕДЛОЖЕНИЕ</b>\n\n"
        f"От: @{user.username or '—'} (ID: {user.id})\n"
        f"🔖 Анкета: {display_id}\n"
        f"Язык: {lang}\n\n"
        f"Текст:\n{message.text}"
    )

    for mod_id in get_all_moderator_ids():
        try:
            await bot.send_message(mod_id, mod_text)
        except Exception:
            pass

    await message.answer(t("user_feedback_thanks", lang), reply_markup=main_menu_kb(lang, user.id))
    await state.clear()


# ── Extend: дополнить анкету / пропустить ──

@router.callback_query(F.data == "extend:skip")
async def extend_skip(callback: CallbackQuery):
    lang = "ru"
    try:
        await callback.message.edit_text(
            "👌 " + ("Xabar olasiz keyinroq" if callback.from_user.language_code == "uz" else "Хорошо, напомним позже")
        )
    except Exception:
        pass
    await callback.answer()


@router.callback_query(F.data.startswith("extend:"))
async def extend_start(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пользователь хочет дополнить анкету — запускаем Этап 2."""
    profile_id_str = callback.data.split(":")[1]
    if not profile_id_str.isdigit():
        await callback.answer()
        return

    profile_id = int(profile_id_str)
    lang = await get_lang(session, callback.from_user.id)

    profile = await session.get(Profile, profile_id)
    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    # Запускаем расширенную анкету
    await state.clear()
    await state.update_data(
        ext_profile_id=profile_id,
        lang=lang,
        profile_type=profile.profile_type.value if profile.profile_type else "son",
    )

    from bot.keyboards.inline import housing_kb
    from bot.states import QuestionnaireStates

    await _safe_edit(
        callback,
        t("ext_housing", lang),
        reply_markup=add_nav(housing_kb(lang).inline_keyboard, lang, "back:menu", show_main=False),
    )
    await state.set_state(QuestionnaireStates.ext_housing)
    await callback.answer()
