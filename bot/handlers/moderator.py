"""Шаг 9 — Модератор: проверка анкет и оплат, ответ пользователям, /ankety, /stats, /vip."""

import logging
from datetime import datetime, timedelta

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    Profile, ProfileStatus, Payment, PaymentStatus, User, VipStatus,
    Favorite, ProfileType, ContactRequest, RequestStatus,
    VipRequest, VipRequestStatus, VipPaymentMethod,
    Requirement, Complaint, Meeting, Feedback,
    PhotoType,
)
from bot.states import ModeratorReplyStates, ModeratorEditStates, ContactStates, VipModReplyStates
from bot.texts import t
from bot.config import config, is_moderator
from bot.keyboards.inline import (
    mod_review_kb, mod_found_kb, mod_vip_duration_kb,
    vip_mod_list_kb, vip_mod_card_kb, vip_after_reply_kb,
    confirmation_kb,
)
from bot.utils.helpers import (
    education_label,
    format_full_anketa,
    marital_label,
    occupation_label,
    religiosity_label,
)
from bot.utils.safe_send import (
    safe_send_message, safe_send_photo, safe_send_document, safe_send_voice,
)
from bot.utils.audit import audit

logger = logging.getLogger(__name__)
router = Router()


# ── Поля анкеты, которые может редактировать модератор ──
EDITABLE_FIELDS = {
    "name": {
        "ru": "✏️ Имя",
        "uz": "✏️ Ism",
        "column": "name",
    },
    "character": {
        "ru": "🌸 Характер и увлечения",
        "uz": "🌸 Xarakter va qiziqishlar",
        "column": "character_hobbies",
    },
    "about": {
        "ru": "💭 О себе",
        "uz": "💭 O'zi haqida",
        "column": "ideal_family_life",
    },
    "health": {
        "ru": "🌿 Здоровье",
        "uz": "🌿 Sog'liq",
        "column": "health_notes",
    },
}


MOD_PAGE_SIZE = 5

_MOD_STATUS_MAP = {
    "pending":   ProfileStatus.PENDING,
    "published": ProfileStatus.PUBLISHED,
    "paused":    ProfileStatus.PAUSED,
    "rejected":  ProfileStatus.REJECTED,
}

_MOD_STATUS_LABELS = {
    "pending":   "🆕 На проверке",
    "published": "✅ Активные",
    "paused":    "⏸ На паузе",
    "rejected":  "❌ Отклонённые",
}


async def _mod_ankety_submenu_kb(session: AsyncSession) -> InlineKeyboardMarkup:
    """Подменю /ankety с актуальными счётчиками по статусам."""
    counts = {}
    for key, st in _MOD_STATUS_MAP.items():
        res = await session.execute(
            select(func.count(Profile.id)).where(Profile.status == st)
        )
        counts[key] = res.scalar() or 0
    buttons = [
        [InlineKeyboardButton(
            text=f"🆕 На проверке ({counts['pending']})",
            callback_data="modlist:pending:0",
        )],
        [InlineKeyboardButton(
            text=f"✅ Активные ({counts['published']})",
            callback_data="modlist:published:0",
        )],
        [InlineKeyboardButton(
            text=f"⏸ На паузе ({counts['paused']})",
            callback_data="modlist:paused:0",
        )],
        [InlineKeyboardButton(
            text=f"❌ Отклонённые ({counts['rejected']})",
            callback_data="modlist:rejected:0",
        )],
        [InlineKeyboardButton(
            text="🔍 Найти по ID",
            callback_data="modlist:find",
        )],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── /ankety — подменю по статусам ──


@router.message(Command("ankety"))
async def cmd_ankety(message: Message, session: AsyncSession, bot: Bot):
    if not is_moderator(message.from_user.id):
        await message.answer("⛔ Только для модераторов")
        return
    kb = await _mod_ankety_submenu_kb(session)
    await message.answer("📋 <b>Анкеты:</b>", reply_markup=kb, parse_mode="HTML")


# ── Подменю /ankety: список по статусу с пагинацией ──


@router.callback_query(F.data == "modlist:back")
async def mod_list_back(callback: CallbackQuery, session: AsyncSession):
    """Назад в подменю /ankety."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    kb = await _mod_ankety_submenu_kb(session)
    try:
        await callback.message.edit_text(
            "📋 <b>Анкеты:</b>", reply_markup=kb, parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            "📋 <b>Анкеты:</b>", reply_markup=kb, parse_mode="HTML"
        )
    await callback.answer()


@router.callback_query(F.data == "modlist:find")
async def mod_list_find(callback: CallbackQuery):
    """Подсказка по команде /find."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="modlist:back")],
    ])
    try:
        await callback.message.edit_text(
            "🔍 Введите команду:\n\n<code>/find &lt;display_id или @username&gt;</code>",
            reply_markup=kb,
            parse_mode="HTML",
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


@router.callback_query(F.data.startswith("modlist:"))
async def mod_list_profiles(callback: CallbackQuery, session: AsyncSession):
    """modlist:{status}:{offset} — список анкет в категории с пагинацией."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return

    parts = callback.data.split(":")
    # back и find обрабатываются выше, но на всякий случай
    if len(parts) < 3:
        await callback.answer()
        return
    status_key = parts[1]
    try:
        offset = int(parts[2])
    except ValueError:
        offset = 0

    status_enum = _MOD_STATUS_MAP.get(status_key)
    if not status_enum:
        await callback.answer("❌")
        return

    total_res = await session.execute(
        select(func.count(Profile.id)).where(Profile.status == status_enum)
    )
    total = total_res.scalar() or 0

    # Подзапрос: кол-во лайков по каждой анкете
    fav_count_sub = (
        select(Favorite.profile_id, func.count(Favorite.id).label("fc"))
        .group_by(Favorite.profile_id)
        .subquery()
    )
    prof_res = await session.execute(
        select(Profile, fav_count_sub.c.fc)
        .outerjoin(fav_count_sub, fav_count_sub.c.profile_id == Profile.id)
        .where(Profile.status == status_enum)
        .order_by(Profile.created_at.desc())
        .offset(offset)
        .limit(MOD_PAGE_SIZE)
    )
    rows = prof_res.all()

    label = _MOD_STATUS_LABELS.get(status_key, status_key)
    if not rows:
        text = f"{label} ({total})\n\n📋 Анкет не найдено."
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="modlist:back")],
        ])
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        await callback.answer()
        return

    text_parts = [f"<b>{label} ({total})</b>", ""]
    buttons: list[list[InlineKeyboardButton]] = []
    now_year = datetime.now().year
    for p, fav_count in rows:
        age = (now_year - p.birth_year) if p.birth_year else "?"
        city = p.city or "—"
        views = p.views_count or 0
        favs = fav_count or 0
        text_parts.append(
            f"🔖 {p.display_id or '—'} · {p.name or '—'} · {age} · {city}\n"
            f"👁 {views} · ❤️ {favs}"
        )
        text_parts.append("")
        buttons.append([InlineKeyboardButton(
            text=f"🔖 {p.display_id or p.id}",
            callback_data=f"modlist_open:{p.id}",
        )])

    # Пагинация
    nav: list[InlineKeyboardButton] = []
    if offset > 0:
        nav.append(InlineKeyboardButton(
            text="⬅️ Пред.",
            callback_data=f"modlist:{status_key}:{max(0, offset - MOD_PAGE_SIZE)}",
        ))
    if offset + MOD_PAGE_SIZE < total:
        nav.append(InlineKeyboardButton(
            text="➡️ След.",
            callback_data=f"modlist:{status_key}:{offset + MOD_PAGE_SIZE}",
        ))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="modlist:back")])

    try:
        await callback.message.edit_text(
            "\n".join(text_parts).rstrip(),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            "\n".join(text_parts).rstrip(),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("modlist_open:"))
async def mod_list_open_profile(callback: CallbackQuery, session: AsyncSession):
    """Открыть анкету из списка — показать полный текст + mod_review_kb."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    profile_id = int(callback.data.split(":", 1)[1])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("❌ Анкета не найдена")
        return
    is_paused = profile.status == ProfileStatus.PAUSED
    text = format_full_anketa(profile, lang="ru")
    try:
        await callback.message.edit_text(
            text,
            reply_markup=mod_review_kb(profile_id, is_paused=is_paused),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=mod_review_kb(profile_id, is_paused=is_paused),
            parse_mode="HTML",
        )
    await callback.answer()


# ── /stats — детальная статистика платформы ──


@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession):
    if not is_moderator(message.from_user.id):
        await message.answer("⛔ Только для модераторов")
        return

    from sqlalchemy import cast, Date
    from datetime import date
    today = date.today()

    # ── Пользователи ──
    total_users = (await session.execute(
        select(func.count(User.id))
    )).scalar() or 0
    new_users_today = (await session.execute(
        select(func.count(User.id)).where(
            cast(User.created_at, Date) == today
        )
    )).scalar() or 0

    # ── Анкеты по статусам ──
    counts: dict[str, int] = {}
    for status in (
        ProfileStatus.PUBLISHED,
        ProfileStatus.PENDING,
        ProfileStatus.PAUSED,
        ProfileStatus.REJECTED,
    ):
        r = await session.execute(
            select(func.count(Profile.id)).where(Profile.status == status)
        )
        counts[status.value] = r.scalar() or 0
    total_profiles = sum(counts.values())

    # ── По типу ──
    sons = (await session.execute(
        select(func.count(Profile.id)).where(Profile.profile_type == ProfileType.SON)
    )).scalar() or 0
    daughters = (await session.execute(
        select(func.count(Profile.id)).where(Profile.profile_type == ProfileType.DAUGHTER)
    )).scalar() or 0

    # ── Оплаты сегодня (Payment.CONFIRMED) ──
    payments_today_res = await session.execute(
        select(
            func.count(Payment.id),
            func.coalesce(func.sum(Payment.amount), 0),
        ).where(
            Payment.status == PaymentStatus.CONFIRMED,
            cast(Payment.created_at, Date) == today,
        )
    )
    pay_count, pay_sum_tiyin = payments_today_res.one()
    payments_today = pay_count or 0
    # amount хранится в тиинах (копейках): 1 sum = 100 tiyin
    income_today_sum = int((pay_sum_tiyin or 0) / 100)

    # ── Просмотры (суммарно по платформе) ──
    views_total = (await session.execute(
        select(func.coalesce(func.sum(Profile.views_count), 0))
    )).scalar() or 0

    # ── Топ-5 городов среди опубликованных ──
    top_cities_res = await session.execute(
        select(Profile.city, func.count(Profile.id).label("cnt"))
        .where(
            Profile.status == ProfileStatus.PUBLISHED,
            Profile.city.isnot(None),
            Profile.city != "",
        )
        .group_by(Profile.city)
        .order_by(func.count(Profile.id).desc())
        .limit(5)
    )
    top_cities = top_cities_res.all()

    text = (
        f"📊 <b>Статистика Rishta</b>\n"
        f"📅 {today.strftime('%d.%m.%Y')}\n\n"

        f"👥 <b>Пользователи:</b>\n"
        f"• Всего: <b>{total_users}</b>\n"
        f"• Сегодня новых: <b>{new_users_today}</b>\n\n"

        f"📋 <b>Анкеты:</b>\n"
        f"• Всего: <b>{total_profiles}</b>\n"
        f"• ✅ Активных: <b>{counts.get('published', 0)}</b>\n"
        f"• 🆕 На проверке: <b>{counts.get('pending', 0)}</b>\n"
        f"• ⏸ На паузе: <b>{counts.get('paused', 0)}</b>\n"
        f"• ❌ Отклонённых: <b>{counts.get('rejected', 0)}</b>\n\n"

        f"👦 Сыновья: <b>{sons}</b>\n"
        f"👧 Дочери: <b>{daughters}</b>\n\n"

        f"💳 <b>Оплаты сегодня:</b>\n"
        f"• Количество: <b>{payments_today}</b>\n"
        f"• Доход: <b>{format(income_today_sum, ',').replace(',', ' ')} сум</b>\n\n"

        f"👁 Просмотров всего: <b>{views_total}</b>\n"
    )

    if top_cities:
        text += "\n🏆 <b>Топ городов:</b>\n"
        for city, cnt in top_cities:
            if city:
                text += f"• {city}: <b>{cnt}</b>\n"

    await message.answer(text, parse_mode="HTML")


