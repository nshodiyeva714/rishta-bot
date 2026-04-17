"""Анкета — ЭТАП 2: Расширенный профиль (9 вопросов).

Порядок:
  Блок 1 — Семья:    1.Отец → 2.Мать → 3.Братья/Сёстры/Место
  Блок 2 — Личное:   4.Характер → 5.Здоровье → 6.О себе
  Блок 3 — Быт:      7.Жильё → 8.Автомобиль
  Блок 4 — Контакты: 9.Телефон → TG родителей → TG кандидата → Адрес
"""

import logging

from aiogram import Router, F, Bot
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
)
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import QuestionnaireStates
from bot.texts import t
from bot.keyboards.inline import skip_kb, back_kb, main_menu_kb
from bot.db.models import (
    Profile, User,
    Housing, ParentHousing, CarStatus, FamilyPosition,
)

logger = logging.getLogger(__name__)

router = Router()

SEP = "\n\n━━━━━━━━━━━━\n\n"


# ══════════════════════════════════════
# Утилиты
# ══════════════════════════════════════

async def _lang(state: FSMContext) -> str:
    data = await state.get_data()
    return data.get("lang", "ru")


async def _get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


async def _get_profile(session: AsyncSession, profile_id: int, user_id: int):
    profile = await session.get(Profile, profile_id)
    if profile and profile.user_id == user_id:
        return profile
    return None


def ext_progress_bar(current: int, total: int = 9) -> str:
    """Прогресс-бар для Этапа 2."""
    filled = round(current / total * 13)
    empty = 13 - filled
    bar = "▓" * filled + "░" * empty
    pct = round(current / total * 100)
    return f"{bar}  {pct}%"


def build_ext_card(data: dict, lang: str = "ru") -> str:
    """Накопленная карточка Этапа 2."""
    lines = []
    L = lang if lang in ("ru", "uz") else "ru"

    # Базовые данные из Этапа 1
    name = data.get("name")
    age = data.get("age")
    height = data.get("height_cm")
    header = []
    if name:
        header.append(name)
    if age:
        header.append(f"{age} {'лет' if L == 'ru' else 'yosh'}")
    if height:
        header.append(f"{height} {'см' if L == 'ru' else 'sm'}")
    if header:
        lines.append("👤 " + " · ".join(header))

    # Семья
    father = data.get("father_occupation")
    mother = data.get("mother_occupation")
    if father:
        lines.append(f"{'Отец' if L == 'ru' else 'Otasi'}: {father}")
    if mother:
        lines.append(f"{'Мать' if L == 'ru' else 'Onasi'}: {mother}")

    # Братья/сёстры/место
    brothers = data.get("brothers_count")
    sisters = data.get("sisters_count")
    position = data.get("family_position")
    if brothers is not None or sisters is not None:
        fam = []
        if brothers is not None:
            fam.append(f"{brothers} {'бр.' if L == 'ru' else 'aka-uka'}")
        if sisters is not None:
            fam.append(f"{sisters} {'сест.' if L == 'ru' else 'opa-singil'}")
        if position:
            pos_map = {
                "ru": {"first": "старший/ая", "middle": "средний/яя",
                       "last": "младший/ая", "only": "единственный/ая"},
                "uz": {"first": "katta", "middle": "o'rtancha",
                       "last": "kenja", "only": "yagona"},
            }
            fam.append(pos_map[L].get(position, position))
        lines.append(" · ".join(fam))

    # Характер
    char = data.get("character_hobbies")
    if char:
        snippet = char[:40] + ("..." if len(char) > 40 else "")
        lines.append(f"✨ {snippet}")

    # Здоровье
    health = data.get("health_notes")
    if health:
        snippet = health[:40] + ("..." if len(health) > 40 else "")
        lines.append(f"❤️ {snippet}")

    # О себе
    about = data.get("ideal_family_life")
    if about:
        snippet = about[:40] + ("..." if len(about) > 40 else "")
        lines.append(f"💬 {snippet}")

    # Жильё
    house_map = {
        "ru": {"own_house": "Свой дом", "own_apt": "Своя квартира",
               "parents": "С родителями", "rent": "Аренда"},
        "uz": {"own_house": "O'z uyi", "own_apt": "O'z kvartirasi",
               "parents": "Ota-ona bilan", "rent": "Ijara"},
    }
    house = data.get("housing")
    if house:
        lines.append(f"🏠 {house_map[L].get(house, house)}")

    # Автомобиль
    car_map = {
        "ru": {"own": "Личный авто", "family": "Семейный авто", "no": "Нет авто"},
        "uz": {"own": "Shaxsiy avto", "family": "Oilaviy avto", "no": "Avto yo'q"},
    }
    car = data.get("car")
    if car:
        lines.append(f"🚗 {car_map[L].get(car, car)}")

    # Телефон
    phone = data.get("parent_phone")
    if phone:
        lines.append(f"📞 {phone}")

    # Telegram родителей и кандидата
    parent_tg = data.get("parent_telegram")
    if parent_tg:
        lines.append(f"📱 {parent_tg}")

    candidate_tg = data.get("candidate_telegram")
    if candidate_tg:
        lines.append(f"💬 {candidate_tg}")

    # Адрес / геолокация
    address = data.get("address")
    if address:
        lines.append(f"🏠 {address}")
    else:
        location_link = data.get("location_link")
        if location_link:
            lines.append(f"📍 {'Geolokatsiya' if L == 'uz' else 'Геолокация'}")

    if not lines:
        return ""

    return "📋 " + "\n   ".join(lines)


