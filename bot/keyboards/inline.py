from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.texts import t


# ── Универсальная навигация ──

def nav_kb(lang: str = "ru", back_cb: str = "back:menu",
           show_back: bool = True, show_main: bool = True) -> list:
    """Навигационные кнопки — возвращает список строк для добавления в клавиатуру."""
    row = []
    if show_back:
        row.append(InlineKeyboardButton(
            text="← Orqaga" if lang == "uz" else "← Назад",
            callback_data=back_cb,
        ))
    if show_main:
        row.append(InlineKeyboardButton(
            text="Menyu" if lang == "uz" else "Меню",
            callback_data="menu:main",
        ))
    return [row] if row else []


def add_nav(existing_rows: list, lang: str = "ru", back_cb: str = "back:menu",
            show_back: bool = True, show_main: bool = True) -> InlineKeyboardMarkup:
    """Добавить навигацию к существующим строкам клавиатуры."""
    rows = list(existing_rows)
    rows.extend(nav_kb(lang, back_cb, show_back, show_main))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_main_kb(lang: str = "ru", back_cb: str = "back:menu") -> InlineKeyboardMarkup:
    """Кнопки Назад + Главное меню."""
    return InlineKeyboardMarkup(inline_keyboard=nav_kb(lang, back_cb))


def skip_back_ext_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Этап 2: текстовый вопрос с [⏭ Пропустить] [← Назад] (back_ext_step)."""
    skip = "⏭ O'tkazib yuborish" if lang == "uz" else "⏭ Пропустить"
    back = "← Orqaga" if lang == "uz" else "← Назад"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=skip, callback_data="skip")],
        [InlineKeyboardButton(text=back, callback_data="back_ext_step")],
    ])


def back_ext_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Этап 2: обязательный текстовый вопрос (без skip) с [← Назад]."""
    back = "← Orqaga" if lang == "uz" else "← Назад"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=back, callback_data="back_ext_step")],
    ])


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
        ]
    ])


def consent_general_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_agree", lang), callback_data="consent:general:yes")],
        [InlineKeyboardButton(text=t("btn_disagree", lang), callback_data="consent:general:no")],
    ])


def consent_special_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_consent_special_yes", lang), callback_data="consent:special:yes")],
        [InlineKeyboardButton(text=t("btn_disagree", lang), callback_data="consent:special:no")],
    ])


def main_menu_kb(lang: str = "ru", user_id: int = 0) -> InlineKeyboardMarkup:
    """Полное меню для всех пользователей."""
    return _full_menu_kb(lang)


def _full_menu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_search_candidate", lang), callback_data="menu:search_sub")],
        [InlineKeyboardButton(text=t("btn_create_profile", lang), callback_data="menu:create_sub")],
        [InlineKeyboardButton(text=t("btn_my_applications", lang), callback_data="menu:my")],
        [
            InlineKeyboardButton(text=t("btn_contact_moderator", lang), callback_data="menu:moderator"),
            InlineKeyboardButton(text=t("btn_about", lang), callback_data="menu:about"),
        ],
    ])


def search_submenu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Подменю: Найти кандидата → невестку / жениха."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_search_bride", lang), callback_data="menu:search_bride")],
        [InlineKeyboardButton(text=t("btn_search_groom", lang), callback_data="menu:search_groom")],
        *nav_kb(lang, "back:menu"),
    ])


def create_submenu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Подменю: Создать анкету → сына / дочери."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_profile_son", lang), callback_data="menu:son")],
        [InlineKeyboardButton(text=t("btn_profile_daughter", lang), callback_data="menu:daughter")],
        *nav_kb(lang, "back:menu", show_main=False),
    ])


def back_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back:menu")],
    ])


def contact_moderator_kb(lang: str = "ru", region: str = "tashkent") -> InlineKeyboardMarkup:
    from bot.config import get_moderator_username
    username = get_moderator_username(region)
    write_tg = "💬 Написать в Telegram" if lang == "ru" else "💬 Telegramda yozish"
    back = t("btn_back", lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=write_tg, url=f"https://t.me/{username}")],
        [InlineKeyboardButton(text=back, callback_data="back:menu")],
    ])


def quest_start_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_start", lang), callback_data="quest:start")],
        *nav_kb(lang, "back:menu"),
    ])


def confirm_age_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn_yes", lang), callback_data="age:confirm"),
            InlineKeyboardButton(text=t("btn_fix", lang), callback_data="age:fix"),
        ]
    ])


def education_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["📚 Среднее", "📋 Среднее специальное", "🎓 Высшее", "🏛 Студент/ка"],
        "uz": ["📚 O'rta", "📋 O'rta maxsus", "🎓 Oliy", "🏛 Talaba"],
    }
    values = ["secondary", "vocational", "higher", "studying"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"edu:{values[i]}")]
        for i in range(4)
    ])


def housing_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["Свой дом", "Своя квартира", "С родителями", "Аренда"],
        "uz": ["O'z uyi", "O'z kvartirasi", "Ota-ona bilan", "Ijara"],
    }
    values = ["own_house", "own_apartment", "with_parents", "rent"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"housing:{values[i]}")]
        for i in range(4)
    ])


def parent_housing_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {"ru": ["Дом", "Квартира"], "uz": ["Uy", "Kvartira"]}
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=labels.get(lang, labels["ru"])[0], callback_data="phousing:house"),
            InlineKeyboardButton(text=labels.get(lang, labels["ru"])[1], callback_data="phousing:apartment"),
        ]
    ])


def car_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["Личный автомобиль", "Семейный автомобиль", "Нет"],
        "uz": ["Shaxsiy avtomobil", "Oilaviy avtomobil", "Yo'q"],
    }
    values = ["personal", "family", "none"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"car:{values[i]}")]
        for i in range(3)
    ])


def residence_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": [
            "🇺🇿 Узбекистан", "🇷🇺 СНГ", "🇺🇸 США (Грин карта/Гражданство)",
            "🌍 Европа", "🟡 Вид на жительство", "🔵 Гражданство (другая страна)",
            "🌏 Другая страна",
        ],
        "uz": [
            "🇺🇿 O'zbekiston", "🇷🇺 MDH", "🇺🇸 AQSH (Green karta/Fuqarolik)",
            "🌍 Yevropa", "🟡 Yashash huquqi", "🔵 Fuqarolik (boshqa davlat)",
            "🌏 Boshqa davlat",
        ],
    }
    values = ["uzbekistan", "cis", "usa", "europe", "residence_permit", "citizenship_other", "other_country"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"res:{values[i]}")]
        for i in range(7)
    ])


def search_scope_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🇺🇿 Только в Узбекистане", "🌍 В зарубежье (диаспора)", "🔍 Везде — без ограничений"],
        "uz": ["🇺🇿 Faqat O'zbekistonda", "🌍 Chet elda (diaspora)", "🔍 Hamma joyda — cheklovsiz"],
    }
    values = ["uzbekistan_only", "diaspora", "anywhere"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"scope:{values[i]}")]
        for i in range(3)
    ])


def diaspora_country_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🇷🇺 СНГ", "🇺🇸 США", "🌍 Европа", "🌏 Другая страна"],
        "uz": ["🇷🇺 MDH", "🇺🇸 AQSH", "🌍 Yevropa", "🌏 Boshqa davlat"],
    }
    values = ["cis", "usa", "europe", "other_country"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=labels.get(lang, labels["ru"])[0], callback_data="dcountry:cis"),
            InlineKeyboardButton(text=labels.get(lang, labels["ru"])[1], callback_data="dcountry:usa"),
        ],
        [
            InlineKeyboardButton(text=labels.get(lang, labels["ru"])[2], callback_data="dcountry:europe"),
            InlineKeyboardButton(text=labels.get(lang, labels["ru"])[3], callback_data="dcountry:other_country"),
        ],
    ])


def region_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return city_kb(lang)  # same cities as regions


_NAT_MAIN_KEYS = ["uzbek", "russian", "tajik", "kazakh", "korean"]
_NAT_MORE_KEYS = ["karakalpak", "tatar", "uyghur", "turkish", "kyrgyz", "turkmen"]


def _nat_label(key: str, lang: str) -> str:
    from bot.utils.helpers import nationality_label
    return nationality_label(key, lang)


