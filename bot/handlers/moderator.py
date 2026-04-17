"""Шаг 9 — Модератор: проверка анкет и оплат, ответ пользователям, /ankety, /stats."""

from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Profile, ProfileStatus, Payment, PaymentStatus, User, VipStatus
from bot.states import ModeratorReplyStates
from bot.texts import t
from bot.config import config, is_moderator
from bot.keyboards.inline import mod_review_kb, mod_found_kb, mod_vip_duration_kb
from bot.utils.helpers import format_full_anketa

router = Router()


# ── /ankety — список анкет на модерации ──
@router.message(Command("ankety"))
async def cmd_ankety(message: Message, session: AsyncSession, bot: Bot):
    if not is_moderator(message.from_user.id):
        await message.answer("⛔ Только для модераторов")
        return

    result = await session.execute(
        select(Profile).where(Profile.status == ProfileStatus.PENDING).order_by(Profile.created_at)
    )
    profiles = result.scalars().all()

    if not profiles:
        await message.answer("✅ Нет анкет на модерации.")
        return

    await message.answer(f"📋 Анкет на модерации: <b>{len(profiles)}</b>")

    for p in profiles[:20]:  # макс 20 чтобы не спамить
        age = datetime.now().year - p.birth_year if p.birth_year else "?"
        icon = "👦" if p.profile_type and p.profile_type.value == "son" else "👧"
        text = (
            f"🔖 {p.display_id or '—'}\n"
            f"{icon} {p.name or '—'} · {age}\n"
            f"📍 {p.city or '—'}\n"
            f"📞 {p.parent_phone or '—'}\n"
            f"📸 {'Есть' if p.photo_file_id else 'Нет'}"
        )
        await message.answer(text, reply_markup=mod_review_kb(p.id))


