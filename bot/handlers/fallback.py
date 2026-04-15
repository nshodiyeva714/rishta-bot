"""Fallback — обработка любых сообщений без активного FSM state.

Если пользователь очистил чат и написал произвольный текст,
показываем главное меню или приглашаем пройти регистрацию.
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User
from bot.texts import t
from bot.keyboards.inline import main_menu_kb, lang_kb

router = Router()


@router.message()
async def fallback_handler(message: Message, state: FSMContext, session: AsyncSession):
    """Любое сообщение без активного FSM state — показываем выбор языка."""
    current_state = await state.get_state()
    if current_state is not None:
        return

    # Всегда показываем выбор языка (Шаг 1)
    await message.answer(
        t("welcome", "ru"),
        reply_markup=lang_kb(),
    )
