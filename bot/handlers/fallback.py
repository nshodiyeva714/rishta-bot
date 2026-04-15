"""Fallback — обработка необработанных callback и сообщений.

Если callback не обработан ни одним хэндлером — сбрасываем FSM и показываем меню.
Если сообщение без FSM — показываем выбор языка.
"""

import logging
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User
from bot.texts import t
from bot.keyboards.inline import main_menu_kb, lang_kb

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query()
async def fallback_callback(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    """Любой необработанный callback — сбросить FSM, показать меню."""
    logger.warning(f"Необработанный callback: {callback.data} от user {callback.from_user.id}")
    await state.clear()

    # Определяем язык
    result = await session.execute(select(User).where(User.id == callback.from_user.id))
    user = result.scalar_one_or_none()
    lang = user.language.value if user and user.language else "ru"

    try:
        await callback.message.edit_text(
            t("main_menu", lang),
            reply_markup=main_menu_kb(lang, callback.from_user.id),
        )
    except Exception:
        await callback.message.answer(
            t("main_menu", lang),
            reply_markup=main_menu_kb(lang, callback.from_user.id),
        )
    await callback.answer()


@router.message()
async def fallback_handler(message: Message, state: FSMContext, session: AsyncSession):
    """Любое сообщение без активного FSM state — показываем выбор языка."""
    current_state = await state.get_state()
    if current_state is not None:
        return

    await message.answer(
        t("welcome", "ru"),
        reply_markup=lang_kb(),
    )
