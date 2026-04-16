from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from bot.texts import t


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
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
    """Главное меню — 6 кнопок."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_search_candidate", lang), callback_data="menu:search_sub")],
        [InlineKeyboardButton(text=t("btn_create_profile", lang), callback_data="menu:create_sub")],
        [InlineKeyboardButton(text=t("btn_my_applications", lang), callback_data="menu:my")],
        [InlineKeyboardButton(text=t("btn_contact_moderator", lang), callback_data="menu:moderator")],
        [InlineKeyboardButton(text=t("btn_feedback", lang), callback_data="menu:feedback")],
        [InlineKeyboardButton(text=t("btn_about", lang), callback_data="menu:about")],
    ])


def search_submenu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Подменю: Найти кандидата → невестку / жениха."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_search_bride", lang), callback_data="menu:search_bride")],
        [InlineKeyboardButton(text=t("btn_search_groom", lang), callback_data="menu:search_groom")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back:menu")],
    ])


def create_submenu_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Подменю: Создать анкету → сына / дочери."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn_profile_son", lang), callback_data="menu:son")],
        [InlineKeyboardButton(text=t("btn_profile_daughter", lang), callback_data="menu:daughter")],
        [InlineKeyboardButton(text=t("btn_back", lang), callback_data="back:menu")],
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
        [InlineKeyboardButton(text=t("btn_cancel", lang), callback_data="back:menu")],
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
        "ru": ["📚 Среднее", "📖 Среднее специальное", "🎓 Высшее", "🏛 Учится в вузе"],
        "uz": ["📚 O'rta", "📖 O'rta maxsus", "🎓 Oliy", "🏛 OTMda o'qiydi"],
    }
    values = ["secondary", "vocational", "higher", "studying"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"edu:{values[i]}")]
        for i in range(4)
    ])


def housing_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🏠 Свой дом", "🏢 Своя квартира", "👨‍👩‍👧 С родителями", "🔑 Аренда"],
        "uz": ["🏠 O'z uyi", "🏢 O'z kvartirasi", "👨‍👩‍👧 Ota-onasi bilan", "🔑 Ijara"],
    }
    values = ["own_house", "own_apartment", "with_parents", "rent"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"housing:{values[i]}")]
        for i in range(4)
    ])


def parent_housing_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {"ru": ["🏠 Дом", "🏢 Квартира"], "uz": ["🏠 Uy", "🏢 Kvartira"]}
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=labels.get(lang, labels["ru"])[0], callback_data="phousing:house"),
            InlineKeyboardButton(text=labels.get(lang, labels["ru"])[1], callback_data="phousing:apartment"),
        ]
    ])


def car_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🚗 Есть личный", "🚗 Есть семейный", "🚫 Нет"],
        "uz": ["🚗 Shaxsiy bor", "🚗 Oilaviy bor", "🚫 Yo'q"],
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


def city_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    cities_ru = ["Ташкент", "Самарканд", "Фергана", "Бухара", "Наманган", "Андижан", "Нукус", "Другой город"]
    cities_uz = ["Toshkent", "Samarqand", "Farg'ona", "Buxoro", "Namangan", "Andijon", "Nukus", "Boshqa shahar"]
    cities = cities_uz if lang == "uz" else cities_ru
    rows = []
    for i in range(0, len(cities), 2):
        row = [InlineKeyboardButton(text=cities[j], callback_data=f"city:{cities_ru[j]}") for j in range(i, min(i + 2, len(cities)))]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


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


def nationality_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["🇺🇿 Узбек", "🇷🇺 Русский", "🇰🇷 Кореец", "🇹🇯 Таджик", "🇰🇿 Казах", "🌍 Другая"],
        "uz": ["🇺🇿 O'zbek", "🇷🇺 Rus", "🇰🇷 Koreys", "🇹🇯 Tojik", "🇰🇿 Qozoq", "🌍 Boshqa"],
    }
    values = ["uzbek", "russian", "korean", "tajik", "kazakh", "other"]
    rows = []
    for i in range(0, len(values), 2):
        row = [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[j], callback_data=f"nat:{values[j]}") for j in range(i, min(i + 2, len(values)))]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
        "ru": ["🕌 Практикующий", "☪️ Умеренный", "🌐 Светский"],
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
            "ru": ["💍 Не был женат", "💔 Разведён", "🖤 Вдовец"],
            "uz": ["💍 Hech uylanmagan", "💔 Ajrashgan", "🖤 Beva"],
        }
    else:
        labels = {
            "ru": ["💍 Не была замужем", "💔 Разведена", "🖤 Вдова"],
            "uz": ["💍 Hech turmushga chiqmagan", "💔 Ajrashgan", "🖤 Beva"],
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
            ("👶 Farzand bor", "child:yes"),
        ]
    else:
        opts = [
            ("👶 Детей нет", "child:no"),
            ("👶 Есть дети", "child:yes"),
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


def work_choice_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    labels = {
        "ru": ["💼 Указать место работы", "⏭ Не важно / пропустить"],
        "uz": ["💼 Ish joyini ko'rsatish", "⏭ Muhim emas / o'tkazish"],
    }
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[0], callback_data="work:specify")],
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[1], callback_data="work:skip")],
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
    """Экран завершения Этапа 1: опубликовать или дополнить."""
    if lang == "uz":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Moderatorga yuborish", callback_data="profile:publish")],
            [InlineKeyboardButton(text="✨ Anketani boyitish", callback_data="profile:enhance")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Отправить на публикацию", callback_data="profile:publish")],
        [InlineKeyboardButton(text="✨ Сделать анкету ярче", callback_data="profile:enhance")],
    ])


def enhance_or_publish_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """После описания Этапа 2: дополнить сейчас или опубликовать."""
    if lang == "uz":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Hozir to'ldirish", callback_data="profile:extend_now")],
            [InlineKeyboardButton(text="🚀 Shundayicha nashr etish", callback_data="profile:publish")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Дополнить сейчас", callback_data="profile:extend_now")],
        [InlineKeyboardButton(text="🚀 Опубликовать как есть", callback_data="profile:publish")],
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


def tariff_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    if lang == "uz":
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⭐ VIP anketa — narxlar", callback_data="tariff:vip")],
            [InlineKeyboardButton(text="📋 Oddiy anketa — bepul", callback_data="tariff:free")],
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ VIP анкета — выбрать срок", callback_data="tariff:vip")],
        [InlineKeyboardButton(text="📋 Обычная анкета — бесплатно", callback_data="tariff:free")],
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
    labels = {
        "ru": ["🇺🇿 Узбечка", "🇷🇺 Русская", "🇰🇷 Кореянка", "🇹🇯 Таджичка", "🇰🇿 Казашка", "✅ Не важно"],
        "uz": ["🇺🇿 O'zbek", "🇷🇺 Rus", "🇰🇷 Koreys", "🇹🇯 Tojik", "🇰🇿 Qozoq", "✅ Muhim emas"],
    }
    values = ["uzbek", "russian", "korean", "tajik", "kazakh", "any"]
    rows = []
    for i in range(0, len(values), 2):
        row = [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[j], callback_data=f"reqnat:{values[j]}") for j in range(i, min(i + 2, len(values)))]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
    labels = {
        "ru": ["👶 Без детей обязательно", "✅ Не важно"],
        "uz": ["👶 Farzandsiz majburiy", "✅ Muhim emas"],
    }
    values = ["no_children", "any"]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=labels.get(lang, labels["ru"])[i], callback_data=f"reqchild:{values[i]}")]
        for i in range(2)
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

def mod_review_kb(profile_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"mod:publish:{profile_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"mod:reject:{profile_id}"),
        ],
        [InlineKeyboardButton(text="📸 Отклонить фото", callback_data=f"mod:reject_photo:{profile_id}")],
        [InlineKeyboardButton(text="⭐ Опубликовать как VIP", callback_data=f"mod:publish_vip:{profile_id}")],
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

def profile_card_kb(profile_id: int, lang: str = "ru", display_id: str = "") -> InlineKeyboardMarkup:
    from bot.config import get_moderator_username
    username = get_moderator_username("tashkent")
    if lang == "uz":
        interest = "💬 Moderatordan so'rash"
        fav = "❤️ Sevimlilarga"
        report = "🚩 Shikoyat qilish"
        skip = "❌ Mos emas"
    else:
        interest = "💬 Узнать подробнее у модератора"
        fav = "❤️ В избранное"
        report = "🚩 Пожаловаться"
        skip = "❌ Не подходит"

    # Живая ссылка на модератора с номером анкеты
    mod_text = f"Анкета {display_id}" if display_id else "Анкета"
    mod_url = f"https://t.me/{username}?text={mod_text.replace(' ', '+')}"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=interest, callback_data=f"interest:{profile_id}")],
        [InlineKeyboardButton(text=f"💬 @{username}", url=mod_url)],
        [InlineKeyboardButton(text=fav, callback_data=f"fav:{profile_id}")],
        [
            InlineKeyboardButton(text=report, callback_data=f"report:{profile_id}"),
            InlineKeyboardButton(text=skip, callback_data=f"skip_profile:{profile_id}"),
        ],
    ])


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
    if lang == "uz":
        buttons = [
            [InlineKeyboardButton(text="✅ Mening talablarim bo'yicha", callback_data="search:my_req")],
            [InlineKeyboardButton(text="🔧 Filtrlarni qo'lda sozlash", callback_data="search:manual")],
            [InlineKeyboardButton(text="👀 Barcha anketalarni ko'rish", callback_data="search:all")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back:menu")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="✅ По моим требованиям", callback_data="search:my_req")],
            [InlineKeyboardButton(text="🔧 Настроить фильтры вручную", callback_data="search:manual")],
            [InlineKeyboardButton(text="👀 Показать все анкеты", callback_data="search:all")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back:menu")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_no_anketa_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Если нет анкеты — предлагаем создать."""
    if lang == "uz":
        buttons = [
            [InlineKeyboardButton(text="👦 Anketa joylashtirish", callback_data="menu:son")],
            [InlineKeyboardButton(text="👧 Anketa joylashtirish", callback_data="menu:daughter")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back:menu")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="👦 Разместить анкету сына", callback_data="menu:son")],
            [InlineKeyboardButton(text="👧 Разместить анкету дочери", callback_data="menu:daughter")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back:menu")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def search_filter_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    """Главное меню ручных фильтров."""
    if lang == "uz":
        buttons = [
            [InlineKeyboardButton(text="📅 Yosh", callback_data="filter:age")],
            [InlineKeyboardButton(text="🕌 Dindorlik", callback_data="filter:religion")],
            [InlineKeyboardButton(text="🎓 Ma'lumoti", callback_data="filter:education")],
            [InlineKeyboardButton(text="💍 Oilaviy holat", callback_data="filter:marital")],
            [InlineKeyboardButton(text="👶 Farzandlar", callback_data="filter:children")],
            [InlineKeyboardButton(text="🌍 Yashash joyi", callback_data="filter:residence")],
            [InlineKeyboardButton(text="🔍 Qidirish", callback_data="filter:go")],
            [InlineKeyboardButton(text="🔄 Tozalash", callback_data="filter:clear")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back:menu")],
        ]
    else:
        buttons = [
            [InlineKeyboardButton(text="📅 Возраст", callback_data="filter:age")],
            [InlineKeyboardButton(text="🕌 Религиозность", callback_data="filter:religion")],
            [InlineKeyboardButton(text="🎓 Образование", callback_data="filter:education")],
            [InlineKeyboardButton(text="💍 Семейное положение", callback_data="filter:marital")],
            [InlineKeyboardButton(text="👶 Дети", callback_data="filter:children")],
            [InlineKeyboardButton(text="🌍 Где проживает", callback_data="filter:residence")],
            [InlineKeyboardButton(text="🔍 Начать поиск", callback_data="filter:go")],
            [InlineKeyboardButton(text="🔄 Сбросить фильтры", callback_data="filter:clear")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back:menu")],
        ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def filter_option_kb(options: list[tuple[str, str]], lang: str = "ru") -> InlineKeyboardMarkup:
    """Клавиатура выбора значения фильтра. options = [(label, callback_data), ...]"""
    buttons = [[InlineKeyboardButton(text=label, callback_data=cd)] for label, cd in options]
    back_label = "🔙 Orqaga" if lang == "uz" else "🔙 Назад к фильтрам"
    buttons.append([InlineKeyboardButton(text=back_label, callback_data="search:manual")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── VIP duration keyboards ──

def _fmt_price(price: int, region: str) -> str:
    if region == "usa":
        return f"${price // 100}"
    return f"{price:,} сум".replace(",", " ")


def vip_duration_kb(lang: str = "ru", region: str = "uzb") -> InlineKeyboardMarkup:
    """Выбор срока VIP с ценами для пользователя."""
    from bot.config import VIP_PRICES_UZB, VIP_PRICES_USD, VIP_PRICES_SNG
    prices = {"uzb": VIP_PRICES_UZB, "sng": VIP_PRICES_SNG, "usa": VIP_PRICES_USD}.get(region, VIP_PRICES_UZB)

    durations = [
        (7,   {"ru": "7 дней",    "uz": "7 kun"}),
        (14,  {"ru": "14 дней",   "uz": "14 kun"}),
        (30,  {"ru": "1 месяц",   "uz": "1 oy"}),
        (90,  {"ru": "3 месяца",  "uz": "3 oy"}),
        (180, {"ru": "6 месяцев", "uz": "6 oy"}),
        (365, {"ru": "1 год",     "uz": "1 yil"}),
    ]

    rows = []
    pair = []
    for days, labels in durations:
        price_str = _fmt_price(prices[str(days)], region)
        text = f"{labels[lang]} — {price_str}"
        pair.append(InlineKeyboardButton(text=text, callback_data=f"vip_dur:{days}"))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)

    cancel = "❌ Bekor qilish" if lang == "uz" else "❌ Отмена"
    rows.append([InlineKeyboardButton(text=cancel, callback_data="back:menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
    rows.append([InlineKeyboardButton(text=t("btn_back", lang), callback_data="back:menu")])
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
    """Выбор одного из двух модераторов."""
    from bot.config import MODERATOR_USERNAMES
    tash = MODERATOR_USERNAMES.get("tashkent", "rishta_manager_tashkent")
    sam = MODERATOR_USERNAMES.get("samarkand", "rishta_manager_samarkand")
    back = "🔙 Orqaga" if lang == "uz" else "🔙 Назад"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💬 @{tash}", url=f"https://t.me/{tash}")],
        [InlineKeyboardButton(text=f"💬 @{sam}", url=f"https://t.me/{sam}")],
        [InlineKeyboardButton(text=back, callback_data="back:menu")],
    ])
