"""Шаг 2 — Главное меню, Шаг 3 — О платформе, Шаг 4 — Мои заявки."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, Profile, ProfileStatus, VipStatus, ContactRequest, Favorite, ProfileType
from bot.texts import t
from bot.keyboards.inline import main_menu_kb, back_kb, my_profile_kb, quest_start_kb
from bot.utils.helpers import age_text, calculate_age

router = Router()


async def get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


async def show_main_menu(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    await callback.message.edit_text(
        t("main_menu", lang),
        reply_markup=main_menu_kb(lang),
    )


@router.callback_query(F.data == "back:menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    await state.clear()
    await show_main_menu(callback, session)
    await callback.answer()


@router.callback_query(F.data == "menu:about")
async def about_platform(callback: CallbackQuery, session: AsyncSession):
    """Шаг 3 — О платформе."""
    lang = await get_lang(session, callback.from_user.id)
    await callback.message.edit_text(t("about", lang), reply_markup=back_kb(lang))
    await callback.answer()


@router.callback_query(F.data == "menu:my")
async def my_applications(callback: CallbackQuery, session: AsyncSession):
    """Шаг 4 — Мои заявки."""
    lang = await get_lang(session, callback.from_user.id)
    user_id = callback.from_user.id

    result = await session.execute(
        select(Profile).where(
            Profile.user_id == user_id,
            Profile.status != ProfileStatus.DELETED,
        )
    )
    profiles = result.scalars().all()

    if not profiles:
        await callback.message.edit_text(t("no_profiles", lang), reply_markup=back_kb(lang))
        await callback.answer()
        return

    for profile in profiles:
        # Считаем запросы и избранное
        req_result = await session.execute(
            select(ContactRequest).where(ContactRequest.target_profile_id == profile.id)
        )
        requests = req_result.scalars().all()

        fav_result = await session.execute(
            select(Favorite).where(Favorite.user_id == user_id)
        )
        fav_count = len(fav_result.scalars().all())

        vip_label = "⭐ VIP" if profile.vip_status == VipStatus.ACTIVE else "📋 Обычная"
        status_map = {
            ProfileStatus.DRAFT: "📝 Черновик",
            ProfileStatus.PENDING: "⏳ На проверке",
            ProfileStatus.PUBLISHED: "✅ Опубликована",
            ProfileStatus.REJECTED: "❌ Отклонена",
            ProfileStatus.PAUSED: "⏸ На паузе",
        }
        status_label = status_map.get(profile.status, str(profile.status))

        text = (
            f"📋 <b>МОИ ЗАЯВКИ</b>\n\n"
            f"🔖 Анкета: {profile.display_id or '—'}\n"
            f"Статус: {status_label}\n"
            f"Тип: {vip_label}\n"
            f"👁 Просмотров: {profile.views_count or 0}\n"
            f"💬 Запросов: {len(requests)}\n\n"
            f"❤️ Избранное ({fav_count} анкет)"
        )

        # Добавляем список запросов
        if requests:
            text += "\n\n📨 Мои запросы:"
            for req in requests[:5]:
                target = await session.get(Profile, req.target_profile_id)
                status_icons = {
                    "pending": "⏳ Ожидание",
                    "talking": "⏳ Общаемся",
                    "contact_given": "✅ Контакт получен",
                    "rejected": "❌ Не подошли",
                }
                icon = status_icons.get(req.status.value, req.status.value)
                text += f"\n• {target.display_id if target else '—'} — {icon}"

        is_active = profile.status == ProfileStatus.PUBLISHED and profile.is_active
        await callback.message.edit_text(
            text,
            reply_markup=my_profile_kb(profile.id, lang, is_active),
        )

    await callback.answer()


@router.callback_query(F.data.startswith("mypause:"))
async def pause_profile(callback: CallbackQuery, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.PAUSED
        profile.is_active = False
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer("⏸ Анкета поставлена на паузу" if lang == "ru" else "⏸ Anketa pauzaga qo'yildi")
    await show_main_menu(callback, session)


@router.callback_query(F.data.startswith("myactivate:"))
async def activate_profile(callback: CallbackQuery, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.PUBLISHED
        profile.is_active = True
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer("🟢 Анкета активирована" if lang == "ru" else "🟢 Anketa faollashtirildi")
    await show_main_menu(callback, session)


@router.callback_query(F.data.startswith("myedit:"))
async def edit_profile(callback: CallbackQuery, session: AsyncSession):
    """Редактирование анкеты — пока через модератора."""
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer(
        "✏️ Свяжитесь с модератором для редактирования" if lang == "ru"
        else "✏️ Tahrirlash uchun moderator bilan bog'laning"
    )


@router.callback_query(F.data.startswith("myvip:"))
async def upgrade_to_vip(callback: CallbackQuery, session: AsyncSession):
    """Переход на VIP — оплата через модератора."""
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    lang = await get_lang(session, callback.from_user.id)

    if not profile or profile.user_id != callback.from_user.id:
        await callback.answer("⛔")
        return

    if profile.vip_status == VipStatus.ACTIVE:
        await callback.answer("⭐ VIP уже активен" if lang == "ru" else "⭐ VIP allaqachon faol")
        return

    from bot.config import config
    moderator = config.moderator_tashkent
    text = (
        f"⭐ <b>Перейти на VIP</b>\n\n"
        f"🔖 Анкета: {profile.display_id or '—'}\n"
        f"💰 Стоимость: 100,000 сум/мес\n\n"
        f"Для оплаты VIP свяжитесь с модератором:\n{moderator}"
    ) if lang == "ru" else (
        f"⭐ <b>VIPga o'tish</b>\n\n"
        f"🔖 Anketa: {profile.display_id or '—'}\n"
        f"💰 Narxi: 100,000 so'm/oy\n\n"
        f"VIP to'lovi uchun moderator bilan bog'laning:\n{moderator}"
    )

    await callback.message.answer(text)
    await callback.answer()


@router.callback_query(F.data.startswith("mydelete:"))
async def delete_profile(callback: CallbackQuery, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == callback.from_user.id:
        profile.status = ProfileStatus.DELETED
        profile.is_active = False
        await session.commit()
    lang = await get_lang(session, callback.from_user.id)
    await callback.answer("🗑 Анкета удалена" if lang == "ru" else "🗑 Anketa o'chirildi")
    await show_main_menu(callback, session)


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
async def contact_moderator_menu(callback: CallbackQuery, session: AsyncSession):
    """Шаг 12 — Связаться с модератором."""
    from bot.config import config
    lang = await get_lang(session, callback.from_user.id)

    # Пытаемся определить регион пользователя по его анкете
    result = await session.execute(
        select(Profile).where(Profile.user_id == callback.from_user.id).limit(1)
    )
    profile = result.scalar_one_or_none()

    if profile and profile.residence_status:
        res = profile.residence_status.value
        if res == "uzbekistan":
            region = "🇺🇿 Узбекистан" if lang == "ru" else "🇺🇿 O'zbekiston"
            moderator = config.moderator_tashkent
            hours = "09:00–21:00 (UZT)"
        elif res == "cis":
            region = "🇷🇺 СНГ" if lang == "ru" else "🇷🇺 MDH"
            moderator = config.moderator_cis
            hours = "09:00–21:00 (MSK)"
        elif res == "usa":
            region = "🇺🇸 США" if lang == "ru" else "🇺🇸 AQSH"
            moderator = config.moderator_usa
            hours = "09:00–21:00 (EST)"
        elif res == "europe":
            region = "🌍 Европа" if lang == "ru" else "🌍 Yevropa"
            moderator = config.moderator_europe
            hours = "09:00–21:00 (CET)"
        else:
            region = "🇺🇿 Узбекистан"
            moderator = config.moderator_tashkent
            hours = "09:00–21:00 (UZT)"
    else:
        region = "🇺🇿 Узбекистан"
        moderator = config.moderator_tashkent
        hours = "09:00–21:00 (UZT)"

    await callback.message.edit_text(
        t("contact_moderator", lang, region=region, moderator=moderator, hours=hours),
        reply_markup=back_kb(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:son")
async def start_son_quest(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 5А — Начало анкеты сына. Если анкета уже есть — переходим к поиску."""
    lang = await get_lang(session, callback.from_user.id)

    # Проверяем, есть ли у пользователя уже анкета типа SON
    result = await session.execute(
        select(Profile).where(
            Profile.user_id == callback.from_user.id,
            Profile.profile_type == ProfileType.SON,
            Profile.status != ProfileStatus.DELETED,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Уже есть анкета — показываем поиск невесток
        callback.data = "search:browse"
        from bot.handlers.search import search_profiles
        await search_profiles(callback, session)
        return

    await state.update_data(lang=lang, profile_type="son")
    await callback.message.edit_text(
        t("quest_son_intro", lang),
        reply_markup=quest_start_kb(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:daughter")
async def start_daughter_quest(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 5Б — Начало анкеты дочери."""
    lang = await get_lang(session, callback.from_user.id)
    await state.update_data(lang=lang, profile_type="daughter")
    await callback.message.edit_text(
        t("quest_daughter_intro", lang),
        reply_markup=quest_start_kb(lang),
    )
    await callback.answer()