def _with_card(data: dict, lang: str, question_text: str) -> str:
    card = build_ext_card(data, lang)
    return (card + SEP + question_text) if card else question_text


async def _show_question(m_or_cb, state: FSMContext, text: str,
                         reply_markup=None, parse_mode: str = None):
    """Показать вопрос: редактируем последнее сообщение бота.

    Если edit не удаётся — сначала УДАЛЯЕМ старое сообщение, потом
    отправляем новое. На экране всегда только одно актуальное окно.
    """
    if hasattr(m_or_cb, "message"):
        # CallbackQuery — редактируем текущее сообщение
        try:
            await m_or_cb.message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
            await state.update_data(last_bot_msg_id=m_or_cb.message.message_id)
            return
        except Exception:
            # Редактирование не удалось — удаляем старое сообщение бота
            try:
                await m_or_cb.message.delete()
            except Exception:
                pass
        sent = await m_or_cb.message.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
        await state.update_data(last_bot_msg_id=sent.message_id)
        return

    # Message — ищем last_bot_msg_id и редактируем
    data = await state.get_data()
    last_id = data.get("last_bot_msg_id")

    if last_id:
        try:
            await m_or_cb.bot.edit_message_text(
                chat_id=m_or_cb.chat.id,
                message_id=last_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )
            return
        except Exception:
            # Редактирование не удалось — удаляем старое сообщение бота
            try:
                await m_or_cb.bot.delete_message(
                    chat_id=m_or_cb.chat.id,
                    message_id=last_id,
                )
            except Exception:
                pass

    # Отправляем новое сообщение
    sent = await m_or_cb.answer(text, reply_markup=reply_markup, parse_mode=parse_mode)
    await state.update_data(last_bot_msg_id=sent.message_id)


# ══════════════════════════════════════
# СТАРТ ЭТАПА 2
# ══════════════════════════════════════

@router.callback_query(F.data == "ext:start")
async def ext_start(callback: CallbackQuery, state: FSMContext):
    """Старт Этапа 2 — сразу к вопросу 1 (отец)."""
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(1)

    if lang == "uz":
        q_text = f"👨‍💼 1/9-savol\n{bar}\n\nOtasi — nima bilan shug'ullanadi:"
    else:
        q_text = f"👨‍💼 Вопрос 1/9\n{bar}\n\nОтец — чем занимается:"

    full_text = _with_card(data, lang, q_text)
    await _show_question(callback, state, full_text, reply_markup=back_kb(lang))
    await state.set_state(QuestionnaireStates.ext_father)
    await callback.answer()