# ── /stats — статистика платформы ──
@router.message(Command("stats"))
async def cmd_stats(message: Message, session: AsyncSession):
    if not is_moderator(message.from_user.id):
        await message.answer("⛔ Только для модераторов")
        return

    total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
    total_profiles = (await session.execute(select(func.count(Profile.id)))).scalar() or 0
    pending = (await session.execute(
        select(func.count(Profile.id)).where(Profile.status == ProfileStatus.PENDING)
    )).scalar() or 0
    published = (await session.execute(
        select(func.count(Profile.id)).where(Profile.status == ProfileStatus.PUBLISHED)
    )).scalar() or 0
    rejected = (await session.execute(
        select(func.count(Profile.id)).where(Profile.status == ProfileStatus.REJECTED)
    )).scalar() or 0
    paused = (await session.execute(
        select(func.count(Profile.id)).where(Profile.status == ProfileStatus.PAUSED)
    )).scalar() or 0
    total_payments = (await session.execute(
        select(func.count(Payment.id)).where(Payment.status == PaymentStatus.CONFIRMED)
    )).scalar() or 0

    text = (
        "📊 <b>Статистика платформы</b>\n\n"
        f"👥 Пользователей: {total_users}\n"
        f"📋 Всего анкет: {total_profiles}\n\n"
        f"⏳ На модерации: {pending}\n"
        f"✅ Опубликовано: {published}\n"
        f"❌ Отклонено: {rejected}\n"
        f"⏸ На паузе: {paused}\n\n"
        f"💰 Подтверждённых оплат: {total_payments}"
    )
    await message.answer(text)


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

    # Уведомляем пользователя
    try:
        lang = "ru"  # По умолчанию; можно достать из User
        from sqlalchemy import select
        from bot.db.models import User
        result = await session.execute(select(User).where(User.id == profile.user_id))
        user = result.scalar_one_or_none()
        if user and user.language:
            lang = user.language.value

        await bot.send_message(
            profile.user_id,
            t("mod_profile_published", lang, display_id=profile.display_id),
        )
    except Exception:
        pass

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

    try:
        lang = "ru"
        from sqlalchemy import select
        from bot.db.models import User
        result = await session.execute(select(User).where(User.id == profile.user_id))
        user = result.scalar_one_or_none()
        if user and user.language:
            lang = user.language.value

        await bot.send_message(
            profile.user_id,
            t("mod_profile_rejected", lang, display_id=profile.display_id),
        )
    except Exception:
        pass

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

    try:
        await bot.send_message(
            profile.user_id,
            "📸 Модератор отклонил фото в анкете " + (profile.display_id or "") +
            ". Пожалуйста, загрузите другое фото через «Редактировать анкету».",
        )
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + "\n\n📸 ФОТО ОТКЛОНЕНО",
    )
    await callback.answer("📸 Фото отклонено")


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
async def mod_reject_payment(callback: CallbackQuery, session: AsyncSession, bot: Bot):
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

    try:
        await bot.send_message(
            payment.user_id,
            "❌ Оплата отклонена модератором. Свяжитесь с модератором для уточнения.",
        )
    except Exception:
        pass

    await callback.message.edit_text(
        callback.message.text + "\n\n❌ ОПЛАТА ОТКЛОНЕНА",
    )
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

    try:
        header = "💬 <b>Ответ от модератора:</b>\n\n"
        await bot.send_message(user_id, header + (message.text or ""))
        if message.photo:
            await bot.send_photo(user_id, message.photo[-1].file_id)
        if message.document:
            await bot.send_document(user_id, message.document.file_id)
        if message.voice:
            await bot.send_voice(user_id, message.voice.file_id)
        await message.answer(f"✅ Ответ отправлен пользователю (ID: {user_id})")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")

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

    # Отправляем
    try:
        if profile.photo_file_id:
            if len(full_text) <= 1024:
                await bot.send_photo(
                    message.from_user.id,
                    profile.photo_file_id,
                    caption=full_text,
                    reply_markup=kb,
                )
            else:
                await bot.send_photo(message.from_user.id, profile.photo_file_id)
                await message.answer(full_text, reply_markup=kb)
        else:
            await message.answer(full_text, reply_markup=kb)
    except Exception:
        if len(full_text) > 4096:
            await message.answer(full_text[:4096])
            await message.answer(full_text[4096:], reply_markup=kb)
        else:
            await message.answer(full_text, reply_markup=kb)


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
            try:
                msg = (
                    f"⏸ Sizning anketangiz <b>{display_id}</b> moderator tomonidan pauzaga qo'yildi."
                    if owner_lang == "uz" else
                    f"⏸ Ваша анкета <b>{display_id}</b> поставлена на паузу модератором."
                )
                await bot.send_message(owner_id, msg)
            except Exception:
                pass

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
            try:
                msg = (
                    f"🟢 Sizning anketangiz <b>{display_id}</b> yana faol!"
                    if owner_lang == "uz" else
                    f"🟢 Ваша анкета <b>{display_id}</b> снова активна!"
                )
                await bot.send_message(owner_id, msg)
            except Exception:
                pass

    elif action == "block":
        profile.status = ProfileStatus.REJECTED
        profile.is_active = False
        await session.commit()

        await callback.message.edit_text(
            f"❌ Анкета <b>{display_id}</b> заблокирована.",
        )
        if owner_id:
            try:
                msg = (
                    f"❌ Sizning anketangiz <b>{display_id}</b> moderator tomonidan bloklandi."
                    if owner_lang == "uz" else
                    f"❌ Ваша анкета <b>{display_id}</b> заблокирована модератором."
                )
                await bot.send_message(owner_id, msg)
            except Exception:
                pass

    elif action == "vip_add":
        # Показать выбор срока VIP
        await callback.message.edit_text(
            f"⭐ <b>Присвоить VIP</b>\n\n"
            f"Анкета: <b>{display_id}</b>\n\n"
            f"Выберите срок:",
            reply_markup=mod_vip_duration_kb(profile.id),
        )

    elif action == "vip_remove":
        profile.vip_status = VipStatus.NONE
        profile.vip_expires_at = None
        await session.commit()

        await callback.message.edit_text(
            f"⭐ VIP статус снят с анкеты <b>{display_id}</b>.",
        )
        if owner_id:
            try:
                msg = (
                    f"ℹ️ <b>{display_id}</b> anketangizning VIP maqomi olib tashlandi."
                    if owner_lang == "uz" else
                    f"ℹ️ VIP статус анкеты <b>{display_id}</b> снят."
                )
                await bot.send_message(owner_id, msg)
            except Exception:
                pass

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
        try:
            await bot.send_message(profile.user_id, msg)
        except Exception:
            pass

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
    try:
        result = await session.execute(select(User).where(User.id == profile.user_id))
        user = result.scalar_one_or_none()
        lang = user.language.value if user and user.language else "ru"
        await bot.send_message(profile.user_id, t("mod_profile_published", lang, display_id=profile.display_id))
    except Exception:
        pass

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
