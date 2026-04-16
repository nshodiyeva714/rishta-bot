"""Шаг 17 — Обратная связь после встречи."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import User, Feedback, FeedbackResult
from bot.states import FeedbackStates
from bot.texts import t
from bot.keyboards.inline import feedback_story_kb, main_menu_kb, back_main_kb, add_nav, nav_kb

router = Router()


async def get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


@router.callback_query(F.data.startswith("fb:"))
async def feedback_result(callback: CallbackQuery, state: FSMContext, session: AsyncSession):
    parts = callback.data.split(":")
    result_value = parts[1]
    profile_id = int(parts[2])

    lang = await get_lang(session, callback.from_user.id)

    fb = Feedback(
        user_id=callback.from_user.id,
        profile_id=profile_id,
        result=FeedbackResult(result_value),
    )
    session.add(fb)
    await session.commit()

    if result_value == "nikoh":
        await callback.message.edit_text(
            t("feedback_nikoh", lang),
            reply_markup=add_nav(feedback_story_kb(lang).inline_keyboard, lang, "back:menu"),
        )
        await state.update_data(feedback_profile_id=profile_id, lang=lang)
        await state.set_state(FeedbackStates.story)
    else:
        responses = {
            "talking": "🤝 Отлично! Желаем удачи в общении!" if lang == "ru" else "🤝 Ajoyib! Muloqotda omad!",
            "thinking": "💬 Понятно! Не торопитесь, пусть всё сложится наилучшим образом 🤲" if lang == "ru" else "💬 Tushunarli! Shoshilmang, hammasi yaxshi bo'lsin 🤲",
            "not_matched": "❌ Жаль, что не подошли. Желаем найти свою пару! 🤲" if lang == "ru" else "❌ Mos kelmaganiga afsusdamiz. Juftingizni topishingizni tilaymiz! 🤲",
        }
        text = responses.get(result_value, "Спасибо за отзыв!")
        from aiogram.types import InlineKeyboardMarkup
        await callback.message.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb(lang, show_back=False)),
        )

    await callback.answer()


@router.callback_query(F.data == "story:yes", FeedbackStates.story)
async def story_yes(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    prompt = "Напишите вашу историю (будет опубликована анонимно):" if lang == "ru" else "Tarixingizni yozing (anonim ravishda nashr etiladi):"
    await callback.message.edit_text(prompt, reply_markup=back_main_kb(lang))
    await callback.answer()


@router.message(FeedbackStates.story)
async def story_text(message: Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    profile_id = data.get("feedback_profile_id")
    lang = data.get("lang", "ru")

    # Обновляем последний feedback
    result = await session.execute(
        select(Feedback).where(
            Feedback.user_id == message.from_user.id,
            Feedback.profile_id == profile_id,
        ).order_by(Feedback.id.desc()).limit(1)
    )
    fb = result.scalar_one_or_none()
    if fb:
        fb.story = message.text.strip()
        await session.commit()

    thanks = "Спасибо за вашу историю! Она будет опубликована анонимно в @Rishta_uz 🤲" if lang == "ru" else "Tarixingiz uchun rahmat! U @Rishta_uz da anonim ravishda nashr etiladi 🤲"
    from aiogram.types import InlineKeyboardMarkup
    await message.answer(
        thanks,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb(lang, show_back=False)),
    )
    await state.clear()


@router.callback_query(F.data == "story:no", FeedbackStates.story)
async def story_no(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = "Спасибо! Nikohingiz muborak bo'lsin! 💍🤲" if lang == "ru" else "Rahmat! Nikohingiz muborak bo'lsin! 💍🤲"
    from aiogram.types import InlineKeyboardMarkup
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=nav_kb(lang, show_back=False)),
    )
    await state.clear()
    await callback.answer()
