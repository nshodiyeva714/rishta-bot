"""Шаг 0-1 — /start → Язык → Согласие → Главное меню."""

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, Language
from bot.states import ConsentStates
from bot.texts import t
from bot.keyboards.inline import (
    lang_kb,
    consent_general_kb,
    consent_special_kb,
    main_menu_kb,
)
from bot.config import config, is_moderator

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Команда /start — всегда показываем выбор языка."""
    await state.clear()
    await message.answer(
        t("welcome", "ru"),
        reply_markup=lang_kb(),
    )


@router.message(Command("reset"))
async def cmd_reset(message: Message, session: AsyncSession):
    """Полная очистка базы данных — только для модераторов."""
    if not is_moderator(message.from_user.id):
        await message.answer("⛔ Только для модераторов")
        return

    from bot.db.models import (
        Feedback, Meeting, Complaint, ContactRequest, Favorite,
        Payment, Requirement, Profile, User,
    )
    for model in [Feedback, Meeting, Complaint, ContactRequest, Favorite, Payment, Requirement, Profile, User]:
        await session.execute(model.__table__.delete())
    await session.commit()

    await message.answer("✅ База данных полностью очищена. Все анкеты, пользователи и данные удалены.")


@router.message(Command("test"))
async def cmd_test(message: Message, bot: Bot):
    """Проверка связи с модераторами."""
    if not is_moderator(message.from_user.id):
        await message.answer("⛔ Только для модераторов")
        return

    results = []
    checks = [
        ("tashkent", config.mod_tashkent_id),
        ("samarkand", config.mod_samarkand_id),
        ("main", config.main_moderator_id),
        ("chat_id", config.moderator_chat_id),
    ]
    for name, mod_id in checks:
        if not mod_id:
            results.append(f"⚠️ {name}: не настроен")
            continue
        try:
            await bot.send_chat_action(mod_id, "typing")
            results.append(f"✅ {name} (ID: {mod_id}): работает")
        except Exception as e:
            results.append(f"❌ {name} (ID: {mod_id}): {e}")

    await message.answer("🔧 <b>Тест модераторов:</b>\n\n" + "\n".join(results))


# ── Выбор языка → Согласие ──
@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 1 — пользователь выбрал язык → показываем согласие."""
    await state.clear()
    lang = callback.data.split(":")[1]

    result = await session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=callback.from_user.id,
            language=Language(lang),
        )
        session.add(user)
    else:
        user.language = Language(lang)

    await session.commit()

    # Проверяем: если пользователь уже давал согласие — сразу в меню
    if user.consent_general and user.consent_special:
        await callback.message.edit_text(
            t("main_menu", lang),
            reply_markup=main_menu_kb(lang, callback.from_user.id),
        )
    else:
        # Показываем согласие
        await callback.message.edit_text(
            t("consent_general", lang),
            reply_markup=consent_general_kb(lang),
        )
        await state.set_state(ConsentStates.general)
        await state.update_data(lang=lang)

    await callback.answer()


# ── Согласие: общее ──
@router.callback_query(F.data == "consent:general:yes", ConsentStates.general)
async def consent_general_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пользователь согласен с общими условиями → спецсогласие."""
    data = await state.get_data()
    lang = data.get("lang", "ru")

    result = await session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    if user:
        user.consent_general = True
        await session.commit()

    await callback.message.edit_text(
        t("consent_special", lang),
        reply_markup=consent_special_kb(lang),
    )
    await state.set_state(ConsentStates.special)
    await callback.answer()


@router.callback_query(F.data == "consent:general:no", ConsentStates.general)
async def consent_general_no(callback: CallbackQuery, state: FSMContext):
    """Пользователь отказался от условий."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.message.edit_text(t("consent_declined", lang))
    await state.clear()
    await callback.answer()


# ── Согласие: специальное (персональные данные) ──
@router.callback_query(F.data == "consent:special:yes", ConsentStates.special)
async def consent_special_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пользователь дал спецсогласие → главное меню."""
    data = await state.get_data()
    lang = data.get("lang", "ru")

    result = await session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    if user:
        user.consent_special = True
        await session.commit()

    await callback.message.edit_text(
        t("main_menu", lang),
        reply_markup=main_menu_kb(lang, callback.from_user.id),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "consent:special:no", ConsentStates.special)
async def consent_special_no(callback: CallbackQuery, state: FSMContext):
    """Пользователь отказался от спецсогласия."""
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.message.edit_text(t("consent_declined", lang))
    await state.clear()
    await callback.answer()