def nationality_main_rows(lang: str, prefix: str, *, show_any: bool = False) -> list:
    """5 национальностей + «🌍 Другая» (→ подменю) + опц. «✅ Не важно».

    prefix задаёт scheme callback-ов: nat / editnat / reqnat / fval:nationality.
    """
    rows: list = []
    pair: list = []
    for key in _NAT_MAIN_KEYS:
        pair.append(InlineKeyboardButton(text=_nat_label(key, lang), callback_data=f"{prefix}:{key}"))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    other_label = "🌍 Другая" if lang != "uz" else "🌍 Boshqa"
    pair.append(InlineKeyboardButton(text=other_label, callback_data=f"{prefix}:more"))
    rows.append(pair)
    if show_any:
        any_label = "✅ Не важно" if lang != "uz" else "✅ Muhim emas"
        rows.append([InlineKeyboardButton(text=any_label, callback_data=f"{prefix}:any")])
    return rows


def nationality_more_rows(lang: str, prefix: str, *, show_custom: bool = True) -> list:
    """6 национальностей подменю + опц. «✍️ Ввести свою» + «🔙 Назад» (→ главное)."""
    rows: list = []
    pair: list = []
    for key in _NAT_MORE_KEYS:
        pair.append(InlineKeyboardButton(text=_nat_label(key, lang), callback_data=f"{prefix}:{key}"))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    if show_custom:
        custom = "✍️ Ввести свою" if lang != "uz" else "✍️ O'zingiz kiriting"
        rows.append([InlineKeyboardButton(text=custom, callback_data=f"{prefix}:custom")])
    back = "🔙 Назад" if lang != "uz" else "🔙 Orqaga"
    rows.append([InlineKeyboardButton(text=back, callback_data=f"{prefix}:back")])
    return rows


def nationality_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=nationality_main_rows(lang, "nat"))


def nationality_more_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=nationality_more_rows(lang, "nat"))


def family_position_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["Старший ребёнок", "Средний ребёнок", "Младший ребёнок", "Единственный ребёнок"],
        "uz": ["Katta farzand", "O'rta farzand", "Kichik farzand", "Yagona farzand"],
    }
    values = ["oldest", "middle", "youngest", "only"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"fpos:{values[i]}")]
        for i in range(4)
    ])


def religiosity_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🕌 Практикующий/ая", "☪️ Умеренный/ая", "🌐 Светский/ая"],
        "uz": ["🕌 Amaliyotchi", "☪️ Mo'tadil", "🌐 Dunyoviy"],
    }
    values = ["practicing", "moderate", "secular"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"rel:{values[i]}")]
        for i in range(3)
    ])


def marital_kb(lang: str = "ru", is_male: bool = True) -> InlineKeyboardMarkup:
    """Шаг 1: семейное положение (3 кнопки)."""
    if is_male:
        labels = {
            "ru": ["💍 Не был женат", "💔 Разведён", "🕊 Вдовец"],
            "uz": ["💍 Uylanmagan", "💔 Ajrashgan", "🕊 Beva"],
        }
    else:
        labels = {
            "ru": ["💍 Не была замужем", "💔 Разведена", "🕊 Вдова"],
            "uz": ["💍 Turmush qurmagan", "💔 Ajrashgan", "🕊 Beva"],
        }
    values = ["never_married", "divorced", "widowed"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"mar:{values[i]}")]
        for i in range(3)
    ])


def children_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Шаг 2: дети (2 кнопки, только если разведён/вдовец)."""
    if lang == "uz":
        opts = [
            ("👶 Farzand yo'q", "child:no"),
            ("👨\u200d👧 Farzand bor", "child:yes"),
        ]
    else:
        opts = [
            ("👶 Детей нет", "child:no"),
            ("👨\u200d👧 Есть дети", "child:yes"),
        ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=cd)] for label, cd in opts
    ])


def skip_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_skip", lang), callback_data="skip")],
    ])


def back_step_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back_step")],
    ])


def skip_back_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Этап 1: текстовый вопрос с [⏭ Пропустить] [← Назад] (back_step)."""
    skip = "⏭ O'tkazib yuborish" if lang == "uz" else "⏭ Пропустить"
    back = "← Orqaga" if lang == "uz" else "← Назад"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=skip, callback_data="skip")],
        [InlineKeyboardButton(text=back, callback_data="back_step")],
    ])


def work_choice_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["💼 Указать место работы", "⏭ Не важно / пропустить"],
        "uz": ["💼 Ish joyini ko'rsatish", "⏭ Muhim emas / o'tkazish"],
    }
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[0], callback_data="work:specify")],
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[1], callback_data="work:skip")],
    ])


def body_type_kb(lang: str = "ru", gender: str = "son") -> InlineKeyboardMarkup:
    """Клавиатура телосложения — gender-aware labels."""
    if gender == "son":
        labels = {
            "ru": ["🪶 Стройный", "🍃 Среднее", "🏃 Спортивный", "🌳 Плотный"],
            "uz": ["🪶 Ozg'in", "🍃 O'rtacha", "🏃 Sportchilarga xos", "🌳 To'ladan kelgan"],
        }
    else:
        labels = {
            "ru": ["🪶 Стройная", "🍃 Среднее", "🏃 Спортивная", "🌳 Плотная"],
            "uz": ["🪶 Ozg'in", "🍃 O'rtacha", "🏃 Sportchilarga xos", "🌳 To'ladan kelgan"],
        }
    values = ["slim", "average", "athletic", "full"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"body:{values[i]}")]
        for i in range(4)
    ])


def occupation_kb(lang: str = "ru", gender: str = "son") -> InlineKeyboardMarkup:
    """Клавиатура занятости — gender-aware, кнопки вместо текста."""
    if gender == "son":
        if lang == "uz":
            opts = [
                ("💼 Ishlaydi", "occ:works"),
                ("🏛 Talaba", "occ:student"),
                ("📈 O'z biznesi bor", "occ:business"),
                ("📌 Boshqa", "occ:other"),
            ]
        else:
            opts = [
                ("💼 Работает", "occ:works"),
                ("🏛 Студент", "occ:student"),
                ("📈 Свой бизнес", "occ:business"),
                ("📌 Другое", "occ:other"),
            ]
    else:
        if lang == "uz":
            opts = [
                ("💼 Ishlaydi", "occ:works"),
                ("🏛 Talaba", "occ:student"),
                ("📈 O'z biznesi bor", "occ:business"),
                ("🌸 Uy bekasi", "occ:housewife"),
                ("📌 Boshqa", "occ:other"),
            ]
        else:
            opts = [
                ("💼 Работает", "occ:works"),
                ("🏛 Студентка", "occ:student"),
                ("📈 Свой бизнес", "occ:business"),
                ("🌸 Домохозяйка", "occ:housewife"),
                ("📌 Другое", "occ:other"),
            ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=cd)] for label, cd in opts
    ])


def photo_type_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🖼 Обычное фото", "😊 Фото с закрытым лицом", "👤 Силуэт / в полный рост", "⏭ Без фото"],
        "uz": ["🖼 Oddiy fotosurat", "😊 Yuz yopilgan fotosurat", "👤 Siluet / to'liq bo'y", "⏭ Fotosuratisiz"],
    }
    values = ["regular", "closed_face", "silhouette", "none"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"photo:{values[i]}")]
        for i in range(4)
    ])


def location_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_send_map_link", lang), callback_data="loc:link")],
        [InlineKeyboardButton(text=t("btn_skip", lang), callback_data="loc:skip")],
    ])


def location_reply_kb(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("btn_send_location", lang), request_location=True)],
            [KeyboardButton(text=t("btn_skip", lang))],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def profile_status_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🟢 В активном поиске", "⏸ Пауза (временно скрыть)"],
        "uz": ["🟢 Faol qidiruvda", "⏸ Pauza (vaqtincha yashirish)"],
    }
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[0], callback_data="status:active")],
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[1], callback_data="status:paused")],
    ])


