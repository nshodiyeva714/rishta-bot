"""Шаг 0 — Юридическое согласие + Шаг 1 — Выбор языка.

Порядок по ТЗ:
  /start → consent_general → consent_special → выбор языка → главное меню
"""

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
    """Команда /start — всегда показываем приветствие или главное меню."""
    await state.clear()

    result = await session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()

    if user and user.consent_general and user.consent_special:
        # Пользователь уже зарегистрирован — показываем главное меню
        lang = user.language.value if user.language else "ru"
        await message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))
        return

    if user and user.consent_general and not user.consent_special:
        # Общее согласие было, спецкатегории — нет
        await message.answer(
            t("consent_special", "ru"),
            reply_markup=consent_special_kb("ru"),
        )
        await state.set_state(ConsentStates.special)
        return

    # Новый пользователь — начинаем с согласия (Шаг 0)
    await message.answer(
        t("consent_general", "ru"),
        reply_markup=consent_general_kb("ru"),
    )
    await state.set_state(ConsentStates.general)


@router.callback_query(F.data == "consent:general:yes", ConsentStates.general)
async def consent_general_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пользователь принял общее согласие — переходим к спецкатегориям."""
    result = await session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(id=callback.from_user.id)
        session.add(user)

    user.consent_general = True
    await session.commit()

    await callback.message.edit_text(
        t("consent_special", "ru"),
        reply_markup=consent_special_kb("ru"),
    )
    await state.set_state(ConsentStates.special)
    await callback.answer()


@router.callback_query(F.data == "consent:general:no", ConsentStates.general)
async def consent_general_no(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(t("consent_declined", "ru"))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "consent:special:yes", ConsentStates.special)
async def consent_special_yes(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Пользователь дал спецсогласие — переходим к выбору языка (Шаг 1)."""
    result = await session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    if user:
        user.consent_special = True
        await session.commit()

    # Шаг 1 — выбор языка
    await callback.message.edit_text(
        t("welcome", "ru"),
        reply_markup=lang_kb(),
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "consent:special:no", ConsentStates.special)
async def consent_special_no(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(t("consent_declined", "ru"))
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def choose_language(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Шаг 1 — пользователь выбрал язык → главное меню."""
    lang = callback.data.split(":")[1]

    result = await session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            id=callback.from_user.id,
            language=Language(lang),
            consent_general=True,
            consent_special=True,
        )
        session.add(user)
    else:
        user.language = Language(lang)

    await session.commit()

    # Переходим в главное меню
    await callback.message.edit_text(
        t("main_menu", lang),
        reply_markup=main_menu_kb(lang),
    )
    await callback.answer()