@router.callback_query(F.data.startswith("mod:publish:"))
async def mod_publish(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор публикует анкету."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена")
        return

    profile.status = ProfileStatus.PUBLISHED
    profile.published_at = datetime.now()
    await session.commit()
    audit(
        "profile_published",
        actor=f"mod:{callback.from_user.id}",
        target=f"user:{profile.user_id}" if profile.user_id else None,
        profile_id=profile.id,
        display_id=profile.display_id,
    )

    # Уведомляем пользователя
    lang = "ru"
    try:
        from sqlalchemy import select
        from bot.db.models import User
        result = await session.execute(select(User).where(User.id == profile.user_id))
        user = result.scalar_one_or_none()
        if user and user.language:
            lang = user.language.value
    except Exception as _e:
        logger.debug("ignored: %s", _e)

    await safe_send_message(
        bot,
        profile.user_id,
        t("mod_profile_published", lang, display_id=profile.display_id),
        label="mod_profile_published",
    )
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ ОПУБЛИКОВАНО",
    )
    await callback.answer("✅ Опубликовано")


@router.callback_query(F.data.startswith("mod:reject:"))
async def mod_reject(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор отклоняет анкету."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена")
        return

    profile.status = ProfileStatus.REJECTED
    await session.commit()
    audit(
        "profile_rejected",
        actor=f"mod:{callback.from_user.id}",
        target=f"user:{profile.user_id}" if profile.user_id else None,
        profile_id=profile.id,
        display_id=profile.display_id,
    )

    lang = "ru"
    try:
        from sqlalchemy import select
        from bot.db.models import User
        result = await session.execute(select(User).where(User.id == profile.user_id))
        user = result.scalar_one_or_none()
        if user and user.language:
            lang = user.language.value
    except Exception as _e:
        logger.debug("ignored: %s", _e)

    await safe_send_message(
        bot,
        profile.user_id,
        t("mod_profile_rejected", lang, display_id=profile.display_id),
        label="mod_profile_rejected",
    )
    await callback.message.edit_text(
        callback.message.text + "\n\n❌ ОТКЛОНЕНО",
    )
    await callback.answer("❌ Отклонено")


@router.callback_query(F.data.startswith("mod:reject_photo:"))
async def mod_reject_photo(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор отклоняет фото."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена")
        return

    profile.photo_file_id = None
    from bot.db.models import PhotoType
    profile.photo_type = PhotoType.NONE
    await session.commit()

    await safe_send_message(
        bot,
        profile.user_id,
        "📸 Модератор отклонил фото в анкете " + (profile.display_id or "") +
        ". Пожалуйста, загрузите другое фото через «Редактировать анкету».",
        label="mod_reject_photo",
    )
    await callback.message.edit_text(
        callback.message.text + "\n\n📸 ФОТО ОТКЛОНЕНО",
    )
    await callback.answer("📸 Фото отклонено")


# ── Пауза / активация анкеты модератором ──