def anketa_finish_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Экран завершения Этапа 1: предпросмотр / опубликовать / дополнить."""
    if lang == "uz":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👁 Anketani ko'rish", callback_data="profile:preview")],
            [InlineKeyboardButton(text="🚀 Moderatorga yuborish", callback_data="profile:publish")],
            [InlineKeyboardButton(text="✨ Anketani boyitish", callback_data="profile:enhance")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Посмотреть анкету", callback_data="profile:preview")],
        [InlineKeyboardButton(text="🚀 Отправить на публикацию", callback_data="profile:publish")],
        [InlineKeyboardButton(text="✨ Сделать анкету ярче", callback_data="profile:enhance")],
    ])


def enhance_or_publish_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """После описания Этапа 2: дополнить сейчас или опубликовать."""
    back_text = "← Orqaga" if lang == "uz" else "← Назад"
    if lang == "uz":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Hozir to'ldirish", callback_data="ext:start")],
            [InlineKeyboardButton(text="🚀 Shundayicha nashr etish", callback_data="profile:confirm")],
            [InlineKeyboardButton(text=back_text, callback_data="profile:back_enhance")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Дополнить сейчас", callback_data="ext:start")],
        [InlineKeyboardButton(text="🚀 Опубликовать как есть", callback_data="profile:confirm")],
        [InlineKeyboardButton(text=back_text, callback_data="profile:back_enhance")],
    ])


def after_publish_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """После публикации — предложить дополнить."""
    if lang == "uz":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✨ Anketani boyitish", callback_data="after:extend")],
            [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="menu:main")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✨ Дополнить анкету", callback_data="after:extend")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu:main")],
    ])


# ── City keyboard (questionnaire step 6) ──

def city_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Шаг 1: Выбор страны (9 опций, по 1 в ряд)."""
    if lang == "uz":
        opts = [
            ("🇺🇿 O'zbekiston",   "city:uzbekistan"),
            ("🇺🇸 AQSH",          "city:usa"),
            ("🇷🇺 Rossiya",       "city:russia"),
            ("🇰🇿 Qozog'iston",   "city:kazakhstan"),
            ("🇰🇬 Qirg'iziston",  "city:kyrgyzstan"),
            ("🇹🇯 Tojikiston",    "city:tajikistan"),
            ("🇹🇲 Turkmaniston",  "city:turkmenistan"),
            ("🌍 Yevropa",        "city:europe"),
        ]
    else:
        opts = [
            ("🇺🇿 Узбекистан",    "city:uzbekistan"),
            ("🇺🇸 США",           "city:usa"),
            ("🇷🇺 Россия",        "city:russia"),
            ("🇰🇿 Казахстан",     "city:kazakhstan"),
            ("🇰🇬 Кыргызстан",    "city:kyrgyzstan"),
            ("🇹🇯 Таджикистан",   "city:tajikistan"),
            ("🇹🇲 Туркменистан",  "city:turkmenistan"),
            ("🌍 Европа",         "city:europe"),
        ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts
    ])


def uz_regions_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Шаг 2: Выбор области Узбекистана (13 опций, по 2 в ряд) + Назад."""
    if lang == "uz":
        opts = [
            ("🏙 Toshkent (shahar)",  "region:tashkent"),
            ("🌆 Toshkent viloyati",  "region:tashkent_region"),
            ("🏛 Samarqand",          "region:samarkand"),
            ("🌸 Farg'ona",           "region:fergana"),
            ("🌿 Andijon",            "region:andijan"),
            ("🏔 Namangan",           "region:namangan"),
            ("🏜 Buxoro",            "region:bukhara"),
            ("🌾 Qashqadaryo",        "region:kashkadarya"),
            ("🏕 Surxondaryo",        "region:surkhandarya"),
            ("🌊 Xorazm",            "region:khorezm"),
            ("🏝 Qoraqalpog'iston",  "region:karakalpakstan"),
            ("🌄 Jizzax",            "region:jizzakh"),
            ("🌻 Sirdaryo",          "region:sirdarya"),
        ]
        back_text = "🔙 Orqaga"
    else:
        opts = [
            ("🏙 Ташкент (город)",    "region:tashkent"),
            ("🌆 Ташкентская обл.",   "region:tashkent_region"),
            ("🏛 Самарканд",          "region:samarkand"),
            ("🌸 Фергана",            "region:fergana"),
            ("🌿 Андижан",            "region:andijan"),
            ("🏔 Наманган",           "region:namangan"),
            ("🏜 Бухара",             "region:bukhara"),
            ("🌾 Кашкадарья",         "region:kashkadarya"),
            ("🏕 Сурхандарья",        "region:surkhandarya"),
            ("🌊 Хорезм",             "region:khorezm"),
            ("🏝 Каракалпакстан",     "region:karakalpakstan"),
            ("🌄 Джизак",             "region:jizzakh"),
            ("🌻 Сырдарья",           "region:sirdarya"),
        ]
        back_text = "🔙 Назад"

    buttons = []
    for i in range(0, len(opts), 2):
        row = [InlineKeyboardButton(text=opts[i][0], callback_data=opts[i][1])]
        if i + 1 < len(opts):
            row.append(InlineKeyboardButton(text=opts[i + 1][0], callback_data=opts[i + 1][1]))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=back_text, callback_data="city_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def city_regions_uz_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Выбор региона Узбекистана (после выбора 🇺🇿)."""
    if lang == "uz":
        opts = [
            ("Toshkent",   "city:tashkent"),
            ("Samarqand",  "city:samarkand"),
            ("Farg'ona",   "city:fergana"),
            ("Buxoro",     "city:bukhara"),
            ("Namangan",   "city:namangan"),
            ("Andijon",    "city:andijan"),
            ("Nukus",      "city:nukus"),
            ("Boshqa",     "city:uz_other"),
        ]
    else:
        opts = [
            ("Ташкент",    "city:tashkent"),
            ("Самарканд",  "city:samarkand"),
            ("Фергана",    "city:fergana"),
            ("Бухара",     "city:bukhara"),
            ("Наманган",   "city:namangan"),
            ("Андижан",    "city:andijan"),
            ("Нукус",      "city:nukus"),
            ("Другой",     "city:uz_other"),
        ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=opts[0][0], callback_data=opts[0][1]),
         InlineKeyboardButton(text=opts[1][0], callback_data=opts[1][1])],
        [InlineKeyboardButton(text=opts[2][0], callback_data=opts[2][1]),
         InlineKeyboardButton(text=opts[3][0], callback_data=opts[3][1])],
        [InlineKeyboardButton(text=opts[4][0], callback_data=opts[4][1]),
         InlineKeyboardButton(text=opts[5][0], callback_data=opts[5][1])],
        [InlineKeyboardButton(text=opts[6][0], callback_data=opts[6][1]),
         InlineKeyboardButton(text=opts[7][0], callback_data=opts[7][1])],
    ])


# ── Requirements keyboards ──

def req_age_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["18–23", "24–27", "28–35", "36–45", "45+", "Не важно"],
        "uz": ["18–23", "24–27", "28–35", "36–45", "45+", "Muhim emas"],
    }
    values = ["age_18_23", "age_24_27", "age_28_35", "age_36_45", "age_45_plus", "age_any"]
    rows = []
    for i in range(0, len(values), 3):
        row = [
            InlineKeyboardButton(text=labels.get(lang, labels["ru"])[j], callback_data=values[j])
            for j in range(i, min(i + 3, len(values)))
        ]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def req_education_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🎓 Высшее обязательно", "📖 Среднее специальное", "✅ Не важно"],
        "uz": ["🎓 Oliy majburiy", "📖 O'rta maxsus", "✅ Muhim emas"],
    }
    values = ["higher", "vocational", "any"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"reqedu:{values[i]}")]
        for i in range(3)
    ])


def req_residence_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🇺🇿 Узбекистан", "🇷🇺 СНГ", "🇺🇸 США", "🌍 Европа", "🟡 ВНЖ", "🔵 Гражданство", "✅ Не важно"],
        "uz": ["🇺🇿 O'zbekiston", "🇷🇺 MDH", "🇺🇸 AQSH", "🌍 Yevropa", "🟡 YHQ", "🔵 Fuqarolik", "✅ Muhim emas"],
    }
    values = ["uzbekistan", "cis", "usa", "europe", "residence_permit", "citizenship_other", "any"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"reqres:{values[i]}")]
        for i in range(7)
    ])


def req_residence_simple_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🇺🇿 Узбекистан", "🌍 Другое", "⏭ Пропустить"],
        "uz": ["🇺🇿 O'zbekiston", "🌍 Boshqa", "⏭ O'tkazib yuborish"],
    }
    values = ["rres_uzb", "rres_other", "rres_skip"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=values[i])]
        for i in range(3)
    ])


def req_residence_regions_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["Ташкент", "Самарканд", "Фергана", "Бухара", "Наманган", "Андижан", "Нукус", "Любой"],
        "uz": ["Toshkent", "Samarqand", "Farg'ona", "Buxoro", "Namangan", "Andijon", "Nukus", "Har qanday"],
    }
    values = ["rregion_tashkent", "rregion_samarkand", "rregion_fergana", "rregion_bukhara",
              "rregion_namangan", "rregion_andijan", "rregion_nukus", "rregion_any"]
    rows = []
    for i in range(0, len(values), 2):
        row = [
            InlineKeyboardButton(text=labels.get(lang, labels["ru"])[j], callback_data=values[j])
            for j in range(i, min(i + 2, len(values)))
        ]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def req_nationality_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=nationality_main_rows(lang, "reqnat", show_any=True))