# ══════════════════════════════════════
# БЛОК 1: СЕМЬЯ
# ══════════════════════════════════════

# ── 1. Отец ──
@router.message(QuestionnaireStates.ext_father)
async def ext_father(message: Message, state: FSMContext):
    await state.update_data(father_occupation=message.text.strip())
    try:
        await message.delete()
    except Exception:
        pass
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(2)

    if lang == "uz":
        q_text = f"👩‍💼 2/9-savol\n{bar}\n\nOnasi — nima bilan shug'ullanadi:"
    else:
        q_text = f"👩‍💼 Вопрос 2/9\n{bar}\n\nМать — чем занимается:"

    full_text = _with_card(data, lang, q_text)
    await _show_question(message, state, full_text, reply_markup=back_kb(lang))
    await state.set_state(QuestionnaireStates.ext_mother)


# ── 2. Мать → 3. Братья ──
def _brothers_kb(lang: str) -> InlineKeyboardMarkup:
    label = "Aka-uka:" if lang == "uz" else "Братьев:"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data="noop")],
        [InlineKeyboardButton(text="0", callback_data="brothers:0"),
         InlineKeyboardButton(text="1", callback_data="brothers:1"),
         InlineKeyboardButton(text="2", callback_data="brothers:2"),
         InlineKeyboardButton(text="3", callback_data="brothers:3"),
         InlineKeyboardButton(text="4+", callback_data="brothers:4")],
    ])


def _sisters_kb(lang: str) -> InlineKeyboardMarkup:
    label = "Opa-singillar:" if lang == "uz" else "Сестёр:"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data="noop")],
        [InlineKeyboardButton(text="0", callback_data="sisters:0"),
         InlineKeyboardButton(text="1", callback_data="sisters:1"),
         InlineKeyboardButton(text="2", callback_data="sisters:2"),
         InlineKeyboardButton(text="3", callback_data="sisters:3"),
         InlineKeyboardButton(text="4+", callback_data="sisters:4")],
    ])


def _position_kb(lang: str) -> InlineKeyboardMarkup:
    if lang == "uz":
        opts = [
            ("Katta farzand", "fpos:first"),
            ("O'rtancha", "fpos:middle"),
            ("Kenja farzand", "fpos:last"),
            ("Yagona farzand", "fpos:only"),
        ]
    else:
        opts = [
            ("Старший/ая", "fpos:first"),
            ("Средний/яя", "fpos:middle"),
            ("Младший/ая", "fpos:last"),
            ("Единственный/ая", "fpos:only"),
        ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts
    ])


@router.message(QuestionnaireStates.ext_mother)
async def ext_mother(message: Message, state: FSMContext):
    await state.update_data(mother_occupation=message.text.strip())
    try:
        await message.delete()
    except Exception:
        pass
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(3)

    if lang == "uz":
        q_text = f"👨‍👩‍👧‍👦 3/9-savol\n{bar}\n\nAka-uka va opa-singillar:"
    else:
        q_text = f"👨‍👩‍👧‍👦 Вопрос 3/9\n{bar}\n\nБратья и сёстры:"

    full_text = _with_card(data, lang, q_text)
    await _show_question(message, state, full_text, reply_markup=_brothers_kb(lang))
    await state.set_state(QuestionnaireStates.ext_brothers)


# ── 3a. Братья ──
@router.callback_query(F.data.startswith("brothers:"), QuestionnaireStates.ext_brothers)
async def ext_brothers(callback: CallbackQuery, state: FSMContext):
    count = int(callback.data.replace("brothers:", ""))
    await state.update_data(brothers_count=count)
    lang = await _lang(state)
    # Меняем только клавиатуру (текст вопроса тот же — "Братья и сёстры")
    await callback.message.edit_reply_markup(reply_markup=_sisters_kb(lang))
    await state.set_state(QuestionnaireStates.ext_sisters)
    await callback.answer()