@router.callback_query(F.data.startswith("mod:pause:"))
async def mod_pause(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор ставит анкету на паузу."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("❌ Анкета не найдена")
        return

    profile.is_active = False
    profile.status = ProfileStatus.PAUSED
    await session.commit()

    display_id = profile.display_id or "—"

    # Уведомить владельца
    if profile.user_id:
        owner_lang = "ru"
        try:
            owner = await session.get(User, profile.user_id)
            owner_lang = owner.language.value if owner and owner.language else "ru"
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        if owner_lang == "uz":
            msg = (
                f"⏸ <b>Anketangiz to'xtatildi</b>\n\n"
                f"🔖 {display_id}\n\n"
                f"Moderator bilan bog'laning."
            )
        else:
            msg = (
                f"⏸ <b>Ваша анкета приостановлена</b>\n\n"
                f"🔖 {display_id}\n\n"
                f"Свяжитесь с модератором."
            )
        await safe_send_message(bot, profile.user_id, msg, parse_mode="HTML", label="mod_pause_notify")
    try:
        await callback.message.edit_reply_markup(
            reply_markup=mod_review_kb(profile_id, is_paused=True)
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("⏸ Приостановлено")


@router.callback_query(F.data.startswith("mod:activate:"))
async def mod_activate(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор активирует ранее приостановленную анкету."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("❌ Анкета не найдена")
        return

    profile.is_active = True
    profile.status = ProfileStatus.PUBLISHED
    if not profile.published_at:
        profile.published_at = datetime.now()
    await session.commit()

    display_id = profile.display_id or "—"

    # Уведомить владельца
    if profile.user_id:
        try:
            owner = await session.get(User, profile.user_id)
            owner_lang = owner.language.value if owner and owner.language else "ru"
        except Exception as _e:
            logger.debug("ignored: %s", _e)
            owner_lang = "ru"
        if owner_lang == "uz":
            msg = (
                f"✅ <b>Anketangiz faollashtirildi!</b>\n\n"
                f"🔖 {display_id}\n\n"
                f"Endi anketangiz qidirishda ko'rinadi. 🤲"
            )
        else:
            msg = (
                f"✅ <b>Ваша анкета активирована!</b>\n\n"
                f"🔖 {display_id}\n\n"
                f"Теперь анкета снова видна в поиске. 🤲"
            )
        await safe_send_message(bot, profile.user_id, msg, parse_mode="HTML", label="mod_activate_notify")
    try:
        await callback.message.edit_reply_markup(
            reply_markup=mod_review_kb(profile_id, is_paused=False)
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("✅ Активировано")


# ── Редактирование анкеты модератором ──


@router.callback_query(F.data.startswith("mod:edit:"))
async def mod_edit_start(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Начать редактирование — показать список полей."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("❌ Анкета не найдена")
        return

    await state.update_data(editing_profile_id=profile_id)

    buttons = []
    for key, field in EDITABLE_FIELDS.items():
        buttons.append([InlineKeyboardButton(
            text=field["ru"],
            callback_data=f"modedit:{key}",
        )])
    buttons.append([InlineKeyboardButton(
        text="🔙 Отмена",
        callback_data=f"modedit:cancel:{profile_id}",
    )])

    display_id = profile.display_id or "—"
    try:
        await callback.message.edit_text(
            f"✏️ Редактирование анкеты <b>{display_id}</b>\n\nВыберите поле:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"✏️ Редактирование анкеты <b>{display_id}</b>\n\nВыберите поле:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML",
        )
    await state.set_state(ModeratorEditStates.choosing_field)
    await callback.answer()


@router.callback_query(F.data.startswith("modedit:cancel:"), ModeratorEditStates.choosing_field)
async def mod_edit_cancel(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Отмена редактирования — вернуть стандартную клавиатуру модератора."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    await state.clear()
    if not profile:
        await callback.answer("❌ Анкета не найдена")
        return
    is_paused = profile.status == ProfileStatus.PAUSED
    try:
        await callback.message.edit_text(
            format_full_anketa(profile, lang="ru"),
            reply_markup=mod_review_kb(profile_id, is_paused=is_paused),
            parse_mode="HTML",
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("Отменено")


@router.callback_query(F.data.startswith("modedit:"), ModeratorEditStates.choosing_field)
async def mod_edit_field(callback: CallbackQuery, session: AsyncSession, state: FSMContext):
    """Выбрал поле — спросить новое значение."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return

    field_key = callback.data.split(":", 1)[1]
    if field_key.startswith("cancel"):
        return  # обработано выше
    field = EDITABLE_FIELDS.get(field_key)
    if not field:
        await callback.answer("❌ Поле не найдено")
        return

    data = await state.get_data()
    profile_id = data.get("editing_profile_id")
    profile = await session.get(Profile, profile_id) if profile_id else None
    current = getattr(profile, field["column"], None) if profile else None
    current_txt = f"\n\nТекущее: <i>{current}</i>" if current else ""

    await state.update_data(editing_field=field_key)
    try:
        await callback.message.edit_text(
            f"{field['ru']}{current_txt}\n\nВведите новое значение:",
            parse_mode="HTML",
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await state.set_state(ModeratorEditStates.editing_value)
    await callback.answer()


@router.message(ModeratorEditStates.editing_value)
async def mod_edit_save(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Получили новое значение — сохранить и уведомить владельца."""
    if not is_moderator(message.from_user.id):
        return

    data = await state.get_data()
    profile_id = data.get("editing_profile_id")
    field_key = data.get("editing_field")
    new_value = (message.text or "").strip()

    if not new_value:
        await message.answer("⚠️ Пустое значение — отправьте текст или /cancel")
        return

    profile = await session.get(Profile, profile_id)
    if not profile:
        await message.answer("❌ Анкета не найдена")
        await state.clear()
        return

    field = EDITABLE_FIELDS.get(field_key)
    if not field:
        await message.answer("❌ Поле не найдено")
        await state.clear()
        return

    setattr(profile, field["column"], new_value)
    await session.commit()

    await message.answer(
        f"✅ Сохранено!\n\n"
        f"Поле: {field['ru']}\n"
        f"Значение: {new_value}"
    )
    await state.clear()

    # Уведомление владельцу
    if profile.user_id:
        owner_lang = "ru"
        try:
            owner = await session.get(User, profile.user_id)
            owner_lang = owner.language.value if owner and owner.language else "ru"
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        display_id = profile.display_id or "—"
        if owner_lang == "uz":
            msg = (
                f"✏️ <b>Anketangiz tahrirlandi</b>\n\n"
                f"🔖 {display_id}\n\n"
                f"Moderator anketangizni\n"
                f"to'g'riladi. 🤝"
            )
        else:
            msg = (
                f"✏️ <b>Ваша анкета отредактирована</b>\n\n"
                f"🔖 {display_id}\n\n"
                f"Модератор исправил данные\n"
                f"в вашей анкете. 🤝"
            )
        await safe_send_message(bot, profile.user_id, msg, parse_mode="HTML", label="mod_edit_notify")


# ── Подтверждение оплаты модератором ──


@router.callback_query(F.data.startswith("modpay:confirm:"))
async def mod_confirm_payment(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    payment_id = int(callback.data.split(":")[2])
    payment = await session.get(Payment, payment_id)
    if not payment:
        await callback.answer("Оплата не найдена")
        return

    payment.status = PaymentStatus.CONFIRMED
    payment.confirmed_at = datetime.now()
    await session.commit()
    audit(
        "payment_confirmed",
        actor=f"mod:{callback.from_user.id}",
        target=f"user:{payment.user_id}",
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
        profile_id=payment.profile_id,
    )

    # Отправляем контакты пользователю
    profile = await session.get(Profile, payment.profile_id)
    if profile:
        from bot.handlers.payment import send_contact_details
        await send_contact_details(bot, session, payment.user_id, profile)

    await callback.message.edit_text(
        callback.message.text + "\n\n✅ ОПЛАТА ПОДТВЕРЖДЕНА",
    )
    await callback.answer("✅ Подтверждено")


@router.callback_query(F.data.startswith("modpay:reject:"))
async def mod_reject_payment_confirm(callback: CallbackQuery, session: AsyncSession):
    """Шаг 1: показать подтверждение отклонения оплаты."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    payment_id = int(callback.data.split(":")[2])
    payment = await session.get(Payment, payment_id)
    if not payment:
        await callback.answer("Оплата не найдена")
        return

    amount_str = f"{(payment.amount or 0) // 100:,} {payment.currency or 'UZS'}"
    prompt = (
        f"⚠️ Отклонить оплату #{payment.id} на <b>{amount_str}</b>?\n\n"
        f"Пользователь не получит контакт.\n"
        f"Revert — только через SQL."
    )
    try:
        await callback.message.edit_text(
            prompt,
            reply_markup=confirmation_kb(
                yes_cb=f"modpay:reject_yes:{payment.id}",
                no_cb="confirm:cancel",
            ),
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


@router.callback_query(F.data.startswith("modpay:reject_yes:"))
async def mod_reject_payment_do(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Шаг 2: фактическое отклонение оплаты (после подтверждения)."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    payment_id = int(callback.data.split(":")[2])
    payment = await session.get(Payment, payment_id)
    if not payment:
        await callback.answer("Оплата не найдена")
        return

    payment.status = PaymentStatus.REJECTED
    await session.commit()
    audit(
        "payment_rejected",
        actor=f"mod:{callback.from_user.id}",
        target=f"user:{payment.user_id}",
        payment_id=payment.id,
        amount=payment.amount,
        currency=payment.currency,
    )

    await safe_send_message(
        bot,
        payment.user_id,
        "❌ Оплата отклонена модератором. Свяжитесь с модератором для уточнения.",
        label="mod_reject_payment_notify",
    )
    try:
        await callback.message.edit_text(f"❌ Оплата #{payment.id} отклонена.")
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("❌ Отклонено")


# ── Ответ пользователю от модератора ──


@router.callback_query(F.data.startswith("modreply:"))
async def mod_reply_start(callback: CallbackQuery, state: FSMContext):
    """Модератор нажал «Ответить» — ожидаем текст."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    user_id = int(callback.data.split(":")[1])
    await state.update_data(reply_to_user_id=user_id)
    await callback.message.answer(f"✍️ Напишите ответ для пользователя (ID: {user_id}):")
    await state.set_state(ModeratorReplyStates.awaiting_reply)
    await callback.answer()


@router.message(ModeratorReplyStates.awaiting_reply)
async def mod_reply_send(message: Message, state: FSMContext, bot: Bot):
    """Модератор написал ответ — пересылаем пользователю."""
    if not is_moderator(message.from_user.id):
        await state.clear()
        return

    data = await state.get_data()
    user_id = data.get("reply_to_user_id")
    if not user_id:
        await state.clear()
        return

    header = "💬 <b>Ответ от модератора:</b>\n\n"
    # Каждый send — отдельный safe-вызов: падение одного не блокирует остальные
    text_ok = await safe_send_message(
        bot, user_id, header + (message.text or ""),
        label="modreply_forward_text",
    )
    if message.photo:
        await safe_send_photo(bot, user_id, message.photo[-1].file_id, label="modreply_forward_photo")
    if message.document:
        await safe_send_document(bot, user_id, message.document.file_id, label="modreply_forward_document")
    if message.voice:
        await safe_send_voice(bot, user_id, message.voice.file_id, label="modreply_forward_voice")

    if text_ok:
        await message.answer(f"✅ Ответ отправлен пользователю (ID: {user_id})")
    else:
        await message.answer(f"⚠️ Не удалось отправить ответ пользователю (ID: {user_id})")

    await state.clear()


# ══════════════════════════════════════════════════════════
#  /find — Поиск анкеты по номеру для модератора
# ══════════════════════════════════════════════════════════


@router.message(Command("find"))
async def cmd_find(message: Message, session: AsyncSession, bot: Bot):
    """
    /find ДД-2026-00023
    /find СН-2026-00001
    /find 00023
    /find #ДД-2026-00023
    """
    if not is_moderator(message.from_user.id):
        await message.answer("⛔ Только для модераторов")
        return

    # Получаем аргумент
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "❓ Укажите номер анкеты.\n\n"
            "Пример:\n"
            "/find ДД-2026-00023\n"
            "/find СН-2026-00001\n"
            "/find 00023"
        )
        return

    search_query = parts[1].strip()

    # Нормализуем: убираем # если есть
    q = search_query.lstrip("#").upper()

    # Пробуем точный поиск по display_id
    profile = None

    # Полный формат: ДД-2026-00023 или СН-2026-00001
    if q.startswith(("ДД-", "СН-")):
        result = await session.execute(
            select(Profile).where(Profile.display_id == f"#{q}")
        )
        profile = result.scalar_one_or_none()

    # Только число: 00023 или 23
    if not profile:
        # Ищем по LIKE
        result = await session.execute(
            select(Profile).where(
                Profile.display_id.ilike(f"%{q}%")
            ).order_by(Profile.created_at.desc()).limit(1)
        )
        profile = result.scalar_one_or_none()

    if not profile:
        await message.answer(
            f"❌ Анкета не найдена: <b>{search_query}</b>\n\n"
            f"Проверьте номер и попробуйте снова.\n"
            f"Пример: /find ДД-2026-00023"
        )
        return

    # Нашли — формируем полную анкету
    full_text = format_full_anketa(profile, lang="ru")

    # Статус
    status_map = {
        ProfileStatus.DRAFT: "📝 Черновик",
        ProfileStatus.PENDING: "⏳ На проверке",
        ProfileStatus.PUBLISHED: "✅ Активна",
        ProfileStatus.REJECTED: "❌ Отклонена",
        ProfileStatus.PAUSED: "⏸ На паузе",
        ProfileStatus.DELETED: "🗑 Удалена",
    }
    status_label = status_map.get(profile.status, "—")
    vip_label = " · ⭐ VIP" if profile.vip_status == VipStatus.ACTIVE else ""

    header = (
        f"🔎 <b>РЕЗУЛЬТАТ ПОИСКА</b>\n"
        f"Статус: {status_label}{vip_label}\n"
        f"👁 Просмотров: {profile.views_count or 0} · 💬 Запросов: {profile.requests_count or 0}\n"
        f"━━━━━━━━━━━━━━━\n"
    )
    full_text = header + full_text

    # Кнопки
    if profile.status == ProfileStatus.PENDING:
        kb = mod_review_kb(profile.id)
    else:
        is_published = profile.status == ProfileStatus.PUBLISHED
        is_vip = profile.vip_status == VipStatus.ACTIVE
        kb = mod_found_kb(profile.id, is_published, is_vip)

    # Отправляем — tri-state через safe_send_* с fallback на text-split.
    chat_id = message.from_user.id

    # Ветка 1: photo + короткий caption — всё одним сообщением
    if profile.photo_file_id and len(full_text) <= 1024:
        ok = await safe_send_photo(
            bot, chat_id, profile.photo_file_id,
            caption=full_text, reply_markup=kb,
            label="mod_find_photo_caption",
        )
        if ok:
            return
        # Если фото не отправилось (flood/forbidden/bad request) —
        # fallback на text-only ниже

    # Ветка 2: photo + текст слишком длинный для caption — фото без caption,
    # текст отдельно. Текст обрабатывается text-only секцией ниже (возможен split).
    elif profile.photo_file_id and len(full_text) > 1024:
        await safe_send_photo(
            bot, chat_id, profile.photo_file_id,
            label="mod_find_photo_only",
        )
        # fallthrough → text-only секция отправит full_text

    # Ветка 3 (и fallback для 1/2): только текст. Если > 4096 — split на две части,
    # reply_markup на последней.
    if len(full_text) <= 4096:
        await safe_send_message(
            bot, chat_id, full_text, reply_markup=kb,
            label="mod_find_text",
        )
    else:
        await safe_send_message(
            bot, chat_id, full_text[:4096],
            label="mod_find_text_part1",
        )
        await safe_send_message(
            bot, chat_id, full_text[4096:], reply_markup=kb,
            label="mod_find_text_part2",
        )


# ── Действия модератора с найденной анкетой ──


@router.callback_query(F.data.startswith("modfind:"))
async def mod_find_action(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """modfind:pause:123 / modfind:activate:123 / modfind:block:123"""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    parts = callback.data.split(":")
    action = parts[1]
    profile_id = int(parts[2])

    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("❌ Анкета не найдена")
        return

    display_id = profile.display_id or "—"
    owner_id = profile.user_id

    # Язык владельца
    owner_lang = "ru"
    if owner_id:
        result = await session.execute(select(User).where(User.id == owner_id))
        owner_user = result.scalar_one_or_none()
        if owner_user and owner_user.language:
            owner_lang = owner_user.language.value

    if action == "pause":
        profile.status = ProfileStatus.PAUSED
        profile.is_active = False
        await session.commit()

        await callback.message.edit_text(
            f"⏸ Анкета <b>{display_id}</b> поставлена на паузу.",
        )
        if owner_id:
            msg = (
                f"⏸ Sizning anketangiz <b>{display_id}</b> moderator tomonidan pauzaga qo'yildi."
                if owner_lang == "uz" else
                f"⏸ Ваша анкета <b>{display_id}</b> поставлена на паузу модератором."
            )
            await safe_send_message(bot, owner_id, msg, label="mod_manage_pause_notify")
    elif action == "activate":
        profile.status = ProfileStatus.PUBLISHED
        profile.is_active = True
        if not profile.published_at:
            profile.published_at = datetime.now()
        await session.commit()

        await callback.message.edit_text(
            f"🟢 Анкета <b>{display_id}</b> активирована.",
        )
        if owner_id:
            msg = (
                f"🟢 Sizning anketangiz <b>{display_id}</b> yana faol!"
                if owner_lang == "uz" else
                f"🟢 Ваша анкета <b>{display_id}</b> снова активна!"
            )
            await safe_send_message(bot, owner_id, msg, label="mod_manage_activate_notify")
    elif action == "block":
        profile.status = ProfileStatus.REJECTED
        profile.is_active = False
        await session.commit()
        audit(
            "profile_blocked",
            actor=f"mod:{callback.from_user.id}",
            target=f"user:{owner_id}" if owner_id else None,
            profile_id=profile.id,
            display_id=display_id,
        )

        await callback.message.edit_text(
            f"❌ Анкета <b>{display_id}</b> заблокирована.",
        )
        if owner_id:
            msg = (
                f"❌ Sizning anketangiz <b>{display_id}</b> moderator tomonidan bloklandi."
                if owner_lang == "uz" else
                f"❌ Ваша анкета <b>{display_id}</b> заблокирована модератором."
            )
            await safe_send_message(bot, owner_id, msg, label="mod_manage_block_notify")
    elif action == "vip_add":
        # Показать выбор срока VIP
        await callback.message.edit_text(
            f"⭐ <b>Присвоить VIP</b>\n\n"
            f"Анкета: <b>{display_id}</b>\n\n"
            f"Выберите срок:",
            reply_markup=mod_vip_duration_kb(profile.id),
        )

    elif action == "vip_remove":
        # Шаг 1 — показать подтверждение. Фактическое снятие — в vip_remove_yes.
        expires_str = ""
        if profile.vip_expires_at:
            expires_str = f" (действует до {profile.vip_expires_at.strftime('%d.%m.%Y')})"
        try:
            await callback.message.edit_text(
                f"⚠️ Снять VIP с анкеты <b>{display_id}</b>{expires_str}?\n\n"
                f"Оставшиеся оплаченные дни будут потеряны.",
                reply_markup=confirmation_kb(
                    yes_cb=f"modfind:vip_remove_yes:{profile.id}",
                    no_cb="confirm:cancel",
                ),
            )
        except Exception as _e:
            logger.debug("ignored: %s", _e)

    elif action == "vip_remove_yes":
        # Шаг 2 — фактическое снятие VIP после подтверждения.
        profile.vip_status = VipStatus.NONE
        profile.vip_expires_at = None
        await session.commit()
        audit(
            "vip_removed_manual",
            actor=f"mod:{callback.from_user.id}",
            target=f"user:{owner_id}" if owner_id else None,
            profile_id=profile.id,
            display_id=display_id,
        )

        await callback.message.edit_text(
            f"⭐ VIP статус снят с анкеты <b>{display_id}</b>.",
        )
        if owner_id:
            msg = (
                f"ℹ️ <b>{display_id}</b> anketangizning VIP maqomi olib tashlandi."
                if owner_lang == "uz" else
                f"ℹ️ VIP статус анкеты <b>{display_id}</b> снят."
            )
            await safe_send_message(bot, owner_id, msg, label="mod_manage_vip_remove_notify")
    await callback.answer()


# ── Модератор выбрал срок VIP ──


@router.callback_query(F.data.startswith("modvip:"))
async def mod_vip_set_duration(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """modvip:30:123 — модератор присваивает VIP на N дней."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    parts = callback.data.split(":")
    days = int(parts[1])
    profile_id = int(parts[2])

    from datetime import timedelta
    from bot.config import VIP_DURATION_LABELS

    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("❌ Анкета не найдена")
        return

    profile.vip_status = VipStatus.ACTIVE
    profile.vip_expires_at = datetime.now() + timedelta(days=days)
    # Если анкета ещё не опубликована — публикуем
    if profile.status in (ProfileStatus.PENDING, ProfileStatus.PAUSED):
        profile.status = ProfileStatus.PUBLISHED
        profile.is_active = True
        if not profile.published_at:
            profile.published_at = datetime.now()
    await session.commit()
    audit(
        "vip_granted_manual",
        actor=f"mod:{callback.from_user.id}",
        target=f"user:{profile.user_id}" if profile.user_id else None,
        profile_id=profile.id,
        display_id=profile.display_id,
        days=days,
        expires_at=profile.vip_expires_at.isoformat(),
    )

    display_id = profile.display_id or "—"
    days_label = VIP_DURATION_LABELS.get(days, {}).get("ru", f"{days} дней")
    vip_until = profile.vip_expires_at.strftime("%d.%m.%Y")

    await callback.message.edit_text(
        f"⭐ <b>VIP статус присвоен!</b>\n\n"
        f"Анкета: <b>{display_id}</b>\n"
        f"Срок: {days_label}\n"
        f"Действует до: {vip_until}",
    )

    # Уведомляем владельца
    if profile.user_id:
        owner_lang = "ru"
        result = await session.execute(select(User).where(User.id == profile.user_id))
        owner_user = result.scalar_one_or_none()
        if owner_user and owner_user.language:
            owner_lang = owner_user.language.value

        days_label_uz = VIP_DURATION_LABELS.get(days, {}).get("uz", f"{days} kun")

        if owner_lang == "uz":
            msg = (
                f"⭐ <b>Tabriklaymiz!</b>\n\n"
                f"<b>{display_id}</b> anketangizga VIP maqomi berildi!\n\n"
                f"Anketangiz:\n"
                f"• Qidirishda birinchi ko'rinadi\n"
                f"• ⭐ belgisi bilan ajratiladi\n\n"
                f"Muddat: {days_label_uz}\n"
                f"Amal qilish: {vip_until} gacha 🎉"
            )
        else:
            msg = (
                f"⭐ <b>Поздравляем!</b>\n\n"
                f"Вашей анкете <b>{display_id}</b> присвоен статус VIP!\n\n"
                f"Ваша анкета:\n"
                f"• Показывается первой в поиске\n"
                f"• Выделена значком ⭐\n\n"
                f"Срок: {days_label}\n"
                f"Действует до: {vip_until} 🎉"
            )
        await safe_send_message(bot, profile.user_id, msg, label="mod_vip_granted_notify")
    await callback.answer()


# ── Опубликовать как VIP при модерации ──


@router.callback_query(F.data.startswith("mod:publish_vip:"))
async def mod_publish_vip(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Модератор публикует анкету и сразу ставит VIP — выбор срока."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    profile_id = int(callback.data.split(":")[2])
    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена")
        return

    # Публикуем
    profile.status = ProfileStatus.PUBLISHED
    profile.published_at = datetime.now()
    profile.is_active = True
    await session.commit()

    # Уведомляем пользователя о публикации
    lang = "ru"
    try:
        result = await session.execute(select(User).where(User.id == profile.user_id))
        user = result.scalar_one_or_none()
        lang = user.language.value if user and user.language else "ru"
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await safe_send_message(
        bot, profile.user_id,
        t("mod_profile_published", lang, display_id=profile.display_id),
        label="mod_publish_vip_notify",
    )
    # Показываем выбор срока VIP
    await callback.message.edit_text(
        f"✅ Анкета <b>{profile.display_id}</b> опубликована!\n\n"
        f"⭐ Выберите срок VIP:",
        reply_markup=mod_vip_duration_kb(profile.id),
    )
    await callback.answer()


# ══════════════════════════════════════════════════════
# /dbcheck — диагностика состояния таблицы profiles (только для модераторов)
# ══════════════════════════════════════════════════════


@router.message(Command("dbcheck"))
async def db_check(message: Message, session: AsyncSession):
    """Пошаговая диагностика БД — каждый блок отправляется отдельно,
    чтобы было видно на каком запросе происходит падение."""
    if not is_moderator(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    await message.answer(f"🛠 /dbcheck запущен от id={message.from_user.id}")

    from sqlalchemy import text
    import traceback

    async def run_step(step_name: str, sql: str):
        """Выполняет SQL и шлёт результат как обычный текст (без HTML)."""
        try:
            result = await session.execute(text(sql))
            rows = result.fetchall()
            if not rows:
                await message.answer(f"{step_name}: (нет данных)")
                return
            lines = [step_name]
            for r in rows:
                lines.append("• " + " | ".join(str(v) for v in r))
            full = "\n".join(lines)
            if len(full) > 4000:
                full = full[:4000] + "\n…(обрезано)"
            await message.answer(full)
        except Exception as e:
            tb = traceback.format_exc()[:3500]
            await message.answer(f"❌ {step_name} упал:\n{type(e).__name__}: {e}\n\n{tb}")

    # Шаг 1 — общая сводка
    await run_step("📊 Состояние БД (type|status|active|cnt):", """
        SELECT profile_type, status, is_active, COUNT(*) as cnt
        FROM profiles
        GROUP BY profile_type, status, is_active
        ORDER BY cnt DESC
    """)

    # Шаг 2 — анкеты про Самарканд
    await run_step("🏙 Самарканд в БД (id|city|code|status|active):", """
        SELECT id, city, city_code, status, is_active
        FROM profiles
        WHERE city ILIKE '%samar%'
           OR city ILIKE '%самар%'
           OR city_code = 'samarkand'
        ORDER BY id
    """)

    # Шаг 3 — симуляция поиска
    await run_step("🔍 Симуляция поиска невесты в Самарканде:", """
        SELECT id, city, city_code, profile_type, status, is_active
        FROM profiles
        WHERE status = 'published'
          AND (is_active IS TRUE OR is_active IS NULL)
          AND profile_type = 'daughter'
          AND (
              city_code = 'samarkand'
              OR city ILIKE '%samar%'
              OR city ILIKE '%самар%'
          )
    """)

    # Шаг 4 — все анкеты (дамп)
    await run_step("📋 Все анкеты (последние 30, id|user|type|status|active|city|code|disp):", """
        SELECT id, user_id, profile_type, status, is_active,
               city, city_code, display_id
        FROM profiles
        ORDER BY id DESC
        LIMIT 30
    """)

    # Шаг 5 — Samarkand debug (в т.ч. проверка поля country)
    await run_step("🔍 Samarkand debug (id|city|code|country|status|active):", """
        SELECT id, city, city_code, country, status, is_active
        FROM profiles
        WHERE city_code = 'samarkand'
           OR country = 'samarkand'
    """)

    await message.answer("✅ /dbcheck завершён")


@router.message(Command("testsearch"))
async def test_search(message: Message, session: AsyncSession):
    """Прямой тест: запускает SQLAlchemy-запрос поиска как в _build_search_query."""
    if not is_moderator(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    from sqlalchemy import select, or_
    from bot.db.models import Profile, ProfileType, ProfileStatus
    import traceback

    await message.answer(f"🧪 /testsearch от id={message.from_user.id}")

    # Шаг А: без фильтров — все DAUGHTER анкеты
    try:
        q1 = select(Profile).where(
            Profile.status.in_([ProfileStatus.PUBLISHED, ProfileStatus.PENDING]),
            or_(Profile.is_active.is_(True), Profile.is_active.is_(None)),
            Profile.profile_type == ProfileType.DAUGHTER,
        )
        r1 = await session.execute(q1)
        profs = r1.scalars().all()
        lines = [f"📋 DAUGHTER profiles (без фильтра города): {len(profs)}"]
        for p in profs:
            lines.append(f"• id={p.id} city={p.city} code={p.city_code} "
                         f"status={p.status} active={p.is_active}")
        await message.answer("\n".join(lines))
    except Exception as e:
        await message.answer(f"❌ Шаг А упал: {type(e).__name__}: {e}\n\n{traceback.format_exc()[:3000]}")

    # Шаг Б: то же + фильтр samarkand по city_code
    try:
        q2 = select(Profile).where(
            Profile.status.in_([ProfileStatus.PUBLISHED, ProfileStatus.PENDING]),
            or_(Profile.is_active.is_(True), Profile.is_active.is_(None)),
            Profile.profile_type == ProfileType.DAUGHTER,
            Profile.city_code == "samarkand",
        )
        r2 = await session.execute(q2)
        profs2 = r2.scalars().all()
        lines2 = [f"📋 DAUGHTER + city_code='samarkand': {len(profs2)}"]
        for p in profs2:
            lines2.append(f"• id={p.id} city={p.city} code={p.city_code}")
        await message.answer("\n".join(lines2))
    except Exception as e:
        await message.answer(f"❌ Шаг Б упал: {type(e).__name__}: {e}")

    # Шаг В: комбинированный OR как в реальном поиске
    try:
        q3 = select(Profile).where(
            Profile.status.in_([ProfileStatus.PUBLISHED, ProfileStatus.PENDING]),
            or_(Profile.is_active.is_(True), Profile.is_active.is_(None)),
            Profile.profile_type == ProfileType.DAUGHTER,
            or_(
                Profile.city_code == "samarkand",
                Profile.city.ilike("%самарканд%"),
                Profile.city.ilike("%samarqand%"),
                Profile.city.ilike("%samarkand%"),
            ),
        )
        r3 = await session.execute(q3)
        profs3 = r3.scalars().all()
        lines3 = [f"📋 DAUGHTER + комбинированный фильтр Самарканд: {len(profs3)}"]
        for p in profs3:
            lines3.append(f"• id={p.id} city={p.city} code={p.city_code}")
        await message.answer("\n".join(lines3))
    except Exception as e:
        await message.answer(f"❌ Шаг В упал: {type(e).__name__}: {e}")

    await message.answer("✅ /testsearch завершён")


# ══════════════════════════════════════════════════════════
#  Платёжный flow: запрос контакта → оплата → согласие → контакт
# ══════════════════════════════════════════════════════════

CARD_NUMBER_TXT = "5614 6887 0899 8959"
CARD_OWNER_TXT = "SHODIYEVA NASIBA"
CONTACT_PRICE = 30_000


@router.callback_query(F.data.startswith("op_reply:"))
async def op_reply_start(callback: CallbackQuery, state: FSMContext):
    """Оператор жмёт «💬 Ответить» — ждём текст ответа."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔ Нет доступа")
        return

    parts = callback.data.split(":")
    try:
        user_id = int(parts[1])
        profile_id = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return
    req_number = parts[3] if len(parts) > 3 else "—"

    await state.update_data(
        reply_user_id=user_id,
        reply_profile_id=profile_id,
        reply_req_number=req_number,
    )
    await state.set_state(ContactStates.waiting_reply)
    try:
        await callback.message.answer(
            f"💬 Введите ответ пользователю\n📋 #{req_number}:",
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


@router.message(ContactStates.waiting_reply, F.text)
async def op_reply_send(message: Message, state: FSMContext, bot: Bot):
    """Оператор прислал текст ответа — пересылаем пользователю."""
    if not is_moderator(message.from_user.id):
        return

    data = await state.get_data()
    user_id = data.get("reply_user_id")
    profile_id = data.get("reply_profile_id")
    req_number = data.get("reply_req_number") or "—"

    if not user_id:
        await state.set_state(None)
        return

    reply_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Ещё вопрос", callback_data=f"ask_op:{profile_id}")],
        [InlineKeyboardButton(text="📤 Запросить контакт", callback_data=f"req_contact:{profile_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_profile:{profile_id}")],
    ])

    sent = await safe_send_message(
        bot,
        user_id,
        (
            f"💁‍♀️ <b>Ответ оператора:</b>\n\n"
            f"📋 #{req_number}\n\n"
            f"{message.text}"
        ),
        reply_markup=reply_kb,
        parse_mode="HTML",
        label="op_reply_send",
    )

    await message.answer(
        f"✅ Ответ отправлен!\n📋 #{req_number}"
        if sent else
        f"⚠️ Не удалось отправить\n📋 #{req_number}"
    )
    await state.set_state(None)


@router.callback_query(F.data.startswith("op_send_req:"))
async def op_send_requisites(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Оператор → «📤 Отправить реквизиты»: пользователю приходят реквизиты."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return

    parts = callback.data.split(":")
    try:
        user_id = int(parts[1])
        profile_id = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return
    req_number = parts[3] if len(parts) > 3 else "—"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📸 Отправить скриншот",
            callback_data=f"send_screenshot:{profile_id}:{req_number}",
        )],
        [InlineKeyboardButton(
            text="💬 Ещё вопрос",
            callback_data=f"ask_op:{profile_id}",
        )],
    ])

    # Язык адресата (получателя сообщения) — для двуязычного текста
    try:
        req_user = await session.get(User, user_id)
        req_lang = req_user.language.value if req_user and req_user.language else "ru"
    except Exception as _e:
        logger.debug("ignored: %s", _e)
        req_lang = "ru"

    payment_text = t("op_payment_requisites", req_lang, req_number=req_number)

    sent = await safe_send_message(
        bot, user_id, payment_text, reply_markup=kb, parse_mode="HTML",
        label="op_send_req",
    )

    try:
        await callback.message.answer(
            f"✅ Реквизиты отправлены!\n📋 #{req_number}"
            if sent else
            f"⚠️ Не удалось отправить\n📋 #{req_number}"
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("✅ Отправлено!" if sent else "⚠️ Ошибка")


@router.callback_query(F.data.startswith("op_reject:"))
async def op_reject_request(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Оператор отклоняет запрос на ранней стадии."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return

    parts = callback.data.split(":")
    try:
        user_id = int(parts[1])
        profile_id = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return
    req_number = parts[3] if len(parts) > 3 else "—"

    reject_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Продолжить поиск", callback_data="menu:search")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
    ])

    await safe_send_message(
        bot,
        user_id,
        (
            f"❌ Запрос отклонён.\n\n"
            f"📋 #{req_number}\n\n"
            f"Попробуйте найти другого\n"
            f"кандидата. 🤲"
        ),
        reply_markup=reject_kb,
        parse_mode="HTML",
        label="op_reject_request",
    )

    try:
        from sqlalchemy import update
        if req_number != "—":
            await session.execute(
                update(ContactRequest)
                .where(
                    ContactRequest.display_id == req_number,
                    ContactRequest.status == RequestStatus.PENDING,
                )
                .values(status=RequestStatus.REJECTED)
            )
            await session.commit()
            audit(
                "contact_request_rejected_early",
                actor=f"mod:{callback.from_user.id}",
                target=f"user:{user_id}",
                contact_req_display_id=req_number,
                profile_id=profile_id,
            )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    try:
        await callback.message.edit_text(
            (callback.message.text or "") + f"\n\n❌ Запрос #{req_number} отклонён",
            parse_mode="HTML",
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("❌ Отклонено")


@router.callback_query(F.data.startswith("confirm_pay:"))
async def confirm_payment(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Оператор подтвердил оплату → сразу передаём контакт покупателю."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return

    parts = callback.data.split(":")
    try:
        user_id = int(parts[1])
        profile_id = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return
    req_number = parts[3] if len(parts) > 3 else "—"

    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("❌ Анкета не найдена")
        return

    import datetime
    display_id = profile.display_id or "—"
    age = (datetime.datetime.now().year - profile.birth_year) if profile.birth_year else "?"

    # Город + район (если есть)
    city_full = profile.city or "—"
    if profile.city and profile.district:
        city_full = f"{profile.city}, {profile.district}"

    contacts = []
    if profile.parent_phone:
        contacts.append(f"📞 {profile.parent_phone}")
    if profile.parent_telegram:
        contacts.append(f"📱 {profile.parent_telegram}")
    if profile.candidate_telegram:
        contacts.append(f"💬 {profile.candidate_telegram}")
    if profile.address:
        contacts.append(f"🏠 {profile.address}")
    if profile.location_link:
        contacts.append(f"🗺 {profile.location_link}")
    contact_text = "\n".join(contacts) if contacts else "Контакты не указаны"

    try:
        req_user = await session.get(User, user_id)
        req_lang = req_user.language.value if req_user and req_user.language else "ru"
    except Exception as _e:
        logger.debug("ignored: %s", _e)
        req_lang = "ru"

    after_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Продолжить поиск", callback_data="menu:search")],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="menu:main")],
    ])

    disclaimer = t("contact_disclaimer", req_lang)
    if req_lang == "uz":
        user_msg = (
            f"✅ <b>Kontakt yuborildi!</b>\n\n"
            f"📋 #{req_number}\n"
            f"🔖 {display_id}\n"
            f"🪪 {profile.name or '—'} · {age} · {city_full}\n\n"
            f"<b>Oila kontaktlari:</b>\n"
            f"{contact_text}\n\n"
            f"{disclaimer}\n\n"
            f"Bu uchrashuv baxt boshlanishi bo'lsin! 🤲"
        )
    else:
        user_msg = (
            f"✅ <b>Контакт получен!</b>\n\n"
            f"📋 #{req_number}\n"
            f"🔖 {display_id}\n"
            f"🪪 {profile.name or '—'} · {age} · {city_full}\n\n"
            f"<b>Контакты семьи:</b>\n"
            f"{contact_text}\n\n"
            f"{disclaimer}\n\n"
            f"Пусть эта встреча станет\n"
            f"началом счастья! 🤲"
        )

    # Куда прикрепить after_kb: к последнему реальному сообщению
    has_photo = bool(profile.photo_file_id)
    has_loc = bool(profile.location_lat and profile.location_lon)

    kb_for_text = after_kb if not (has_photo or has_loc) else None
    kb_for_photo = after_kb if has_photo and not has_loc else None
    kb_for_loc = after_kb if has_loc else None

    await safe_send_message(
        bot, user_id, user_msg, reply_markup=kb_for_text, parse_mode="HTML",
        label="confirm_pay_contact",
    )

    # Фото из анкеты (если есть) — с caption по photo_type
    if has_photo:
        _caption_key = {
            PhotoType.REGULAR:      "contact_photo_regular",
            PhotoType.CLOSED_FACE:  "contact_photo_closed",
            PhotoType.SILHOUETTE:   "contact_photo_silhouette",
        }.get(profile.photo_type, "contact_photo_regular")
        await safe_send_photo(
            bot, user_id, profile.photo_file_id,
            caption=t(_caption_key, req_lang),
            reply_markup=kb_for_photo,
            label="confirm_pay_photo",
        )

    # Геоточка (если есть) — всегда последняя
    if has_loc:
        try:
            await bot.send_location(
                user_id,
                latitude=profile.location_lat,
                longitude=profile.location_lon,
                reply_markup=kb_for_loc,
            )
        except Exception as _e:
            logger.debug("send_location failed: %s", _e)

    if profile.user_id and profile.user_id != user_id:
        owner_lang = "ru"
        try:
            owner = await session.get(User, profile.user_id)
            owner_lang = owner.language.value if owner and owner.language else "ru"
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        if owner_lang == "uz":
            owner_msg = (
                f"💌 <b>Sizning kontaktingiz ulashildi!</b>\n\n"
                f"🔖 {display_id}\n\n"
                f"Jiddiy oila anketangizga qiziqdi.\n"
                f"Qo'ng'iroqni kuting! 🤝"
            )
        else:
            owner_msg = (
                f"💌 <b>Вашим контактом поделились!</b>\n\n"
                f"🔖 {display_id}\n\n"
                f"Серьёзная семья заинтересовалась.\n"
                f"Ждите звонка! 🤝"
            )
        await safe_send_message(bot, profile.user_id, owner_msg, parse_mode="HTML", label="confirm_pay_owner_notify")

    try:
        from sqlalchemy import update
        await session.execute(
            update(ContactRequest)
            .where(
                ContactRequest.display_id == req_number,
                ContactRequest.status == RequestStatus.PENDING,
            )
            .values(status=RequestStatus.CONTACT_GIVEN)
        )
        await session.commit()
    except Exception as _e:
        logger.debug("ignored: %s", _e)

    try:
        mark = (
            f"\n\n✅ <b>КОНТАКТ ПЕРЕДАН</b>\n"
            f"📋 #{req_number}\n"
            f"🔖 {display_id}\n"
            f"👤 ID: <code>{user_id}</code>"
        )
        if callback.message.caption is not None:
            await callback.message.edit_caption(
                caption=(callback.message.caption or "") + mark,
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                (callback.message.text or "") + mark,
                parse_mode="HTML",
            )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("✅ Контакт передан!")


@router.callback_query(F.data.startswith("reject_pay:"))
async def reject_payment(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Оператор не подтвердил оплату — уведомляем пользователя."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return

    parts = callback.data.split(":")
    try:
        user_id = int(parts[1])
        profile_id = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return
    req_number = parts[3] if len(parts) > 3 else "—"

    retry_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📸 Отправить скриншот снова",
            callback_data=f"send_screenshot:{profile_id}:{req_number}",
        )],
        [InlineKeyboardButton(
            text="💬 Задать вопрос",
            callback_data=f"ask_op:{profile_id}",
        )],
    ])

    await safe_send_message(
        bot,
        user_id,
        (
            f"❌ Оплата не подтверждена.\n\n"
            f"📋 #{req_number}\n\n"
            f"Проверьте правильность\n"
            f"реквизитов и попробуйте снова."
        ),
        reply_markup=retry_kb,
        parse_mode="HTML",
        label="reject_payment_user",
    )

    try:
        mark = f"\n\n❌ Оплата #{req_number} не подтверждена"
        if callback.message.caption is not None:
            await callback.message.edit_caption(
                caption=(callback.message.caption or "") + mark,
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                (callback.message.text or "") + mark,
            )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("❌ Отклонено")



# ══════════════════════════════════════════════════════════
#  /requests — активные запросы контакта с навигацией
# ══════════════════════════════════════════════════════════

async def _active_requests(session: AsyncSession) -> list:
    """Все запросы в статусе PENDING, новые сверху."""
    res = await session.execute(
        select(ContactRequest)
        .where(ContactRequest.status == RequestStatus.PENDING)
        .order_by(ContactRequest.created_at.desc())
    )
    return res.scalars().all()


async def _render_requests_list(target_message: Message, session: AsyncSession, *, edit: bool = False):
    """Отрисовать список активных запросов — в новое сообщение или edit_text."""
    requests = await _active_requests(session)

    if not requests:
        text = "📋 Активных запросов нет."
        try:
            if edit:
                await target_message.edit_text(text)
            else:
                await target_message.answer(text)
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        return

    text = f"📋 <b>Активные запросы ({len(requests)}):</b>"
    buttons: list[list[InlineKeyboardButton]] = []
    for req in requests:
        try:
            profile = await session.get(Profile, req.target_profile_id)
            p_name = profile.name if profile else "—"
            # User.username не хранится в БД — показываем только ID
            username = f"ID:{req.requester_user_id}"
            req_id = req.display_id or f"ЗАП-{req.id}"
            label = f"📋 #{req_id} · {username} · {p_name}"
            if len(label.encode("utf-8")) > 60:
                label = label[:55] + "…"
            buttons.append([InlineKeyboardButton(
                text=label, callback_data=f"view_req:{req.id}:0",
            )])
        except Exception as e:
            logger.error(f"render request {req.id} failed: {e}", exc_info=True)
            continue

    if not buttons:
        try:
            if edit:
                await target_message.edit_text("📋 Активных запросов нет.")
            else:
                await target_message.answer("📋 Активных запросов нет.")
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        return

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    try:
        if edit:
            await target_message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        else:
            await target_message.answer(text, reply_markup=kb, parse_mode="HTML")
    except Exception as _e:
        logger.debug("ignored: %s", _e)


@router.message(Command("requests"))
async def cmd_requests(message: Message, session: AsyncSession):
    """Список активных запросов контакта."""
    if not is_moderator(message.from_user.id):
        return
    await _render_requests_list(message, session, edit=False)


@router.callback_query(F.data == "requests:list")
async def requests_list_back(callback: CallbackQuery, session: AsyncSession):
    """Вернуться к списку из детального вида."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    await _render_requests_list(callback.message, session, edit=True)
    await callback.answer()


@router.callback_query(F.data.startswith("view_req:"))
async def view_request(callback: CallbackQuery, session: AsyncSession):
    """Детальный вид запроса + навигация prev/next."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return

    parts = callback.data.split(":")
    try:
        req_id = int(parts[1])
        index = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    requests = await _active_requests(session)
    total = len(requests)
    if total == 0:
        try:
            await callback.message.edit_text("📋 Активных запросов нет.")
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        await callback.answer()
        return

    # Ищем запрос по id — индекс в актуальном списке
    current_index = None
    req = None
    for i, r in enumerate(requests):
        if r.id == req_id:
            req = r
            current_index = i
            break
    # fallback: если запрос уже обработан и исчез из PENDING — берём по индексу
    if req is None:
        current_index = max(0, min(index, total - 1))
        req = requests[current_index]

    profile = await session.get(Profile, req.target_profile_id)
    # User.username не хранится в БД — показываем только ID
    username = f"ID:{req.requester_user_id}"
    req_number = req.display_id or f"ЗАП-{req.id}"

    # Статус
    status_raw = req.status.value if hasattr(req.status, "value") else req.status
    status_map = {
        "pending": "⏳ Ожидает обработки",
        "talking": "💬 В диалоге",
        "contact_given": "✅ Контакт передан",
        "rejected": "❌ Отклонён",
    }
    status = status_map.get(status_raw, status_raw or "—")

    # Профиль: аккуратно извлекаем значения
    import datetime
    if profile:
        age = (datetime.datetime.now().year - profile.birth_year) if profile.birth_year else "?"
        is_male = profile.profile_type == ProfileType.SON
        p_display = profile.display_id or "—"
        p_name = profile.name or "—"
        p_city = profile.city or "—"
        p_edu = education_label(profile.education.value if profile.education else None, "ru")
        p_rel = religiosity_label(profile.religiosity.value if profile.religiosity else None, "ru")
        p_mar = marital_label(profile.marital_status.value if profile.marital_status else None, is_male, "ru")
        p_occ = occupation_label(profile.occupation, "ru")
    else:
        age, p_display, p_name, p_city, p_edu, p_rel, p_mar, p_occ = ("?",) + ("—",) * 7

    text = (
        f"📋 <b>ЗАПРОС #{req_number}</b>\n"
        f"{current_index + 1} из {total}\n\n"
        f"КТО ИЩЕТ:\n"
        f"👤 {username}\n"
        f"ID: <code>{req.requester_user_id}</code>\n\n"
        f"НА КОГО:\n"
        f"🔖 {p_display}\n"
        f"🪪 {p_name} · {age} · {p_city}\n"
        f"🎓 {p_edu} · 💼 {p_occ}\n"
        f"🕌 {p_rel} · 💍 {p_mar}\n\n"
        f"Статус: {status}"
    )

    buttons: list[list[InlineKeyboardButton]] = [
        [InlineKeyboardButton(
            text="💬 Ответить",
            callback_data=f"op_reply:{req.requester_user_id}:{req.target_profile_id}:{req_number}",
        )],
        [InlineKeyboardButton(
            text="📤 Отправить реквизиты",
            callback_data=f"op_send_req:{req.requester_user_id}:{req.target_profile_id}:{req_number}",
        )],
        [InlineKeyboardButton(
            text="❌ Отклонить",
            callback_data=f"op_reject:{req.requester_user_id}:{req.target_profile_id}:{req_number}",
        )],
    ]

    # Навигация
    nav: list[InlineKeyboardButton] = []
    if current_index > 0:
        prev_req = requests[current_index - 1]
        nav.append(InlineKeyboardButton(
            text="⬅️ Предыдущий",
            callback_data=f"view_req:{prev_req.id}:{current_index - 1}",
        ))
    if current_index < total - 1:
        next_req = requests[current_index + 1]
        nav.append(InlineKeyboardButton(
            text="➡️ Следующий",
            callback_data=f"view_req:{next_req.id}:{current_index + 1}",
        ))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(
        text="🔙 К списку",
        callback_data="requests:list",
    )])

    try:
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
            parse_mode="HTML",
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