def req_nationality_more_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=nationality_more_rows(lang, "reqnat"))


def req_religiosity_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🕌 Практикующий", "☪️ Умеренный", "🌐 Светский", "✅ Не важно"],
        "uz": ["🕌 Amaliyotchi", "☪️ Mo'tadil", "🌐 Dunyoviy", "✅ Muhim emas"],
    }
    values = ["practicing", "moderate", "secular", "any"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"reqrel:{values[i]}")]
        for i in range(4)
    ])


def req_marital_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["💍 Только незамужняя", "💔 Рассмотрю разведённую", "🖤 Рассмотрю вдову", "✅ Не важно"],
        "uz": ["💍 Faqat turmushga chiqmagan", "💔 Ajrashganni ko'rib chiqaman", "🖤 Bevani ko'rib chiqaman", "✅ Muhim emas"],
    }
    values = ["never_married", "divorced", "widowed", "any"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"reqmar:{values[i]}")]
        for i in range(4)
    ])


def req_children_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    if lang == "uz":
        opts = [
            ("👶 Farzandsiz", "reqchild:no"),
            ("👶 Farzand bor", "reqchild:yes"),
            ("✅ Muhim emas", "reqchild:any"),
        ]
    else:
        opts = [
            ("👶 Без детей", "reqchild:no"),
            ("👶 Есть дети", "reqchild:yes"),
            ("✅ Не важно", "reqchild:any"),
        ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=txt, callback_data=cb)] for txt, cb in opts
    ])


def req_car_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🚗 Обязательно личный", "🚗 Достаточно семейного", "✅ Не важно"],
        "uz": ["🚗 Shaxsiy majburiy", "🚗 Oilaviy yetarli", "✅ Muhim emas"],
    }
    values = ["personal", "family", "any"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"reqcar:{values[i]}")]
        for i in range(3)
    ])


def req_housing_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🏠 Своё жильё обязательно", "✅ Не важно"],
        "uz": ["🏠 O'z uyi majburiy", "✅ Muhim emas"],
    }
    values = ["own", "any"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"reqhouse:{values[i]}")]
        for i in range(2)
    ])


def req_job_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["💼 Работает обязательно", "✅ Не важно"],
        "uz": ["💼 Ishlashi majburiy", "✅ Muhim emas"],
    }
    values = ["required", "any"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"reqjob:{values[i]}")]
        for i in range(2)
    ])


def confirm_profile_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_confirm", lang), callback_data="profile:confirm")],
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="profile:cancel")],
    ])


# ── Moderator keyboards ──

def mod_review_kb(profile_id: int, is_paused: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура модератора на экране анкеты (на модерации / после публикации)."""
    if is_paused:
        pause_btn = InlineKeyboardButton(
            text="🟢 Активировать",
            callback_data=f"mod:activate:{profile_id}",
        )
    else:
        pause_btn = InlineKeyboardButton(
            text="⏸ Пауза",
            callback_data=f"mod:pause:{profile_id}",
        )
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"mod:publish:{profile_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod:reject:{profile_id}"),
        ],
        [InlineKeyboardButton(text="📸 Отклонить фото", callback_data=f"mod:reject_photo:{profile_id}")],
        [pause_btn],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"mod:edit:{profile_id}")],
        [InlineKeyboardButton(text="⭐ Опубликовать как VIP", callback_data=f"mod:publish_vip:{profile_id}")],
        [InlineKeyboardButton(text="💬 Написать пользователю", callback_data=f"modreply:{profile_id}")],
    ])


def mod_found_kb(profile_id: int, is_published: bool = True, is_vip: bool = False) -> InlineKeyboardMarkup:
    """Кнопки управления после /find — для уже проверенных анкет."""
    rows = []
    # VIP toggle
    if is_vip:
        rows.append([InlineKeyboardButton(text="⭐ Убрать VIP", callback_data=f"modfind:vip_remove:{profile_id}")])
    else:
        rows.append([InlineKeyboardButton(text="⭐ Присвоить VIP", callback_data=f"modfind:vip_add:{profile_id}")])
    if is_published:
        rows.append([InlineKeyboardButton(text="⏸ Поставить на паузу", callback_data=f"modfind:pause:{profile_id}")])
    else:
        rows.append([InlineKeyboardButton(text="🟢 Активировать", callback_data=f"modfind:activate:{profile_id}")])
    rows.append([InlineKeyboardButton(text="❌ Заблокировать анкету", callback_data=f"modfind:block:{profile_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mod_payment_kb(payment_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"modpay:confirm:{payment_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"modpay:reject:{payment_id}"),
        ],
    ])


# ── Search / browsing keyboards ──

def profile_card_kb(
    profile_id: int,
    lang: str = "ru",
    display_id: str = "",
    show_next: bool = True,
    show_prev: bool = False,
    current: int = 0,
    total: int = 0,
) -> InlineKeyboardMarkup:
    """Клавиатура карточки анкеты с двусторонней навигацией.

    current/total — 1-based позиции для счётчика.
    show_prev/show_next — кнопки навигации, скрываются на границах.
    """
    if lang == "uz":
        interest_txt = "💌 Ma'lumotni olish"
        fav_txt = "❤️ Saqlash"
        prev_txt = "⬅️ Orqaga"
        next_txt = "Keyingisi ➡️"
        filters_txt = "🔧 Filtrlarni o'zgartirish"
        menu_txt = "🏠 Menyu"
    else:
        interest_txt = "💌 Узнать контакт"
        fav_txt = "❤️ В избранное"
        prev_txt = "⬅️ Назад"
        next_txt = "Следующая ➡️"
        filters_txt = "🔧 Изменить фильтры"
        menu_txt = "🏠 Меню"

    builder = InlineKeyboardBuilder()

    # 1-й ряд: действие по текущей анкете
    builder.row(InlineKeyboardButton(
        text=interest_txt, callback_data=f"get_contact:{profile_id}"
    ))

    # 2-й ряд: ❤️ В избранное
    builder.row(InlineKeyboardButton(
        text=fav_txt, callback_data=f"fav:{profile_id}"
    ))

    # 3-й ряд: ⬅️ Назад · счётчик · Следующая ➡️
    nav_row: list[InlineKeyboardButton] = []
    if show_prev:
        nav_row.append(InlineKeyboardButton(
            text=prev_txt, callback_data="search_nav:prev"
        ))
    if total > 0:
        nav_row.append(InlineKeyboardButton(
            text=f"📄 {current}/{total}", callback_data="noop"
        ))
    if show_next:
        nav_row.append(InlineKeyboardButton(
            text=next_txt, callback_data="search_nav:next"
        ))
    if nav_row:
        builder.row(*nav_row)

    # 4-й ряд: фильтры
    builder.row(InlineKeyboardButton(
        text=filters_txt, callback_data="search:manual"
    ))

    # 5-й ряд: меню
    builder.row(InlineKeyboardButton(
        text=menu_txt, callback_data="menu:main"
    ))

    return builder.as_markup()


def get_contact_kb(profile_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка «Получить контакт и адрес» — ведёт к оплате (Шаг 13)."""
    label = "💳 Получить контакт и адрес" if lang == "ru" else "💳 Kontakt va manzil olish"
    back = t("btn_back", lang)
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data=f"getcontact:{profile_id}")],
        [InlineKeyboardButton(text=back, callback_data="back:menu")],
    ])


def search_nav_kb(page: int, total_pages: int, lang: str = "ru") -> InlineKeyboardMarkup:
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"search_page:{page - 1}"))
    buttons.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"search_page:{page + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons, [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back:menu")]])


# ── Search mode keyboards ──