# ── 3b. Сёстры → Место в семье ──
@router.callback_query(F.data.startswith("sisters:"), QuestionnaireStates.ext_sisters)
async def ext_sisters(callback: CallbackQuery, state: FSMContext):
    count = int(callback.data.replace("sisters:", ""))
    await state.update_data(sisters_count=count)
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(3)

    if lang == "uz":
        q_text = f"👨‍👩‍👧‍👦 3/9-savol\n{bar}\n\nOiladagi o'rni:"
    else:
        q_text = f"👨‍👩‍👧‍👦 Вопрос 3/9\n{bar}\n\nМесто в семье:"

    full_text = _with_card(data, lang, q_text)
    await _show_question(callback, state, full_text, reply_markup=_position_kb(lang))
    await state.set_state(QuestionnaireStates.ext_position)
    await callback.answer()


# ── 3c. Место в семье → 4. Характер ──
@router.callback_query(F.data.startswith("fpos:"), QuestionnaireStates.ext_position)
async def ext_position(callback: CallbackQuery, state: FSMContext):
    position = callback.data.replace("fpos:", "")
    await state.update_data(family_position=position)
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(4)

    if lang == "uz":
        q_text = f"🌸 4/9-savol\n{bar}\n\nXarakter va qiziqishlar\n(ixtiyoriy):"
    else:
        q_text = f"🌸 Вопрос 4/9\n{bar}\n\nХарактер и увлечения\n(необязательно):"

    full_text = _with_card(data, lang, q_text)
    await _show_question(callback, state, full_text, reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.ext_character)
    await callback.answer()


# ══════════════════════════════════════
# БЛОК 2: ЛИЧНОЕ
# ══════════════════════════════════════

