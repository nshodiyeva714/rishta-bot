"""Шаг 16 — Планировщик встречи."""

from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, Meeting, Profile
from bot.states import MeetingStates
from bot.texts import t
from bot.keyboards.inline import main_menu_kb, meeting_skip_kb
from bot.config import config

router = Router()


async def get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


@router.callback_query(F.data == "meeting:skip")
async def meeting_skip(callback: CallbackQuery, session: AsyncSession):
    lang = await get_lang(session, callback.from_user.id)
    await callback.message.edit_text(t("meeting_skip", lang))
    await callback.answer()


@router.message(MeetingStates.date)
async def meeting_date(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")

    # Парсим дату
    text = message.text.strip()
    try:
        date = datetime.strptime(text, "%d.%m.%Y")
    except ValueError:
        error = "❌ Введите дату в формате ДД.ММ.ГГГГ" if lang == "ru" else "❌ Sanani KK.OO.YYYY formatda kiriting"
        await message.answer(error)
        return

    await state.update_data(meeting_date=text)
    await message.answer(t("meeting_time", lang))
    await state.set_state(MeetingStates.time)


@router.message(MeetingStates.time)
async def meeting_time(message: Message, state: FSMContext, session: AsyncSession, bot: Bot):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    date_str = data.get("meeting_date", "")
    time_str = message.text.strip()
    profile_id = data.get("pay_profile_id")

    try:
        meeting_dt = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
    except ValueError:
        error = "❌ Введите время в формате ЧЧ:ММ" if lang == "ru" else "❌ Vaqtni SS:DD formatda kiriting"
        await message.answer(error)
        return

    # Сохраняем встречу
    meeting = Meeting(
        user_id=message.from_user.id,
        profile_id=profile_id or 0,
        meeting_date=meeting_dt,
    )
    session.add(meeting)
    await session.commit()

    # Уведомляем модератора
    if config.moderator_chat_id:
        profile = await session.get(Profile, profile_id) if profile_id else None
        mod_text = (
            f"📅 <b>ЗАПРОС НА ВСТРЕЧУ</b>\n\n"
            f"🔖 Анкета: {profile.display_id if profile else '—'}\n"
            f"От: @{message.from_user.username or '—'}\n"
            f"Дата: {date_str}\n"
            f"Время: {time_str}"
        )
        try:
            await bot.send_message(config.moderator_chat_id, mod_text)
        except Exception:
            pass

    await message.answer(t("meeting_confirmed", lang, date=date_str, time=time_str))
    await state.clear()