def search_mode_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """3 варианта поиска когда у пользователя есть анкета."""
    buttons = [
        [InlineKeyboardButton(
            text="✅ Mening talablarim bo'yicha" if lang == "uz" else "✅ По моим требованиям",
            callback_data="search:my_req")],
        [InlineKeyboardButton(
            text="🔧 Filtrlarni qo'lda sozlash" if lang == "uz" else "🔧 Настроить фильтры вручную",
            callback_data="search:manual")],
        [InlineKeyboardButton(
            text="👀 Barcha anketalarni ko'rish" if lang == "uz" else "👀 Показать все анкеты",
            callback_data="search:all")],
        *nav_kb(lang, "back:menu"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_no_anketa_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Если нет анкеты — предлагаем создать."""
    buttons = [
        [InlineKeyboardButton(
            text="👦 Anketa joylashtirish" if lang == "uz" else "👦 Разместить анкету сына",
            callback_data="menu:son")],
        [InlineKeyboardButton(
            text="👧 Anketa joylashtirish" if lang == "uz" else "👧 Разместить анкету дочери",
            callback_data="menu:daughter")],
        *nav_kb(lang, "back:menu"),
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _filter_value_label(key: str, value, lang: str, filters: dict) -> str:
    """Человекочитаемое значение фильтра на языке пользователя."""
    L = lang if lang in ("ru", "uz") else "ru"
    vl = {
        "ru": {
            "age": {"18_23": "18–23", "24_27": "24–27", "28_35": "28–35",
                    "36_45": "36–45", "45plus": "45+"},
            "religion": {"practicing": "Практикующий", "moderate": "Умеренный",
                         "secular": "Светский"},
            "education": {"secondary": "Среднее", "vocational": "Среднее спец.",
                          "higher": "Высшее", "studying": "Студент"},
            "residence": {"uzbekistan": "Узбекистан", "cis": "СНГ", "usa": "США",
                          "europe": "Европа", "other_country": "Другое", "other": "Другое",
                          "tashkent": "Ташкент", "samarkand": "Самарканд",
                          "fergana": "Фергана", "bukhara": "Бухара",
                          "namangan": "Наманган", "andijan": "Андижан", "nukus": "Нукус"},
            "nationality": {"uzbek": "Узбек", "russian": "Русский", "korean": "Кореец",
                            "tajik": "Таджик", "kazakh": "Казах", "other": "Другая"},
            "marital": {"never_married": "Не был(а) в браке", "divorced": "Разведён/а",
                        "widowed": "Вдовец/Вдова"},
            "children": {"no": "Без детей", "no_children": "Без детей",
                         "has_children": "Есть дети",
                         "yes_with_me": "Есть", "yes_with_ex": "Есть"},
        },
        "uz": {
            "age": {"18_23": "18–23", "24_27": "24–27", "28_35": "28–35",
                    "36_45": "36–45", "45plus": "45+"},
            "religion": {"practicing": "Amaliyotchi", "moderate": "Mo'tadil",
                         "secular": "Dunyoviy"},
            "education": {"secondary": "O'rta", "vocational": "O'rta maxsus",
                          "higher": "Oliy", "studying": "Talaba"},
            "residence": {"uzbekistan": "O'zbekiston", "cis": "MDH", "usa": "AQSH",
                          "europe": "Yevropa", "other_country": "Boshqa", "other": "Boshqa",
                          "tashkent": "Toshkent", "samarkand": "Samarqand",
                          "fergana": "Farg'ona", "bukhara": "Buxoro",
                          "namangan": "Namangan", "andijan": "Andijon", "nukus": "Nukus"},
            "nationality": {"uzbek": "O'zbek", "russian": "Rus", "korean": "Koreys",
                            "tajik": "Tojik", "kazakh": "Qozoq", "other": "Boshqa"},
            "marital": {"never_married": "Turmush qurmagan", "divorced": "Ajrashgan",
                        "widowed": "Beva"},
            "children": {"no": "Farzandsiz", "no_children": "Farzandsiz",
                         "has_children": "Farzandli",
                         "yes_with_me": "Bor", "yes_with_ex": "Bor"},
        },
    }
    # Специальный случай: возраст из требований (age_from/age_to)
    if key == "age" and "age_from" in filters:
        return f"{filters.get('age_from', '?')}–{filters.get('age_to', '?')}"
    # Специальный случай: регион
    if key == "residence" and "region" in filters:
        return vl[L].get("residence", {}).get(str(filters["region"]), str(filters["region"]))
    return vl[L].get(key, {}).get(str(value), str(value))


def search_filter_kb(lang: str = "ru", filters: dict | None = None) -> InlineKeyboardMarkup:
    """Меню фильтров — выбранные исчезают (показаны текстом), остальные кнопками."""
    if filters is None:
        filters = {}
    is_uz = lang == "uz"

    all_filters = [
        ("age",         "🎂 " + ("Yoshi" if is_uz else "Возраст"),              "filter:age"),
        ("religion",    "🕌 " + ("Dindorligi" if is_uz else "Религиозность"),   "filter:religion"),
        ("education",   "🎓 " + ("Ma'lumoti" if is_uz else "Образование"),      "filter:education"),
        ("residence",   "🏡 " + ("Yashash joyi" if is_uz else "Где проживает"),"filter:residence"),
        ("nationality", "🌍 " + ("Millati" if is_uz else "Национальность"),     "filter:nationality"),
        ("marital",     "💍 " + ("Oilaviy holati" if is_uz else "Семейное положение"), "filter:marital"),
        ("children",    "👶 " + ("Farzandlari" if is_uz else "Наличие детей"),  "filter:children"),
    ]

    age_selected = "age" in filters or "age_from" in filters or "age_to" in filters
    residence_selected = "residence" in filters or "region" in filters

    buttons = []
    for key, label, cb in all_filters:
        # Выбранные — пропускаем (они показаны текстом в сообщении)
        if key == "age" and age_selected:
            continue
        if key == "residence" and residence_selected:
            continue
        if key in filters:
            continue
        # Дети — скрываем если «Не был(а) в браке»
        if key == "children" and filters.get("marital") == "never_married":
            continue
        # Невыбранные — показываем кнопкой
        buttons.append([InlineKeyboardButton(text=label, callback_data=cb)])

    # Кнопка поиска
    buttons.append([InlineKeyboardButton(
        text="🔍 Qidiruvni boshlash" if is_uz else "🔍 Начать поиск",
        callback_data="filter:go",
    )])

    # Сброс — всегда (no-op при пустых фильтрах, зато кнопка стабильно на месте)
    buttons.append([InlineKeyboardButton(
        text="🔄 Filtrlarni tozalash" if is_uz else "🔄 Сбросить фильтры",
        callback_data="filter:clear",
    )])

    buttons.append([InlineKeyboardButton(
        text="← Orqaga" if is_uz else "← Назад",
        callback_data="menu:main",
    )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def filter_option_kb(options: list[tuple[str, str]], lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура выбора значения фильтра. options = [(label, callback_data), ...]"""
    buttons = [[InlineKeyboardButton(text=label, callback_data=cd)] for label, cd in options]
    # «← Назад» возвращает на экран фильтров БЕЗ сброса выбранных фильтров
    buttons.extend(nav_kb(lang, "filter:back"))
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── VIP duration keyboards ──

def _fmt_price(price: int, region: str) -> str:
    if region == "usa":
        return f"${price // 100}"
    return f"{price:,} сум".replace(",", " ")


VIP_DURATIONS = [
    (7,   {"ru": "7 дней",    "uz": "7 kun"}),
    (14,  {"ru": "14 дней",   "uz": "14 kun"}),
    (30,  {"ru": "1 месяц",   "uz": "1 oy"}),
    (90,  {"ru": "3 месяца",  "uz": "3 oy"}),
    (180, {"ru": "6 месяцев", "uz": "6 oy"}),
    (365, {"ru": "1 год",     "uz": "1 yil"}),
]


def _vip_price_for(days: int, region: str) -> int:
    from bot.config import VIP_PRICES_UZB, VIP_PRICES_USD, VIP_PRICES_SNG
    prices = {"uzb": VIP_PRICES_UZB, "sng": VIP_PRICES_SNG, "usa": VIP_PRICES_USD}.get(region, VIP_PRICES_UZB)
    return prices[str(days)]


def vip_duration_kb(
    lang: str = "ru",
    region: str = "uzb",
    *,
    back_cb: str | None = None,
    show_skip: bool = False,
) -> InlineKeyboardMarkup:
    """Выбор срока VIP с ценами для пользователя.

    show_skip=True → добавляет «❌ Без VIP пока» (creation flow).
    back_cb → callback для «🔙 Назад» (upgrade flow). Если None — кнопки назад нет.
    """
    rows: list = []
    pair: list = []
    for days, labels in VIP_DURATIONS:
        price_str = _fmt_price(_vip_price_for(days, region), region)
        text_btn = f"{labels[lang]} — {price_str}"
        pair.append(InlineKeyboardButton(text=text_btn, callback_data=f"vip_dur:{days}"))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)

    if show_skip:
        rows.append([InlineKeyboardButton(text=t("vip_skip_for_now", lang), callback_data="vip:skip")])
    if back_cb:
        back = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
        rows.append([InlineKeyboardButton(text=back, callback_data=back_cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def vip_method_kb(profile_id: int, days: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Выбор способа оплаты VIP: свою карту или связь с модератором."""
    back = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_vip_pay_self", lang),
                              callback_data=f"vip_pay:self:{profile_id}:{days}")],
        [InlineKeyboardButton(text=t("btn_vip_pay_moderator", lang),
                              callback_data=f"vip_pay:moderator:{profile_id}:{days}")],
        [InlineKeyboardButton(text=back, callback_data=f"vip:back_to_duration:{profile_id}")],
    ])


def vip_pay_card_kb(profile_id: int, days: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Экран реквизитов: кнопка 📤 Отправить скриншот + 🔙 Назад."""
    back = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_vip_send_screenshot", lang),
                              callback_data=f"vip_send_ss:{profile_id}:{days}")],
        [InlineKeyboardButton(text=back,
                              callback_data=f"vip:back_to_method:{profile_id}:{days}")],
    ])


def vip_mod_list_kb(requests: list) -> InlineKeyboardMarkup:
    """Список PENDING VipRequest для модератора (/vip)."""
    rows = []
    for r in requests:
        days_label = f"{r.days} дн"
        rows.append([InlineKeyboardButton(
            text=f"{r.display_id or '—'} · {days_label}",
            callback_data=f"vipmod:view:{r.id}",
        )])
    if not rows:
        rows.append([InlineKeyboardButton(text="Нет заявок", callback_data="noop")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def vip_mod_card_kb(req_id: int) -> InlineKeyboardMarkup:
    """Карточка VIP-заявки для модератора: ✅ / ❌ / 🔙 к списку."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"vipmod:confirm:{req_id}")],
        [InlineKeyboardButton(text="❌ Отклонить",   callback_data=f"vipmod:reject:{req_id}")],
        [InlineKeyboardButton(text="🔙 К списку",    callback_data="vipmod:list")],
    ])


def vip_moderator_intro_kb(profile_id: int, days: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Путь Б — экран с реквизитами: задать вопрос / прислать скриншот / назад."""
    back = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_vip_ask_question", lang),
                              callback_data=f"vip_ask:{profile_id}:{days}")],
        [InlineKeyboardButton(text=t("btn_vip_send_screenshot", lang),
                              callback_data=f"vip_ss_moderator:{profile_id}:{days}")],
        [InlineKeyboardButton(text=back,
                              callback_data=f"vip:back_to_method:{profile_id}:{days}")],
    ])


