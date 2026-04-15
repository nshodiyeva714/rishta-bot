"""Шаг 1 — Выбор языка → Главное меню.

Порядок:
  /start → выбор языка → главное меню (каждый раз с начала)
"""

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, Language
from bot.texts import t
from bot.keyboards.inline import (
    lang_kb,
    main_menu_kb,
)

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: AsyncSession):
    """Команда /start — всегда показываем выбор языка (Шаг 1)."""
    await state.clear()

    # Всегда начинаем с выбора языка
    await message.answer(
        t("welcome", "ru"),
        reply_markup=lang_kb(),
    )


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
