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
)
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states import QuestionnaireStates
from bot.texts import t
from bot.keyboards.inline import (
    skip_kb, back_kb, main_menu_kb,
    skip_back_ext_kb, back_ext_kb, add_nav,
    enhance_or_publish_kb,
)
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


def ext_progress_bar(current: int, total: int = 8) -> str:
    """Прогресс-бар для Этапа 2."""
    filled = current
    empty = total - filled
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
                "ru": {"oldest": "старший/ая", "middle": "средний/яя",
                       "youngest": "младший/ая", "only": "единственный/ая"},
                "uz": {"oldest": "katta", "middle": "o'rtancha",
                       "youngest": "kenja", "only": "yagona"},
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
        lines.append(f"💭 {snippet}")

    # Жильё
    house_map = {
        "ru": {"own_house": "Свой дом", "own_apartment": "Своя квартира",
               "with_parents": "С родителями", "rent": "Аренда"},
        "uz": {"own_house": "O'z uyi", "own_apartment": "O'z kvartirasi",
               "with_parents": "Ota-ona bilan", "rent": "Ijara"},
    }
    house = data.get("housing")
    if house:
        lines.append(f"🏡 {house_map[L].get(house, house)}")

    # Автомобиль
    car_map = {
        "ru": {"own": "Личный авто", "family": "Семейный авто", "no": "Нет авто"},
        "uz": {"own": "Shaxsiy avto", "family": "Oilaviy avto", "no": "Avto yo'q"},
    }
    car = data.get("car")
    if car:
        lines.append(f"🚘 {car_map[L].get(car, car)}")

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
# RENDER-функции для каждого вопроса Этапа 2
# (используются и в forward-flow, и в back-handler)
# ══════════════════════════════════════

async def _render_ext_intro(m_or_cb, state: FSMContext):
    """Возврат на экран «Сделать анкету ярче» (до Этапа 2)."""
    from bot.states import RequirementStates
    lang = await _lang(state)
    if lang == "uz":
        text = (
            "✨ <b>Anketani boyiting</b>\n\n"
            "Qo'shimcha ma'lumotlar qo'shing —\n"
            "va anketangiz boshqalardan ajralib turadi:\n\n"
            "👨‍👩‍👧 Oila haqida\n🌸 Xarakter va qiziqishlar\n"
            "🏡 Turar joy va avtomobil\n📞 Kontaktlar\n\n"
            "Taxminan 2 daqiqa vaqt oladi 🕐"
        )
    else:
        text = (
            "✨ <b>Сделайте анкету ярче</b>\n\n"
            "Добавьте детали — и ваша анкета\nбудет выделяться среди остальных:\n\n"
            "👨‍👩‍👧 О семье\n🌸 Характер и увлечения\n"
            "🏡 Жильё и автомобиль\n📞 Контакты\n\n"
            "Займёт около 2 минут 🕐"
        )
    await _show_question(m_or_cb, state, text, reply_markup=enhance_or_publish_kb(lang), parse_mode="HTML")
    await state.set_state(RequirementStates.summary)