def vip_after_reply_kb(profile_id: int, days: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """После ответа модератора — задать ещё / прислать скриншот / в меню."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_vip_ask_more", lang),
                              callback_data=f"vip_ask:{profile_id}:{days}")],
        [InlineKeyboardButton(text=t("btn_vip_send_screenshot", lang),
                              callback_data=f"vip_ss_moderator:{profile_id}:{days}")],
        [InlineKeyboardButton(text=t("btn_vip_home", lang),
                              callback_data="menu:main")],
    ])


def vip_mod_reply_kb(req_id: int) -> InlineKeyboardMarkup:
    """Модератору: одна кнопка «💬 Ответить» под VIP-вопросом пользователя."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Ответить", callback_data=f"vipmod:reply:{req_id}")],
    ])


def mod_vip_duration_kb(profile_id: int) -> InlineKeyboardMarkup:
    """Выбор срока VIP модератором."""
    durations = [
        (7, "7 дней"), (14, "14 дней"), (30, "1 месяц"),
        (90, "3 месяца"), (180, "6 месяцев"), (365, "1 год"),
    ]
    rows = []
    pair = []
    for days, label in durations:
        pair.append(InlineKeyboardButton(text=label, callback_data=f"modvip:{days}:{profile_id}"))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="back:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Payment keyboards ──

def payment_uz_kb(profile_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏦 Перевод на карту (30,000 сум)" if lang == "ru" else "🏦 Kartaga o'tkazma (30,000 so'm)",
            callback_data=f"pay:card:{profile_id}",
        )],
        [InlineKeyboardButton(
            text="💬 Через модератора" if lang == "ru" else "💬 Moderator orqali",
            callback_data=f"pay:moderator:{profile_id}",
        )],
    ])


def payment_cis_kb(profile_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏦 Перевод на карту (30,000 сум)" if lang == "ru" else "🏦 Kartaga o'tkazma (30,000 so'm)",
            callback_data=f"pay:card:{profile_id}",
        )],
        [InlineKeyboardButton(
            text="💬 Через модератора" if lang == "ru" else "💬 Moderator orqali",
            callback_data=f"pay:moderator:{profile_id}",
        )],
    ])


def payment_intl_kb(profile_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏦 Оплата картой ($15)" if lang == "ru" else "🏦 Karta orqali to'lov ($15)",
            callback_data=f"pay:card:{profile_id}",
        )],
        [InlineKeyboardButton(
            text="💬 Через модератора" if lang == "ru" else "💬 Moderator orqali",
            callback_data=f"pay:moderator:{profile_id}",
        )],
    ])


# ── Meeting keyboard ──

def meeting_skip_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    label = "⏭ Свяжусь сам" if lang == "ru" else "⏭ O'zim bog'lanaman"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=label, callback_data="meeting:skip")],
    ])


# ── Feedback keyboards ──

def feedback_kb(profile_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["💍 Никох состоялся — Альхамдулиллах!", "🤝 Продолжаем общение", "💬 Ещё думаем", "❌ Не подошли"],
        "uz": ["💍 Nikoh bo'ldi — Alhamdulillah!", "🤝 Muloqotni davom ettiramiz", "💬 Hali o'ylayapmiz", "❌ Mos kelmadi"],
    }
    values = ["nikoh", "talking", "thinking", "not_matched"]
    l = labels.get(lang, labels["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=l[i], callback_data=f"fb:{values[i]}:{profile_id}")]
        for i in range(4)
    ])


def feedback_story_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {"ru": ["✅ Да, поделиться", "❌ Нет, спасибо"], "uz": ["✅ Ha, baham ko'rish", "❌ Yo'q, rahmat"]}
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[0], callback_data="story:yes")],
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[1], callback_data="story:no")],
    ])


# ── Complaint keyboards ──

def complaint_reason_kb(profile_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["❗ Данные не соответствуют", "🤖 Подозрительная / фейковая", "📸 Чужое фото", "⚠️ Некорректное поведение", "📵 Другая причина"],
        "uz": ["❗ Ma'lumotlar mos emas", "🤖 Shubhali / soxta", "📸 Begona fotosurat", "⚠️ Noto'g'ri xulq", "📵 Boshqa sabab"],
    }
    values = ["wrong_data", "suspicious", "stolen_photo", "bad_behavior", "other"]
    l = labels.get(lang, labels["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=l[i], callback_data=f"complaint:{values[i]}:{profile_id}")]
        for i in range(5)
    ])


# ── My applications keyboard ──

def edit_education_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура образования для редактирования (prefix editedu:)."""
    labels = {
        "ru": ["Среднее", "Среднее специальное", "Высшее", "Студент/ка"],
        "uz": ["O'rta", "O'rta maxsus", "Oliy", "Talaba"],
    }
    values = ["secondary", "vocational", "higher", "studying"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"editedu:{values[i]}")]
        for i in range(4)
    ])


def edit_religiosity_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура религиозности для редактирования (prefix editrel:)."""
    labels = {
        "ru": ["🕌 Практикующий", "Умеренный", "Светский"],
        "uz": ["🕌 Amaliyotchi", "Mo'tadil", "Dunyoviy"],
    }
    values = ["practicing", "moderate", "secular"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"editrel:{values[i]}")]
        for i in range(3)
    ])


def edit_marital_kb(lang: str = "ru", is_male: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура семейного положения для редактирования (prefix editmar:)."""
    if is_male:
        labels = {
            "ru": ["Не был женат", "Разведён", "Вдовец"],
            "uz": ["Hech uylanmagan", "Ajrashgan", "Beva"],
        }
    else:
        labels = {
            "ru": ["Не была замужем", "Разведена", "Вдова"],
            "uz": ["Hech turmushga chiqmagan", "Ajrashgan", "Beva"],
        }
    values = ["never_married", "divorced", "widowed"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"editmar:{values[i]}")]
        for i in range(3)
    ])


def edit_nationality_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура национальностей для редактирования (prefix editnat:)."""
    return InlineKeyboardMarkup(inline_keyboard=nationality_main_rows(lang, "editnat"))


def edit_nationality_more_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=nationality_more_rows(lang, "editnat"))