# ── 4. Характер → 5. Здоровье ──
async def _ask_health(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(5)

    if lang == "uz":
        q_text = f"🌿 5/9-savol\n{bar}\n\nSog'lig'ining xususiyatlari\n(ixtiyoriy):"
    else:
        q_text = f"🌿 Вопрос 5/9\n{bar}\n\nОсобенности здоровья\n(необязательно):"

    full_text = _with_card(data, lang, q_text)
    await _show_question(m_or_cb, state, full_text, reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.ext_health)


@router.message(QuestionnaireStates.ext_character)
async def ext_character(message: Message, state: FSMContext):
    await state.update_data(character_hobbies=message.text.strip())
    try:
        await message.delete()
    except Exception:
        pass
    await _ask_health(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_character)
async def ext_character_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(character_hobbies=None)
    await _ask_health(callback, state)
    await callback.answer()


# ── 5. Здоровье → 6. О себе ──
async def _ask_about(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(6)

    if lang == "uz":
        q_text = f"💭 6/9-savol\n{bar}\n\nO'zingiz va kutganlaringiz haqida\n(ixtiyoriy):"
    else:
        q_text = f"💭 Вопрос 6/9\n{bar}\n\nО себе и ожиданиях\n(необязательно):"

    full_text = _with_card(data, lang, q_text)
    await _show_question(m_or_cb, state, full_text, reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.ext_ideal_family)


@router.message(QuestionnaireStates.ext_health)
async def ext_health(message: Message, state: FSMContext):
    await state.update_data(health_notes=message.text.strip())
    try:
        await message.delete()
    except Exception:
        pass
    await _ask_about(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_health)
async def ext_health_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(health_notes=None)
    await _ask_about(callback, state)
    await callback.answer()


# ── 6. О себе → 7. Жильё ──
async def _ask_housing(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(7)

    if lang == "uz":
        q_text = f"🏡 7/9-savol\n{bar}\n\nTurar joy:"
        opts = [
            ("O'z uyi", "housing:own_house"),
            ("O'z kvartirasi", "housing:own_apt"),
            ("Ota-ona bilan", "housing:parents"),
            ("Ijara", "housing:rent"),
        ]
    else:
        q_text = f"🏡 Вопрос 7/9\n{bar}\n\nЖильё:"
        opts = [
            ("Свой дом", "housing:own_house"),
            ("Своя квартира", "housing:own_apt"),
            ("С родителями", "housing:parents"),
            ("Аренда", "housing:rent"),
        ]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts
    ])
    full_text = _with_card(data, lang, q_text)
    await _show_question(m_or_cb, state, full_text, reply_markup=kb)
    await state.set_state(QuestionnaireStates.ext_housing)


@router.message(QuestionnaireStates.ext_ideal_family)
async def ext_about(message: Message, state: FSMContext):
    await state.update_data(ideal_family_life=message.text.strip())
    try:
        await message.delete()
    except Exception:
        pass
    await _ask_housing(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_ideal_family)
async def ext_about_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(ideal_family_life=None)
    await _ask_housing(callback, state)
    await callback.answer()


# ══════════════════════════════════════
# БЛОК 3: МАТЕРИАЛЬНОЕ
# ══════════════════════════════════════

# ── 7. Жильё → (тип жилья родителей) → 8. Автомобиль ──
@router.callback_query(F.data.startswith("housing:"), QuestionnaireStates.ext_housing)
async def ext_housing(callback: CallbackQuery, state: FSMContext):
    housing = callback.data.replace("housing:", "")
    await state.update_data(housing=housing)
    lang = await _lang(state)

    if housing == "parents":
        if lang == "uz":
            opts = [("Uy", "phousing:house"), ("Kvartira", "phousing:apt")]
            title = "Ota-ona uyining turi:"
        else:
            opts = [("Дом", "phousing:house"), ("Квартира", "phousing:apt")]
            title = "Тип жилья родителей:"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts
        ])
        await _show_question(callback, state, title, reply_markup=kb)
        await state.set_state(QuestionnaireStates.ext_housing_parent)
    else:
        await _ask_car(callback, state)
    await callback.answer()


@router.callback_query(F.data.startswith("phousing:"), QuestionnaireStates.ext_housing_parent)
async def ext_housing_parent(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parent_housing_type=callback.data.replace("phousing:", ""))
    await _ask_car(callback, state)
    await callback.answer()


# ── 8. Автомобиль → 9. Контакты ──
async def _ask_car(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(8)

    if lang == "uz":
        q_text = f"🚘 8/9-savol\n{bar}\n\nAvtomobil:"
        opts = [
            ("Shaxsiy", "car:own"),
            ("Oilaviy", "car:family"),
            ("Yo'q", "car:no"),
        ]
    else:
        q_text = f"🚘 Вопрос 8/9\n{bar}\n\nАвтомобиль:"
        opts = [
            ("Личный", "car:own"),
            ("Семейный", "car:family"),
            ("Нет", "car:no"),
        ]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts
    ])
    full_text = _with_card(data, lang, q_text)
    await _show_question(m_or_cb, state, full_text, reply_markup=kb)
    await state.set_state(QuestionnaireStates.ext_car)


@router.callback_query(F.data.startswith("car:"), QuestionnaireStates.ext_car)
async def ext_car(callback: CallbackQuery, state: FSMContext):
    await state.update_data(car=callback.data.replace("car:", ""))
    await _ask_parent_phone(callback, state)
    await callback.answer()


# ══════════════════════════════════════
# БЛОК 4: КОНТАКТЫ
# ══════════════════════════════════════

# ══════════════════════════════════════
# Общие тексты о защите контактов
# ══════════════════════════════════════

_CONTACT_NOTICE_RU = (
    "Ваши контакты будут переданы\n"
    "только с вашего одобрения.\n"
    "Модератор сначала свяжется\n"
    "с вами и спросит разрешения. 🤝"
)
_CONTACT_NOTICE_UZ = (
    "Kontaktlaringiz faqat sizning\n"
    "roziligingiz bilan beriladi.\n"
    "Moderator avval siz bilan\n"
    "bog'lanib ruxsat so'raydi. 🤝"
)

