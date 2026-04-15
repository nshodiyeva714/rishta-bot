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
from bot.states import ConsentStates
from bot.texts import t
from bot.keyboards.inline import main_menu_kb, consent_general_kb

router = Router()


@router.message()
async def fallback_handler(message: Message, state: FSMContext, session: AsyncSession):
    """Любое сообщение без активного FSM state — показываем меню или согласие."""
    current_state = await state.get_state()
    if current_state is not None:
        # Есть активный FSM state — не перехватываем (обработает другой хендлер)
        return

    result = await session.execute(select(User).where(User.id == message.from_user.id))
    user = result.scalar_one_or_none()

    if user and user.consent_general and user.consent_special:
        # Зарегистрированный пользователь — главное меню
        lang = user.language.value if user.language else "ru"
        await message.answer(t("main_menu", lang), reply_markup=main_menu_kb(lang))
    else:
        # Новый пользователь — начинаем с согласия (Шаг 0)
        await message.answer(
            t("consent_general", "ru"),
            reply_markup=consent_general_kb("ru"),
        )
        await state.set_state(ConsentStates.general)