def edit_profile_kb(profile_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Меню редактирования — список полей для изменения."""
    if lang == "uz":
        fields = [
            ("👤 Ism", "edit:name"),
            ("🗓 Tug'ilgan yili", "edit:birth_year"),
            ("📏 Bo'yi / Vazni", "edit:height_weight"),
            ("👥 Millat", "edit:nationality"),
            ("🏙 Shahar va tuman", "edit:city"),
            ("🎓 Ma'lumoti", "edit:education"),
            ("💼 Ish joyi", "edit:occupation"),
            ("🕌 Dindorlik", "edit:religiosity"),
            ("💍 Oilaviy holat", "edit:marital"),
            ("📸 Fotosurat", "edit:photo"),
            ("📞 Ota-onalar telefoni", "edit:phone"),
            ("📱 Ota-onalar TG", "edit:parent_telegram"),
            ("💬 Nomzod TG", "edit:candidate_telegram"),
            ("👨‍💼 Otasi", "edit:father"),
            ("👩‍💼 Onasi", "edit:mother"),
            ("👨‍👩‍👧 Aka-uka / opa-singil", "edit:siblings"),
            ("🌸 Xarakter", "edit:character"),
            ("🌿 Sog'lig'i", "edit:health"),
            ("💭 O'zi haqida", "edit:about"),
            ("🏡 Turar joy", "edit:housing"),
            ("🚗 Avtomobil", "edit:car"),
            ("🏠 Manzil", "edit:address"),
        ]
        back_text = "🔙 Ortga"
    else:
        fields = [
            ("👤 Имя", "edit:name"),
            ("🗓 Год рождения", "edit:birth_year"),
            ("📏 Рост / Вес", "edit:height_weight"),
            ("👥 Национальность", "edit:nationality"),
            ("🏙 Город и район", "edit:city"),
            ("🎓 Образование", "edit:education"),
            ("💼 Работа", "edit:occupation"),
            ("🕌 Религиозность", "edit:religiosity"),
            ("💍 Семейное положение", "edit:marital"),
            ("📸 Фото", "edit:photo"),
            ("📞 Телефон родителей", "edit:phone"),
            ("📱 TG родителей", "edit:parent_telegram"),
            ("💬 TG кандидата", "edit:candidate_telegram"),
            ("👨‍💼 Отец", "edit:father"),
            ("👩‍💼 Мать", "edit:mother"),
            ("👨‍👩‍👧 Братья / сёстры", "edit:siblings"),
            ("🌸 Характер", "edit:character"),
            ("🌿 Здоровье", "edit:health"),
            ("💭 О себе", "edit:about"),
            ("🏡 Жильё", "edit:housing"),
            ("🚗 Автомобиль", "edit:car"),
            ("🏠 Адрес", "edit:address"),
        ]
        back_text = "🔙 Назад"
    rows = [[InlineKeyboardButton(text=label, callback_data=f"{cd}:{profile_id}")] for label, cd in fields]
    rows.extend(nav_kb(lang, "menu:my"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ══════════════════════════════════════
# Новое меню редактирования: хаб + 2 раздела
# ══════════════════════════════════════

# Локальные label-мапы для форматирования значений (не импортируем из tariff.py — cross-dep)
_EDIT_BODY_LABELS = {
    "ru": {"slim": "Стройное", "average": "Среднее", "athletic": "Спортивное", "full": "Плотное"},
    "uz": {"slim": "Ozg'in", "average": "O'rtacha", "athletic": "Sportchilarga xos", "full": "To'ladan kelgan"},
}
_EDIT_EDU_LABELS = {
    "ru": {"secondary": "Среднее", "vocational": "Среднее спец.", "higher": "Высшее", "studying": "Студент/ка"},
    "uz": {"secondary": "O'rta", "vocational": "O'rta maxsus", "higher": "Oliy", "studying": "Talaba"},
}
_EDIT_REL_LABELS = {
    "ru": {"practicing": "Практикующий/ая", "moderate": "Умеренный/ая", "secular": "Светский/ая"},
    "uz": {"practicing": "Amaliyotchi", "moderate": "Mo'tadil", "secular": "Dunyoviy"},
}
_EDIT_MAR_LABELS = {
    "ru": {"never_married": "Не был(а) в браке", "divorced": "Разведён/а", "widowed": "Вдовец/Вдова"},
    "uz": {"never_married": "Turmush qurmagan", "divorced": "Ajrashgan", "widowed": "Beva"},
}
_EDIT_HOUSING_LABELS = {
    "ru": {"own_house": "Свой дом", "own_apartment": "Своя квартира",
           "with_parents": "С родителями", "rent": "Аренда"},
    "uz": {"own_house": "O'z uyi", "own_apartment": "O'z kvartirasi",
           "with_parents": "Ota-ona bilan", "rent": "Ijara"},
}
_EDIT_PHOUSING_LABELS = {
    "ru": {"house": "Дом", "apartment": "Квартира"},
    "uz": {"house": "Uy", "apartment": "Kvartira"},
}
_EDIT_CAR_LABELS = {
    "ru": {"personal": "Личный", "family": "Семейный", "none": "Нет"},
    "uz": {"personal": "Shaxsiy", "family": "Oilaviy", "none": "Yo'q"},
}
_EDIT_FPOS_SHORT = {
    "ru": {"oldest": "старший", "middle": "средний", "youngest": "младший", "only": "единств."},
    "uz": {"oldest": "katta", "middle": "o'rta", "youngest": "kenja", "only": "yagona"},
}


def _enum_value(v):
    """Вернуть .value для enum или сам объект."""
    return v.value if hasattr(v, "value") else v


def _truncate(s: str, limit: int = 25) -> str:
    return s if len(s) <= limit else s[:limit - 3] + "..."


def _mask_phone(phone: str) -> str:
    """+998901234567 → +998**...67"""
    if not phone:
        return ""
    if len(phone) < 4:
        return phone
    return phone[:4] + "**..." + phone[-2:]


def _format_edit_value(field: str, profile, lang: str) -> str:
    """Форматирует текущее значение поля для кнопки меню редактирования."""
    L = lang if lang in ("ru", "uz") else "ru"
    dash = t("edit_not_specified", L)
    filled = t("edit_filled", L)
    not_filled = t("edit_not_filled", L)

    if profile is None:
        return dash

    if field == "name":
        return _truncate(profile.name or dash)
    if field == "birth_year":
        return str(profile.birth_year) if profile.birth_year else dash
    if field == "height_weight":
        h, w = profile.height_cm, profile.weight_kg
        if h and w:
            return f"{h} / {w}"
        if h:
            return f"{h} / —"
        if w:
            return f"— / {w}"
        return dash
    if field == "nationality":
        from bot.utils.helpers import nationality_label
        return _truncate(nationality_label(profile.nationality, L) if profile.nationality else dash)
    if field == "city":
        city, district = profile.city, profile.district
        if city and district:
            return _truncate(f"{city}, {district}")
        return _truncate(city or dash)
    if field == "education":
        edu = _enum_value(profile.education)
        label = _EDIT_EDU_LABELS.get(L, _EDIT_EDU_LABELS["ru"]).get(edu, dash)
        return _truncate(label)
    if field == "occupation":
        from bot.utils.helpers import occupation_label
        return _truncate(occupation_label(profile.occupation, L) if profile.occupation else dash)
    if field == "religiosity":
        rel = _enum_value(profile.religiosity)
        return _EDIT_REL_LABELS.get(L, _EDIT_REL_LABELS["ru"]).get(rel, dash)
    if field == "marital":
        mar = _enum_value(profile.marital_status)
        return _EDIT_MAR_LABELS.get(L, _EDIT_MAR_LABELS["ru"]).get(mar, dash)
    if field == "photo":
        return t("edit_photo_uploaded", L) if profile.photo_file_id else t("edit_photo_not_uploaded", L)
    if field == "phone":
        return _mask_phone(profile.parent_phone) if profile.parent_phone else dash
    if field == "parent_telegram":
        return _truncate(profile.parent_telegram or dash)
    if field == "candidate_telegram":
        return _truncate(profile.candidate_telegram or dash)
    if field == "address":
        if profile.address:
            return _truncate(profile.address)
        if profile.location_link:
            return "🗺 Карта" if L == "ru" else "🗺 Karta"
        return dash
    # ── Family ──
    if field == "father":
        return _truncate(profile.father_occupation or dash)
    if field == "mother":
        return _truncate(profile.mother_occupation or dash)
    if field == "siblings":
        b = profile.brothers_count if profile.brothers_count is not None else 0
        s = profile.sisters_count if profile.sisters_count is not None else 0
        pos = _enum_value(profile.family_position)
        pos_short = _EDIT_FPOS_SHORT.get(L, _EDIT_FPOS_SHORT["ru"]).get(pos) if pos else None
        if pos_short:
            base = f"{b} бр. / {s} с. · {pos_short}" if L == "ru" else f"{b} a-u / {s} o-s · {pos_short}"
        else:
            base = f"{b} бр. / {s} с." if L == "ru" else f"{b} a-u / {s} o-s"
        return _truncate(base)
    if field == "character":
        return filled if (profile.character_hobbies or "").strip() else not_filled
    if field == "health":
        return filled if (profile.health_notes or "").strip() else not_filled
    if field == "about":
        return filled if (profile.ideal_family_life or "").strip() else not_filled
    if field == "housing":
        h = _enum_value(profile.housing)
        label = _EDIT_HOUSING_LABELS.get(L, _EDIT_HOUSING_LABELS["ru"]).get(h, dash)
        if h == "with_parents" and profile.parent_housing_type:
            ph = _enum_value(profile.parent_housing_type)
            ph_label = _EDIT_PHOUSING_LABELS.get(L, _EDIT_PHOUSING_LABELS["ru"]).get(ph)
            if ph_label:
                label = f"{label} ({ph_label.lower()})"
        return _truncate(label)
    if field == "car":
        c = _enum_value(profile.car)
        return _EDIT_CAR_LABELS.get(L, _EDIT_CAR_LABELS["ru"]).get(c, dash)

    return dash


def edit_hub_kb(profile_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Хаб редактирования: 2 раздела + навигация."""
    rows = [
        [InlineKeyboardButton(
            text=t("edit_hub_candidate", lang),
            callback_data=f"editsec:candidate:{profile_id}",
        )],
        [InlineKeyboardButton(
            text=t("edit_hub_family", lang),
            callback_data=f"editsec:family:{profile_id}",
        )],
    ]
    rows.extend(nav_kb(lang, "menu:my"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_candidate_kb(profile, lang: str = "ru") -> InlineKeyboardMarkup:
    """Раздел «О кандидате» — 14 полей со значениями."""
    pid = profile.id if profile else 0
    fields_uz = [
        ("👤 Ism", "name"),
        ("🗓 Tug'ilgan yili", "birth_year"),
        ("📏 Bo'yi / Vazni", "height_weight"),
        ("👥 Millat", "nationality"),
        ("🏙 Shahar", "city"),
        ("🎓 Ma'lumoti", "education"),
        ("💼 Ish", "occupation"),
        ("🕌 Dindorlik", "religiosity"),
        ("💍 Oilaviy holat", "marital"),
        ("📸 Foto", "photo"),
        ("📞 Ota-onalar telefoni", "phone"),
        ("📱 Ota-onalar TG", "parent_telegram"),
        ("💬 Nomzod TG", "candidate_telegram"),
        ("🏠 Manzil", "address"),
    ]
    fields_ru = [
        ("👤 Имя", "name"),
        ("🗓 Год рождения", "birth_year"),
        ("📏 Рост / Вес", "height_weight"),
        ("👥 Национальность", "nationality"),
        ("🏙 Город", "city"),
        ("🎓 Образование", "education"),
        ("💼 Работа", "occupation"),
        ("🕌 Религиозность", "religiosity"),
        ("💍 Семейное положение", "marital"),
        ("📸 Фото", "photo"),
        ("📞 Телефон родителей", "phone"),
        ("📱 TG родителей", "parent_telegram"),
        ("💬 TG кандидата", "candidate_telegram"),
        ("🏠 Адрес", "address"),
    ]
    fields = fields_uz if lang == "uz" else fields_ru

    rows = []
    for label, field in fields:
        value = _format_edit_value(field, profile, lang)
        rows.append([InlineKeyboardButton(
            text=f"{label}: {value}",
            callback_data=f"edit:{field}:{pid}",
        )])
    rows.extend(nav_kb(lang, f"myedit:{pid}"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def edit_family_kb(profile, lang: str = "ru") -> InlineKeyboardMarkup:
    """Раздел «О семье» — 8 полей со значениями."""
    pid = profile.id if profile else 0
    fields_uz = [
        ("👨‍💼 Otasi", "father"),
        ("👩‍💼 Onasi", "mother"),
        ("👨‍👩‍👧 Aka-uka / opa-singil", "siblings"),
        ("🌸 Xarakter", "character"),
        ("🌿 Sog'lig'i", "health"),
        ("💭 O'zi haqida", "about"),
        ("🏡 Turar joy", "housing"),
        ("🚗 Avtomobil", "car"),
    ]
    fields_ru = [
        ("👨‍💼 Отец", "father"),
        ("👩‍💼 Мать", "mother"),
        ("👨‍👩‍👧 Братья / сёстры", "siblings"),
        ("🌸 Характер", "character"),
        ("🌿 Здоровье", "health"),
        ("💭 О себе", "about"),
        ("🏡 Жильё", "housing"),
        ("🚗 Автомобиль", "car"),
    ]
    fields = fields_uz if lang == "uz" else fields_ru

    rows = []
    for label, field in fields:
        value = _format_edit_value(field, profile, lang)
        rows.append([InlineKeyboardButton(
            text=f"{label}: {value}",
            callback_data=f"edit:{field}:{pid}",
        )])
    rows.extend(nav_kb(lang, f"myedit:{pid}"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def my_profile_kb(profile_id: int, lang: str = "ru", is_active: bool = True) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(
            text="✏️ Редактировать анкету" if lang == "ru" else "✏️ Anketani tahrirlash",
            callback_data=f"myedit:{profile_id}",
        )],
        [InlineKeyboardButton(
            text="⭐ Перейти на VIP" if lang == "ru" else "⭐ VIPga o'tish",
            callback_data=f"myvip:{profile_id}",
        )],
    ]
    if is_active:
        rows.append([InlineKeyboardButton(
            text="⏸ Поставить на паузу" if lang == "ru" else "⏸ Pauzaga qo'yish",
            callback_data=f"mypause:{profile_id}",
        )])
    else:
        rows.append([InlineKeyboardButton(
            text="🟢 Активировать" if lang == "ru" else "🟢 Faollashtirish",
            callback_data=f"myactivate:{profile_id}",
        )])
    rows.append([InlineKeyboardButton(
        text="🗑 Удалить анкету" if lang == "ru" else "🗑 Anketani o'chirish",
        callback_data=f"mydelete:{profile_id}",
    )])
    rows.extend(nav_kb(lang, "back:menu"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Reminder keyboard ──

def reminder_kb(profile_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["✅ Да, всё в силе", "✏️ Хочу обновить данные", "⏸ Поставить на паузу", "🗑 Удалить анкету"],
        "uz": ["✅ Ha, hammasi kuchda", "✏️ Ma'lumotlarni yangilamoqchiman", "⏸ Pauzaga qo'yish", "🗑 Anketani o'chirish"],
    }
    values = ["keep", "edit", "pause", "delete"]
    l = labels.get(lang, labels["ru"])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=l[i], callback_data=f"remind:{values[i]}:{profile_id}")]
        for i in range(4)
    ])


def choose_moderator_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Выбор модератора по региону. Водий/USA/СНГ/Европа добавляются,
    если их username настроен (непустой).
    """
    from bot.config import MODERATOR_USERNAMES
    # Ordered для стабильного отображения
    regions: list[tuple[str, str]] = [
        ("tashkent",  "Ташкент"),
        ("samarkand", "Самарканд"),
        ("vodiy",     "Водий"),
        ("usa",       "США"),
        ("cis",       "СНГ"),
        ("europe",    "Европа"),
    ]
    rows = []
    for key, label in regions:
        username = MODERATOR_USERNAMES.get(key, "")
        if not username:
            continue
        rows.append([InlineKeyboardButton(text=f"💬 @{username}",
                                          url=f"https://t.me/{username}")])
    # Fallback: если вообще ни один регион не настроен (маловероятно) — только Ташкент-дефолт
    if not rows:
        tash = "rishta_manager_tashkent"
        rows.append([InlineKeyboardButton(text=f"💬 @{tash}",
                                          url=f"https://t.me/{tash}")])
    rows.extend(nav_kb(lang, "back:menu"))
    return InlineKeyboardMarkup(inline_keyboard=rows)