_CONTACT_NOTICE_SHORT_RU = (
    "Ваши контакты — только\n"
    "с вашего одобрения. 🤝"
)
_CONTACT_NOTICE_SHORT_UZ = (
    "Kontaktlaringiz faqat sizning\n"
    "roziligingiz bilan beriladi. 🤝"
)


# ── 9a. Телефон родителей (с вступлением) ──
async def _ask_parent_phone(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    card = build_ext_card(data, lang)
    bar = ext_progress_bar(9)

    if lang == "uz":
        body = (
            f"📞 9/9-savol\n{bar}\n\n"
            f"<b>Kontaktlar</b>\n\n"
            f"{_CONTACT_NOTICE_UZ}\n\n"
            f"Ota-onalar telefoni:\n"
            f"Prefiks bilan yoki usiz kiriting:\n"
            f"+998 90 123 45 67\n"
            f"yoki shunchaki: 901234567"
        )
    else:
        body = (
            f"📞 Вопрос 9/9\n{bar}\n\n"
            f"<b>Контактные данные</b>\n\n"
            f"{_CONTACT_NOTICE_RU}\n\n"
            f"Телефон родителей:\n"
            f"Можно с префиксом или без:\n"
            f"+998 90 123 45 67\n"
            f"или просто: 901234567"
        )

    full_text = (card + SEP + body) if card else body
    await _show_question(m_or_cb, state, full_text, reply_markup=skip_kb(lang), parse_mode="HTML")
    await state.set_state(QuestionnaireStates.ext_parent_phone)


def _parent_tg_text(lang: str, card: str = "") -> str:
    if lang == "uz":
        body = "📱 Ota-onalar Telegram:\n(@username)"
    else:
        body = "📱 Telegram родителей:\n(@username)"
    return (card + SEP + body) if card else body


@router.message(QuestionnaireStates.ext_parent_phone)
async def ext_parent_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    digits = "".join(filter(str.isdigit, phone))
    if len(digits) == 9:
        phone = f"+998{digits}"
    elif len(digits) == 12 and digits.startswith("998"):
        phone = f"+{digits}"
    await state.update_data(parent_phone=phone)
    lang = await _lang(state)

    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except Exception:
        pass

    # Удаляем старое окно бота
    data = await state.get_data()
    last_id = data.get("last_bot_msg_id")
    if last_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_id)
        except Exception:
            pass
        await state.update_data(last_bot_msg_id=None)

    # Отправляем следующий вопрос с обновлённой карточкой
    data = await state.get_data()
    card = build_ext_card(data, lang)
    text = _parent_tg_text(lang, card)
    sent = await message.answer(text, reply_markup=skip_kb(lang))
    await state.update_data(last_bot_msg_id=sent.message_id)
    await state.set_state(QuestionnaireStates.ext_parent_telegram)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_parent_phone)
async def ext_parent_phone_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parent_phone=None)
    lang = await _lang(state)
    data = await state.get_data()
    card = build_ext_card(data, lang)
    text = _parent_tg_text(lang, card)
    await _show_question(callback, state, text, reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.ext_parent_telegram)
    await callback.answer()


# ── 9b. Telegram родителей ──
def _candidate_tg_text(lang: str, card: str = "") -> str:
    if lang == "uz":
        body = "💬 Nomzod Telegram:\n(@username)"
    else:
        body = "💬 Telegram кандидата:\n(@username)"
    return (card + SEP + body) if card else body