async def _ask_father(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(1)
    if lang == "uz":
        q = f"👨‍💼 1/8-savol\n{bar}\n\nOtasi — nima bilan shug'ullanadi:"
    else:
        q = f"👨‍💼 Вопрос 1/8\n{bar}\n\nОтец — чем занимается:"
    await _show_question(m_or_cb, state, _with_card(data, lang, q), reply_markup=back_ext_kb(lang))
    await state.set_state(QuestionnaireStates.ext_father)


async def _ask_mother(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(2)
    if lang == "uz":
        q = f"👩‍💼 2/8-savol\n{bar}\n\nOnasi — nima bilan shug'ullanadi:"
    else:
        q = f"👩‍💼 Вопрос 2/8\n{bar}\n\nМать — чем занимается:"
    await _show_question(m_or_cb, state, _with_card(data, lang, q), reply_markup=back_ext_kb(lang))
    await state.set_state(QuestionnaireStates.ext_mother)


async def _ask_brothers(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(3)
    if lang == "uz":
        q = f"👨‍👩‍👧‍👦 3/8-savol\n{bar}\n\nAka-uka va opa-singillar:"
    else:
        q = f"👨‍👩‍👧‍👦 Вопрос 3/8\n{bar}\n\nБратья и сёстры:"
    kb = add_nav(_brothers_kb(lang).inline_keyboard, lang, "back_ext_step", show_main=False)
    await _show_question(m_or_cb, state, _with_card(data, lang, q), reply_markup=kb)
    await state.set_state(QuestionnaireStates.ext_brothers)


async def _ask_sisters(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(3)
    if lang == "uz":
        q = f"👨‍👩‍👧‍👦 3/8-savol\n{bar}\n\nAka-uka va opa-singillar:"
    else:
        q = f"👨‍👩‍👧‍👦 Вопрос 3/8\n{bar}\n\nБратья и сёстры:"
    kb = add_nav(_sisters_kb(lang).inline_keyboard, lang, "back_ext_step", show_main=False)
    await _show_question(m_or_cb, state, _with_card(data, lang, q), reply_markup=kb)
    await state.set_state(QuestionnaireStates.ext_sisters)


async def _ask_position(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(3)
    if lang == "uz":
        q = f"👨‍👩‍👧‍👦 3/8-savol\n{bar}\n\nOiladagi o'rni:"
    else:
        q = f"👨‍👩‍👧‍👦 Вопрос 3/8\n{bar}\n\nМесто в семье:"
    kb = add_nav(_position_kb(lang).inline_keyboard, lang, "back_ext_step", show_main=False)
    await _show_question(m_or_cb, state, _with_card(data, lang, q), reply_markup=kb)
    await state.set_state(QuestionnaireStates.ext_position)


async def _ask_character(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    data = await state.get_data()
    bar = ext_progress_bar(4)
    if lang == "uz":
        q = f"🌸 4/8-savol\n{bar}\n\nXarakter va qiziqishlar\n(ixtiyoriy):"
    else:
        q = f"🌸 Вопрос 4/8\n{bar}\n\nХарактер и увлечения\n(необязательно):"
    await _show_question(m_or_cb, state, _with_card(data, lang, q), reply_markup=skip_back_ext_kb(lang))
    await state.set_state(QuestionnaireStates.ext_character)


async def _ask_housing_parent(m_or_cb, state: FSMContext):
    lang = await _lang(state)
    if lang == "uz":
        opts = [("Uy", "phousing:house"), ("Kvartira", "phousing:apartment")]
        title = "Ota-ona uyining turi:"
    else:
        opts = [("Дом", "phousing:house"), ("Квартира", "phousing:apartment")]
        title = "Тип жилья родителей:"
    kb_rows = [[InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts]
    kb = add_nav(kb_rows, lang, "back_ext_step", show_main=False)
    await _show_question(m_or_cb, state, title, reply_markup=kb)
    await state.set_state(QuestionnaireStates.ext_housing_parent)


# ══════════════════════════════════════
# BACK_MAP_EXT + handler back_ext_step
# ══════════════════════════════════════

def _get_back_map_ext():
    """Отложенное построение мапы: render-функции объявлены выше и _ask_* ниже
    в файле, так что собираем словарь динамически из глобалей.
    Для ext_car — специальная логика (см. handler).
    """
    return {
        QuestionnaireStates.ext_father.state:             _render_ext_intro,
        QuestionnaireStates.ext_mother.state:             _ask_father,
        QuestionnaireStates.ext_brothers.state:           _ask_mother,
        QuestionnaireStates.ext_sisters.state:            _ask_brothers,
        QuestionnaireStates.ext_position.state:           _ask_sisters,
        QuestionnaireStates.ext_character.state:          _ask_position,
        QuestionnaireStates.ext_health.state:             _ask_character,
        QuestionnaireStates.ext_ideal_family.state:       _ask_health,
        QuestionnaireStates.ext_housing.state:            _ask_about,
        QuestionnaireStates.ext_housing_parent.state:     _ask_housing,
        # ext_car — conditional, см. handler ниже
    }


@router.callback_query(F.data == "back_ext_step")
async def back_ext_step(callback: CallbackQuery, state: FSMContext):
    """Универсальный «← Назад» на Этапе 2 — возврат к предыдущему вопросу."""
    current = await state.get_state()
    data = await state.get_data()

    # Специальный случай: Q8 → Q7a (если housing=with_parents) или Q7
    if current == QuestionnaireStates.ext_car.state:
        if data.get("housing") == "with_parents":
            await _ask_housing_parent(callback, state)
        else:
            await _ask_housing(callback, state)
        await callback.answer()
        return

    # (адрес/геолокация перенесены в Этап 1 как Q14)

    render_fn = _get_back_map_ext().get(current)
    if not render_fn:
        await callback.answer("🔙")
        return
    await render_fn(callback, state)
    await callback.answer()


# ══════════════════════════════════════
# СТАРТ ЭТАПА 2
# ══════════════════════════════════════

@router.callback_query(F.data == "ext:start")
async def ext_start(callback: CallbackQuery, state: FSMContext):
    """Старт Этапа 2 — сразу к вопросу 1 (отец)."""
    await _ask_father(callback, state)
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
    await _ask_mother(message, state)


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
            ("Katta farzand", "fpos:oldest"),
            ("O'rtancha", "fpos:middle"),
            ("Kenja farzand", "fpos:youngest"),
            ("Yagona farzand", "fpos:only"),
        ]
    else:
        opts = [
            ("Старший/ая", "fpos:oldest"),
            ("Средний/яя", "fpos:middle"),
            ("Младший/ая", "fpos:youngest"),
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
    await _ask_brothers(message, state)


# ── 3a. Братья ──
@router.callback_query(F.data.startswith("brothers:"), QuestionnaireStates.ext_brothers)
async def ext_brothers(callback: CallbackQuery, state: FSMContext):
    count = int(callback.data.replace("brothers:", ""))
    await state.update_data(brothers_count=count)
    await _ask_sisters(callback, state)
    await callback.answer()


# ── 3b. Сёстры → Место в семье ──
@router.callback_query(F.data.startswith("sisters:"), QuestionnaireStates.ext_sisters)
async def ext_sisters(callback: CallbackQuery, state: FSMContext):
    count = int(callback.data.replace("sisters:", ""))
    await state.update_data(sisters_count=count)
    await _ask_position(callback, state)
    await callback.answer()


# ── 3c. Место в семье → 4. Характер ──
@router.callback_query(F.data.startswith("fpos:"), QuestionnaireStates.ext_position)
async def ext_position(callback: CallbackQuery, state: FSMContext):
    position = callback.data.replace("fpos:", "")
    await state.update_data(family_position=position)
    await _ask_character(callback, state)
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
        q_text = f"🌿 5/8-savol\n{bar}\n\nSog'lig'ining xususiyatlari\n(ixtiyoriy):"
    else:
        q_text = f"🌿 Вопрос 5/8\n{bar}\n\nОсобенности здоровья\n(необязательно):"

    full_text = _with_card(data, lang, q_text)
    await _show_question(m_or_cb, state, full_text, reply_markup=skip_back_ext_kb(lang))
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
        q_text = f"💭 6/8-savol\n{bar}\n\nO'zingiz va kutganlaringiz haqida\n(ixtiyoriy):"
    else:
        q_text = f"💭 Вопрос 6/8\n{bar}\n\nО себе и ожиданиях\n(необязательно):"

    full_text = _with_card(data, lang, q_text)
    await _show_question(m_or_cb, state, full_text, reply_markup=skip_back_ext_kb(lang))
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
        q_text = f"🏡 7/8-savol\n{bar}\n\nTurar joy:"
        opts = [
            ("O'z uyi", "housing:own_house"),
            ("O'z kvartirasi", "housing:own_apartment"),
            ("Ota-ona bilan", "housing:with_parents"),
            ("Ijara", "housing:rent"),
        ]
    else:
        q_text = f"🏡 Вопрос 7/8\n{bar}\n\nЖильё:"
        opts = [
            ("Свой дом", "housing:own_house"),
            ("Своя квартира", "housing:own_apartment"),
            ("С родителями", "housing:with_parents"),
            ("Аренда", "housing:rent"),
        ]

    kb_rows = [[InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts]
    kb = add_nav(kb_rows, lang, "back_ext_step", show_main=False)
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

    if housing == "with_parents":
        await _ask_housing_parent(callback, state)
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
        q_text = f"🚘 8/8-savol\n{bar}\n\nAvtomobil:"
        opts = [
            ("Shaxsiy", "car:own"),
            ("Oilaviy", "car:family"),
            ("Yo'q", "car:no"),
        ]
    else:
        q_text = f"🚘 Вопрос 8/8\n{bar}\n\nАвтомобиль:"
        opts = [
            ("Личный", "car:own"),
            ("Семейный", "car:family"),
            ("Нет", "car:no"),
        ]

    kb_rows = [[InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts]
    kb = add_nav(kb_rows, lang, "back_ext_step", show_main=False)
    full_text = _with_card(data, lang, q_text)
    await _show_question(m_or_cb, state, full_text, reply_markup=kb)
    await state.set_state(QuestionnaireStates.ext_car)


@router.callback_query(F.data.startswith("car:"), QuestionnaireStates.ext_car)
async def ext_car(callback: CallbackQuery, state: FSMContext):
    await state.update_data(car=callback.data.replace("car:", ""))
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
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="ext:back")],
        ]
    else:
        text = (
            f"✅ <b>Анкета дополнена!</b>\n\n"
            f"{card}\n\n"
            f"Готовы опубликовать?"
        )
        buttons = [
            [InlineKeyboardButton(text="🚀 Опубликовать", callback_data="profile:confirm")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="ext:back")],
        ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await _show_question(m_or_cb, state, text, reply_markup=kb, parse_mode="HTML")
    await state.set_state(QuestionnaireStates.ext_confirm)


# ── «← Назад» с финального экрана Этапа 2 → снова авто (последний вопрос) ──
@router.callback_query(F.data == "ext:back", QuestionnaireStates.ext_confirm)
async def ext_back(callback: CallbackQuery, state: FSMContext):
    await _ask_car(callback, state)
    await callback.answer()
