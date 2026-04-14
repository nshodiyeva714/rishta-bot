"""Шаг 0 — Юридическое согласие + Шаг 1 — Выбор языка."""

from aiogram import Router, F
from aiogram.filters import CommandStart
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

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Команда /start — проверяем есть ли пользователь, если нет — начинаем с согласия."""
    await state.clear()

    result = await session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()

    if user and user.consent_general and user.consent_special:
        lang = user.language.value if user.language else "ru"
        await message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))
        return

    # Новый пользователь — показываем выбор языка
    await message.answer(
        t("welcome", "ru"),
        reply_markup=lang_kb(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 1 — пользователь выбрал язык."""
    lang = callback.data.split(":")[1]
    await state.update_data(lang=lang)

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

    # Шаг 0 — общее согласие
    await callback.message.edit_text(
        t("consent_general", lang),
        reply_markup=consent_general_kb(lang),
    )
    await state.set_state(ConsentStates.general)
    await callback.answer()


@router.callback_query(F.data == "consent:general:yes", ConsentStates.general)
async def consent_general_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пользователь принял общее согласие — переходим к спецкатегориям."""
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
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.message.edit_text(t("consent_declined", lang))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "consent:special:yes", ConsentStates.special)
async def consent_special_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пользователь дал спецсогласие — переходим в главное меню."""
    data = await state.get_data()
    lang = data.get("lang", "ru")

    result = await session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    if user:
        user.consent_special = True
        await session.commit()

    await callback.message.edit_text(
        t("main_menu", lang),
        reply_markup=main_menu_kb(lang),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "consent:special:no", ConsentStates.special)
async def consent_special_no(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    await callback.message.edit_text(t("consent_declined", lang))
    await state.clear()
    await callback.answer()