# ══════════════════════════════════════════════════════════
#  /vip — VIP-заявки: список, просмотр, подтверждение/отклонение
# ══════════════════════════════════════════════════════════


async def _pending_vip_requests(session: AsyncSession) -> list[VipRequest]:
    result = await session.execute(
        select(VipRequest)
        .where(VipRequest.status == VipRequestStatus.PENDING)
        .order_by(VipRequest.created_at.asc())
    )
    return list(result.scalars().all())


async def _render_vip_list(msg_or_cb, session: AsyncSession, edit: bool):
    reqs = await _pending_vip_requests(session)
    text = f"⭐ <b>VIP-заявки</b>\nВ очереди: {len(reqs)}"
    kb = vip_mod_list_kb(reqs)
    target = msg_or_cb.message if hasattr(msg_or_cb, "message") else msg_or_cb
    try:
        if edit:
            await target.edit_text(text, reply_markup=kb)
        else:
            await target.answer(text, reply_markup=kb)
    except Exception as _e:
        logger.debug("ignored: %s", _e)


@router.message(Command("vip"))
async def cmd_vip(message: Message, session: AsyncSession):
    """Список PENDING VIP-заявок."""
    if not is_moderator(message.from_user.id):
        return
    await _render_vip_list(message, session, edit=False)