@router.message(QuestionnaireStates.ext_parent_telegram)
async def ext_parent_tg(message: Message, state: FSMContext):
    tg = message.text.strip()
    if not tg.startswith("@"):
        tg = f"@{tg}"
    await state.update_data(parent_telegram=tg)
    lang = await _lang(state)

    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except Exception:
        pass

    # Удаляем старое окно бота
    data = await state.get_data()
    last_id = data.get("last_bot_msg_id")
    if last_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=last_id)
        except Exception:
            pass
        await state.update_data(last_bot_msg_id=None)

    # Отправляем следующий вопрос с карточкой
    data = await state.get_data()
    card = build_ext_card(data, lang)
    text = _candidate_tg_text(lang, card)
    sent = await message.answer(text, reply_markup=skip_kb(lang))
    await state.update_data(last_bot_msg_id=sent.message_id)
    await state.set_state(QuestionnaireStates.ext_candidate_telegram)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_parent_telegram)
async def ext_parent_tg_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(parent_telegram=None)
    lang = await _lang(state)
    data = await state.get_data()
    card = build_ext_card(data, lang)
    text = _candidate_tg_text(lang, card)
    await _show_question(callback, state, text, reply_markup=skip_kb(lang))
    await state.set_state(QuestionnaireStates.ext_candidate_telegram)
    await callback.answer()


# ── 9c. Telegram кандидата ──
@router.message(QuestionnaireStates.ext_candidate_telegram)
async def ext_candidate_tg(message: Message, state: FSMContext):
    tg = message.text.strip()
    if not tg.startswith("@"):
        tg = f"@{tg}"
    await state.update_data(candidate_telegram=tg)

    try:
        await message.delete()
    except Exception:
        pass

    await _ask_address(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_candidate_telegram)
async def ext_candidate_tg_skip(callback: CallbackQuery, state: FSMContext):
    await state.update_data(candidate_telegram=None)
    await _ask_address(callback, state)
    await callback.answer()


# ── 9d. Адрес / Геолокация / Ссылка ──
async def _ask_address(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    card = build_ext_card(data, lang)

    if lang == "uz":
        body = "🏠 Manzil yoki geolokasiya:"
        opts = [
            ("🏠 Manzilni yozish", "addr:text"),
            ("📍 Geolokatsiya yuborish", "addr:geo"),
            ("🗺 Xarita havolasi", "addr:link"),
            ("⏭ O'tkazib yuborish", "addr:skip"),
        ]
    else:
        body = "🏠 Адрес или геолокация:"
        opts = [
            ("🏠 Написать адрес", "addr:text"),
            ("📍 Отправить геолокацию", "addr:geo"),
            ("🗺 Ссылка на карту", "addr:link"),
            ("⏭ Пропустить", "addr:skip"),
        ]

    text = (card + SEP + body) if card else body
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts
    ])
    await _show_question(m_or_cb, state, text, reply_markup=kb)
    await state.set_state(QuestionnaireStates.ext_address)


@router.callback_query(F.data.startswith("addr:"), QuestionnaireStates.ext_address)
async def ext_address_choice(callback: CallbackQuery, state: FSMContext):
    choice = callback.data.replace("addr:", "")
    lang = await _lang(state)

    # skip → сразу финальный экран (там своё редактирование)
    if choice == "skip":
        await _show_ext_complete(callback, state)
        await callback.answer()
        return

    # Удаляем текущее окно с выбором адреса
    try:
        await callback.message.delete()
    except Exception:
        pass
    await state.update_data(last_bot_msg_id=None)

    if choice == "text":
        text = "Ko'cha/mahalla nomini kiriting:" if lang == "uz" else "Введите улицу/махаллю:"
        sent = await callback.message.answer(text, reply_markup=skip_kb(lang))
        await state.update_data(last_bot_msg_id=sent.message_id)
        await state.set_state(QuestionnaireStates.ext_address_text)
    elif choice == "geo":
        geo_label = "📍 Geolokatsiya yuborish" if lang == "uz" else "📍 Отправить геолокацию"
        title = "📍 Geolokatsiya:" if lang == "uz" else "📍 Геолокация:"
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=geo_label, request_location=True)]],
            resize_keyboard=True, one_time_keyboard=True,
        )
        sent = await callback.message.answer(title, reply_markup=kb)
        await state.update_data(last_bot_msg_id=sent.message_id)
        await state.set_state(QuestionnaireStates.ext_location)
    elif choice == "link":
        text = "🗺 Google Maps yoki 2GIS havolasini kiriting:" if lang == "uz" else "🗺 Вставьте ссылку Google Maps или 2GIS:"
        sent = await callback.message.answer(text, reply_markup=skip_kb(lang))
        await state.update_data(last_bot_msg_id=sent.message_id)
        await state.set_state(QuestionnaireStates.ext_address_link)

    await callback.answer()