@router.callback_query(F.data == "vipmod:list")
async def vipmod_list_back(callback: CallbackQuery, session: AsyncSession):
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    await _render_vip_list(callback, session, edit=True)
    await callback.answer()


@router.callback_query(F.data == "noop")
async def _noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("vipmod:view:"))
async def vipmod_view(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Карточка VIP-заявки."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    try:
        req_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    req = await session.get(VipRequest, req_id)
    if not req:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    profile = await session.get(Profile, req.profile_id)
    p_display = profile.display_id if profile else "—"
    p_name = profile.name if profile else "—"

    method_label = (
        t("vip_method_self_label", "ru")
        if req.payment_method == VipPaymentMethod.SELF
        else t("vip_method_moderator_label", "ru")
    )
    price_str = f"{req.amount:,} сум".replace(",", " ")

    text = (
        f"⭐ <b>{req.display_id or '—'}</b>\n\n"
        f"👤 user_id: <code>{req.user_id}</code>\n"
        f"🔖 Анкета: {p_display}\n"
        f"🪪 {p_name}\n"
        f"📅 Срок: {req.days} дн.\n"
        f"💰 Сумма: {price_str}\n"
        f"💳 Способ: {method_label}"
    )

    kb = vip_mod_card_kb(req.id)
    try:
        if req.payment_method == VipPaymentMethod.SELF and req.screenshot_file_id:
            # Скриншот + текст — отдельным сообщением, карточка ниже
            await callback.message.edit_text(text, reply_markup=kb)
            try:
                await callback.message.answer_photo(
                    photo=req.screenshot_file_id,
                    caption=f"📸 Скриншот: {req.display_id}",
                )
            except Exception as _e:
                logger.debug("ignored: %s", _e)
        else:
            await callback.message.edit_text(text, reply_markup=kb)
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


@router.callback_query(F.data.startswith("vipmod:confirm:"))
async def vipmod_confirm(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Подтвердить VIP-заявку: опубликовать анкету (если PENDING/PAUSED) и активировать VIP."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    try:
        req_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    req = await session.get(VipRequest, req_id)
    if not req or req.status != VipRequestStatus.PENDING:
        await callback.answer("Заявка уже обработана", show_alert=True)
        return

    profile = await session.get(Profile, req.profile_id)
    if not profile:
        await callback.answer("Анкета не найдена", show_alert=True)
        return

    now = datetime.now()
    req.status = VipRequestStatus.CONFIRMED
    req.confirmed_at = now

    if profile.status in (ProfileStatus.PENDING, ProfileStatus.PAUSED):
        profile.status = ProfileStatus.PUBLISHED
        profile.is_active = True
        if not profile.published_at:
            profile.published_at = now
    profile.vip_status = VipStatus.ACTIVE
    profile.vip_expires_at = now + timedelta(days=req.days)

    await session.commit()
    audit(
        "vip_request_confirmed",
        actor=f"mod:{callback.from_user.id}",
        target=f"user:{req.user_id}",
        vip_req_id=req.id,
        display_id=req.display_id,
        profile_id=profile.id,
        days=req.days,
        amount=req.amount,
        expires_at=profile.vip_expires_at.isoformat(),
    )

    # Язык юзера для уведомления
    user_result = await session.execute(select(User).where(User.id == req.user_id))
    user = user_result.scalar_one_or_none()
    user_lang = user.language.value if user and user.language else "ru"

    await safe_send_message(
        bot,
        req.user_id,
        t(
            "vip_confirmed_user", user_lang,
            display_id=profile.display_id or "—",
            expires_at=profile.vip_expires_at.strftime("%d.%m.%Y"),
        ),
        label="vip_confirmed_user",
    )

    try:
        await callback.message.edit_text(
            f"✅ <b>{req.display_id}</b> подтверждена. VIP до {profile.vip_expires_at.strftime('%d.%m.%Y')}.",
            reply_markup=vip_mod_card_kb(req.id),
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("✅ Подтверждено")


@router.callback_query(F.data.startswith("vipmod:reject:"))
async def vipmod_reject_confirm(callback: CallbackQuery, session: AsyncSession):
    """Шаг 1: показать подтверждение отклонения VIP-заявки."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    try:
        req_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    req = await session.get(VipRequest, req_id)
    if not req or req.status != VipRequestStatus.PENDING:
        await callback.answer("Заявка уже обработана", show_alert=True)
        return

    prompt = (
        f"⚠️ Отклонить VIP-заявку <b>{req.display_id or req.id}</b>?\n\n"
        f"Пользователь не получит VIP.\n"
        f"Revert — только через SQL."
    )
    try:
        await callback.message.edit_text(
            prompt,
            reply_markup=confirmation_kb(
                yes_cb=f"vipmod:reject_yes:{req.id}",
                no_cb="confirm:cancel",
            ),
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


@router.callback_query(F.data.startswith("vipmod:reject_yes:"))
async def vipmod_reject_do(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Шаг 2: фактическое отклонение VIP-заявки (после подтверждения)."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    try:
        req_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    req = await session.get(VipRequest, req_id)
    if not req or req.status != VipRequestStatus.PENDING:
        await callback.answer("Заявка уже обработана", show_alert=True)
        return

    req.status = VipRequestStatus.REJECTED
    await session.commit()
    audit(
        "vip_request_rejected",
        actor=f"mod:{callback.from_user.id}",
        target=f"user:{req.user_id}",
        vip_req_id=req.id,
        display_id=req.display_id,
    )

    user_result = await session.execute(select(User).where(User.id == req.user_id))
    user = user_result.scalar_one_or_none()
    user_lang = user.language.value if user and user.language else "ru"

    await safe_send_message(
        bot,
        req.user_id,
        t(
            "vip_rejected_user", user_lang,
            display_id=req.display_id or "—",
            moderator=config.moderator_tashkent,
        ),
        label="vip_rejected_user",
    )

    try:
        await callback.message.edit_text(
            f"❌ <b>{req.display_id}</b> отклонена.",
            reply_markup=vip_mod_card_kb(req.id),
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("❌ Отклонено")


# ── «💬 Ответить» на VIP-вопрос пользователя (Путь Б) ──
@router.callback_query(F.data.startswith("vipmod:reply:"))
async def vipmod_reply_start(callback: CallbackQuery, state: FSMContext):
    """Модератор жмёт «💬 Ответить» под VIP-вопросом — ждём текст ответа."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    try:
        req_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    await state.update_data(vip_reply_req_id=req_id)
    await state.set_state(VipModReplyStates.awaiting_reply)
    try:
        await callback.message.answer(f"💬 Введите ответ по VIP-заявке #{req_id}:")
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


@router.message(VipModReplyStates.awaiting_reply, F.text)
async def vipmod_reply_send(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    """Модератор прислал ответ — пересылаем пользователю и показываем after_reply_kb."""
    if not is_moderator(message.from_user.id):
        return

    data = await state.get_data()
    req_id = data.get("vip_reply_req_id")
    if not req_id:
        await state.set_state(None)
        return

    req = await session.get(VipRequest, req_id)
    if not req:
        await state.set_state(None)
        await message.answer("⚠️ Заявка не найдена.")
        return

    # Язык пользователя
    user_result = await session.execute(select(User).where(User.id == req.user_id))
    user = user_result.scalar_one_or_none()
    user_lang = user.language.value if user and user.language else "ru"

    reply_text = (message.text or "").strip()
    if not reply_text:
        return

    ok = await safe_send_message(
        bot,
        req.user_id,
        t(
            "vip_reply_received", user_lang,
            display_id=req.display_id or "—",
            text=reply_text,
        ),
        reply_markup=vip_after_reply_kb(req.profile_id, req.days, user_lang),
        label="vip_reply_received",
    )

    back_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🔙 К списку VIP", callback_data="vipmod:list"),
    ]])
    await message.answer(
        f"✅ Ответ отправлен по {req.display_id or req_id}"
        if ok else
        f"⚠️ Не удалось отправить ответ по {req.display_id or req_id}",
        reply_markup=back_kb,
    )
    await state.set_state(None)


# ══════════════════════════════════════════════════════════
#  /reset — только модератор Ташкент (config.mod_tashkent_id)
# ══════════════════════════════════════════════════════════


async def _delete_profile_cascade(session: AsyncSession, profile: Profile) -> None:
    """Удалить Profile со всеми связанными записями. Commit — снаружи."""
    pid = profile.id
    await session.execute(delete(Favorite).where(Favorite.profile_id == pid))
    await session.execute(delete(ContactRequest).where(ContactRequest.target_profile_id == pid))
    await session.execute(delete(Payment).where(Payment.profile_id == pid))
    await session.execute(delete(VipRequest).where(VipRequest.profile_id == pid))
    await session.execute(delete(Complaint).where(Complaint.profile_id == pid))
    await session.execute(delete(Meeting).where(Meeting.profile_id == pid))
    await session.execute(delete(Feedback).where(Feedback.profile_id == pid))
    await session.execute(delete(Requirement).where(Requirement.profile_id == pid))
    await session.execute(delete(Profile).where(Profile.id == pid))


@router.message(Command("reset"))
async def cmd_reset(message: Message, session: AsyncSession):
    """/reset <id> или /reset all — только для модератора Ташкент."""
    if message.from_user.id != config.mod_tashkent_id:
        return

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await message.answer(
            "Использование:\n"
            "<code>/reset &lt;id&gt;</code> — удалить одну анкету (display_id или числовой ID)\n"
            "<code>/reset all</code> — удалить все анкеты (с подтверждением)"
        )
        return

    arg = parts[1].strip()

    if arg.lower() == "all":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, всё удалить", callback_data="reset:confirm_all")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="reset:cancel")],
        ])
        await message.answer(
            "⚠️ <b>Удалить ВСЕ анкеты?</b>\n\n"
            "Будут удалены все Profile, Requirement, Favorite,\n"
            "ContactRequest, Payment, VipRequest, Complaint,\n"
            "Meeting, Feedback.\n\n"
            "Пользователи (таблица users) остаются.\n"
            "Действие необратимо.",
            reply_markup=kb,
        )
        return

    # Поиск по display_id (с '#' или без), потом по числовому ID
    profile: Profile | None = None
    candidates = [arg, arg.lstrip("#"), f"#{arg.lstrip('#')}"]
    for cand in candidates:
        res = await session.execute(select(Profile).where(Profile.display_id == cand))
        profile = res.scalar_one_or_none()
        if profile:
            break
    if profile is None and arg.isdigit():
        profile = await session.get(Profile, int(arg))

    if profile is None:
        await message.answer(f"❌ Анкета не найдена: <code>{arg}</code>")
        return

    # Показать подтверждение — фактическое удаление в reset:confirm_one:<id>
    display_id = profile.display_id or f"id={profile.id}"
    name = profile.name or "—"
    age = ""
    if profile.birth_year:
        try:
            from datetime import datetime as _dt
            age = f", {_dt.now().year - profile.birth_year}"
        except Exception:
            pass

    await message.answer(
        f"⚠️ Удалить анкету <b>{display_id}</b> ({name}{age}) навсегда?\n\n"
        f"Будут стёрты: анкета, избранные, запросы контакта, оплаты,\n"
        f"VIP-заявки, жалобы, встречи, отзывы, требования.\n\n"
        f"Действие необратимо.",
        reply_markup=confirmation_kb(
            yes_cb=f"reset:confirm_one:{profile.id}",
            no_cb="reset:cancel",
        ),
    )


@router.callback_query(F.data.startswith("reset:confirm_one:"))
async def reset_confirm_one(callback: CallbackQuery, session: AsyncSession):
    """Удалить одну анкету — после подтверждения. Только модератор Ташкент."""
    if callback.from_user.id != config.mod_tashkent_id:
        await callback.answer("⛔")
        return
    try:
        profile_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.answer("❌")
        return

    profile = await session.get(Profile, profile_id)
    if profile is None:
        try:
            await callback.message.edit_text("❌ Анкета не найдена — возможно, уже удалена.")
        except Exception as _e:
            logger.debug("ignored: %s", _e)
        await callback.answer()
        return

    display_id = profile.display_id or f"id={profile.id}"
    name = profile.name or "—"
    owner_user_id = profile.user_id

    await _delete_profile_cascade(session, profile)
    await session.commit()

    logger.info(
        "reset by mod %s: deleted profile %s owned by user %s",
        callback.from_user.id, display_id, owner_user_id,
    )
    try:
        await callback.message.edit_text(f"✅ Удалено: <b>{display_id}</b> ({name})")
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("✅ Удалено")


@router.callback_query(F.data == "reset:confirm_all")
async def reset_confirm_all(callback: CallbackQuery, session: AsyncSession):
    """Удалить все анкеты + связанные данные. Пользователей не трогаем."""
    if callback.from_user.id != config.mod_tashkent_id:
        await callback.answer("⛔")
        return

    # Считаем до удаления — чтобы дать отчёт
    counts = {}
    for model, key in (
        (Profile, "профилей"), (VipRequest, "VIP-заявок"),
        (ContactRequest, "контакт-запросов"), (Payment, "платежей"),
        (Favorite, "избранных"), (Complaint, "жалоб"),
        (Meeting, "встреч"), (Feedback, "отзывов"), (Requirement, "требований"),
    ):
        r = await session.execute(select(func.count(model.id)))
        counts[key] = r.scalar() or 0

    # Удаляем в правильном порядке
    await session.execute(delete(Favorite))
    await session.execute(delete(ContactRequest))
    await session.execute(delete(Payment))
    await session.execute(delete(VipRequest))
    await session.execute(delete(Complaint))
    await session.execute(delete(Meeting))
    await session.execute(delete(Feedback))
    await session.execute(delete(Requirement))
    await session.execute(delete(Profile))
    await session.commit()

    logger.info("reset ALL by mod %s: %s", callback.from_user.id, counts)

    summary_lines = [f"{v} {k}" for k, v in counts.items() if v > 0]
    summary = ", ".join(summary_lines) if summary_lines else "ничего не было"
    try:
        await callback.message.edit_text(
            f"✅ Удалено: {summary}.\n\n"
            f"Следующая VIP-заявка начнётся с <b>VIP-001</b>."
        )
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer("✅ Готово")


@router.callback_query(F.data == "reset:cancel")
async def reset_cancel(callback: CallbackQuery):
    if callback.from_user.id != config.mod_tashkent_id:
        await callback.answer("⛔")
        return
    try:
        await callback.message.edit_text("❌ Отменено.")
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()


# ══════════════════════════════════════════════════════════
#  Общий cancel для confirmation_kb — замена карточки на «❌ Отменено»
# ══════════════════════════════════════════════════════════

@router.callback_query(F.data == "confirm:cancel")
async def confirm_cancel(callback: CallbackQuery):
    """Общий cancel для подтверждений критичных действий."""
    if not is_moderator(callback.from_user.id):
        await callback.answer("⛔")
        return
    try:
        await callback.message.edit_text("❌ Отменено.")
    except Exception as _e:
        logger.debug("ignored: %s", _e)
    await callback.answer()