@router.message(QuestionnaireStates.ext_address_text)
async def ext_address_text(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    # Удаляем сообщение пользователя, чтобы экран был чистым
    try:
        await message.delete()
    except Exception:
        pass
    await _show_ext_complete(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_address_text)
async def ext_address_text_skip(callback: CallbackQuery, state: FSMContext):
    await _show_ext_complete(callback, state)
    await callback.answer()


@router.message(QuestionnaireStates.ext_location)
async def ext_location(message: Message, state: FSMContext):
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude
        await state.update_data(
            location_lat=lat,
            location_lon=lon,
            location_link=f"https://maps.google.com/?q={lat},{lon}",
        )
    # Удаляем сообщение пользователя с геолокацией
    try:
        await message.delete()
    except Exception:
        pass
    # Удаляем reply-клавиатуру одноразовым сообщением, которое тут же убираем
    try:
        tmp = await message.answer("✓", reply_markup=ReplyKeyboardRemove())
        await tmp.delete()
    except Exception:
        pass
    # Удаляем старое сообщение бота (с prompt "📍 Геолокация:")
    data = await state.get_data()
    last_id = data.get("last_bot_msg_id")
    if last_id:
        try:
            await message.bot.delete_message(message.chat.id, last_id)
        except Exception:
            pass
        await state.update_data(last_bot_msg_id=None)
    await _show_ext_complete(message, state)


@router.message(QuestionnaireStates.ext_address_link)
async def ext_address_link(message: Message, state: FSMContext):
    await state.update_data(location_link=message.text.strip())
    try:
        await message.delete()
    except Exception:
        pass
    await _show_ext_complete(message, state)


@router.callback_query(F.data == "skip", QuestionnaireStates.ext_address_link)
async def ext_address_link_skip(callback: CallbackQuery, state: FSMContext):
    await _show_ext_complete(callback, state)
    await callback.answer()


# ══════════════════════════════════════
# noop — заглушка для label-кнопок
# ══════════════════════════════════════
@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()


# ══════════════════════════════════════
# Финальный экран Этапа 2
# ══════════════════════════════════════

async def _show_ext_complete(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    card = build_ext_card(data, lang)

    if lang == "uz":
        text = (
            f"✅ <b>Anketa to'ldirildi!</b>\n\n"
            f"{card}\n\n"
            f"Nashr etishga tayyormisiz?"
        )
        buttons = [
            [InlineKeyboardButton(text="🚀 Nashr etish", callback_data="profile:confirm")],
            [InlineKeyboardButton(text="← Orqaga", callback_data="ext:back")],
        ]
    else:
        text = (
            f"✅ <b>Анкета дополнена!</b>\n\n"
            f"{card}\n\n"
            f"Готовы опубликовать?"
        )
        buttons = [
            [InlineKeyboardButton(text="🚀 Опубликовать", callback_data="profile:confirm")],
            [InlineKeyboardButton(text="← Назад", callback_data="ext:back")],
        ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await _show_question(m_or_cb, state, text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(QuestionnaireStates.ext_confirm)


# ── «← Назад» с финального экрана Этапа 2 → снова адрес ──
@router.callback_query(F.data == "ext:back", QuestionnaireStates.ext_confirm)
async def ext_back(callback: CallbackQuery, state: FSMContext):
    await _ask_address(callback, state)
    await callback.answer()
