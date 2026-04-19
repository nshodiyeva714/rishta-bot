import datetime
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import Profile, ProfileType, VipStatus


async def generate_display_id(session: AsyncSession, profile_type: ProfileType) -> str:
    prefix = "ДД" if profile_type == ProfileType.DAUGHTER else "СН"
    year = datetime.datetime.now().year
    result = await session.execute(
        select(func.count(Profile.id)).where(
            Profile.display_id.like(f"#{prefix}-{year}-%")
        )
    )
    count = result.scalar() or 0
    return f"#{prefix}-{year}-{count + 1:05d}"


def calculate_age(birth_year: int) -> int:
    return datetime.datetime.now().year - birth_year


_OCCUPATION_LABELS = {
    "ru": {
        "works": "Работает",
        "student": "Студент/ка",
        "business": "Свой бизнес",
        "housewife": "Домохозяйка",
        "other": "Другое",
    },
    "uz": {
        "works": "Ishlaydi",
        "student": "Talaba",
        "business": "O'z biznesi bor",
        "housewife": "Uy bekasi",
        "other": "Boshqa",
    },
}


def occupation_label(key, lang: str = "ru") -> str:
    """Человекочитаемая метка занятости по ключу из БД.

    None / "—" → "—". Неизвестный ключ (legacy свободный ввод) → key как есть.
    """
    if key is None or key == "—":
        return "—"
    L = lang if lang in ("ru", "uz") else "ru"
    return _OCCUPATION_LABELS[L].get(key, key)


_NATIONALITY_LABELS = {
    "ru": {
        "uzbek":      "🇺🇿 Узбек",
        "russian":    "🇷🇺 Русский",
        "tajik":      "🇹🇯 Таджик",
        "kazakh":     "🇰🇿 Казах",
        "korean":     "🇰🇷 Кореец",
        "karakalpak": "🌾 Каракалпак",
        "tatar":      "Татарин",
        "uyghur":     "Уйгур",
        "turkish":    "Турок",
        "kyrgyz":     "🇰🇬 Киргиз",
        "turkmen":    "🇹🇲 Туркмен",
        "other":      "🌍 Другая",
    },
    "uz": {
        "uzbek":      "🇺🇿 O'zbek",
        "russian":    "🇷🇺 Rus",
        "tajik":      "🇹🇯 Tojik",
        "kazakh":     "🇰🇿 Qozoq",
        "korean":     "🇰🇷 Koreys",
        "karakalpak": "🌾 Qoraqalpoq",
        "tatar":      "Tatar",
        "uyghur":     "Uyg'ur",
        "turkish":    "Turk",
        "kyrgyz":     "🇰🇬 Qirg'iz",
        "turkmen":    "🇹🇲 Turkman",
        "other":      "🌍 Boshqa",
    },
}


def nationality_label(key, lang: str = "ru") -> str:
    """Человекочитаемая метка национальности по ключу из БД.

    None / "" → "—". Неизвестный ключ (свободный текстовый ввод / legacy) → key как есть.
    """
    if key is None or key == "" or key == "—":
        return "—"
    L = lang if lang in ("ru", "uz") else "ru"
    return _NATIONALITY_LABELS[L].get(key, key)


def age_text(age: int, lang: str = "ru") -> str:
    """Age with correct word form. UZ uses 'da', RU uses год/года/лет."""
    if lang == "uz":
        return f"{age} da"
    if age % 10 == 1 and age % 100 != 11:
        return f"{age} год"
    elif age % 10 in (2, 3, 4) and age % 100 not in (12, 13, 14):
        return f"{age} года"
    return f"{age} лет"


def _ev(obj, attr: str) -> str:
    """Safe extract enum value or plain value."""
    val = getattr(obj, attr, None)
    if val is None:
        return ""
    return val.value if hasattr(val, "value") else str(val)


def _get_card_lang(profile: Profile) -> str:
    """Get the language the anketa was filled in."""
    return getattr(profile, "anketa_lang", None) or "ru"


# ══════════════════════════════════════════════════════
#  Централизованные словари перевода
#  ФИКСИРОВАННЫЕ значения (кнопки) — переводим на card_lang
#  Данные введённые вручную — показываем КАК ЕСТЬ
# ══════════════════════════════════════════════════════

# ── Метки заголовков ──
LABELS = {
    "ru": {
        "age_suffix": "лет",  # overridden by age_text()
        "cm": "см", "kg": "кг",
        "edu": "Образование",
        "work": "Работа",
        "housing": "Жильё",
        "city": "Город/район",
        "region": "Регион",
        "nat": "Национальность",
        "father": "Отец",
        "mother": "Мать",
        "family": "Семья",
        "religion": "Религиозность",
        "marital": "Семейное положение",
        "children": "Дети",
        "health": "Здоровье",
        "char": "Характер",
        "views": "Просмотров",
        "lock": "🔒 Контакты · адрес · фото откроются после согласия автора и подтверждения модератора.",
        "brothers": "бр.",
        "sisters": "сестр.",
        # private
        "contacts_header": "✅ <b>Контакты семьи:</b>",
        "phone": "Телефон",
        "tg_parents": "TG родителей",
        "tg_child": "TG",
        "address": "Адрес",
        "address_empty": "не указан",
        "on_map": "На карте",
        "warn": (
            "⚠️ Просим сохранять уважение к семье.\n\n"
            "Модератор предупредил семью о вашем визите 🤝\n\n"
            "Удачи! Пусть всё сложится наилучшим образом 🤲\n\n"
            "<i>Через 14 дней спросим о результате 😊</i>"
        ),
    },
    "uz": {
        "age_suffix": "da",
        "cm": "sm", "kg": "kg",
        "edu": "Ma'lumoti",
        "work": "Ishi",
        "housing": "Turar joyi",
        "city": "Shahar/tuman",
        "region": "Hudud",
        "nat": "Millati",
        "father": "Otasi",
        "mother": "Onasi",
        "family": "Oilasi",
        "religion": "Dindorligi",
        "marital": "Oilaviy holati",
        "children": "Farzandlari",
        "health": "Sog'lig'ining xususiyatlari",
        "char": "Xarakteri",
        "views": "Ko'rishlar",
        "lock": "🔒 Kontakt · manzil · foto profil egasi roziligidan va moderator tasdig'idan so'ng ochiladi.",
        "brothers": "aka-uka",
        "sisters": "opa-singil",
        # private
        "contacts_header": "✅ <b>Oila kontaktlari:</b>",
        "phone": "Telefon",
        "tg_parents": "Ota-onalar TG",
        "tg_child": "Nomzod TG",
        "address": "Manzil",
        "address_empty": "ko'rsatilmagan",
        "on_map": "Xaritada",
        "warn": (
            "⚠️ Oilaga hurmat bilan munosabatda bo'ling.\n\n"
            "Moderator oilani tashrif haqida ogohlantirdi 🤝\n\n"
            "Omad! Hammasi yaxshi bo'lsin 🤲\n\n"
            "<i>14 kundan so'ng natija haqida so'raymiz 😊</i>"
        ),
    },
}


def _lb(lang: str) -> dict:
    return LABELS.get(lang, LABELS["ru"])


# ── Фиксированные варианты ответов (кнопки) ──

def _edu_map(lang: str = "ru") -> dict:
    return {
        "secondary": "Среднее" if lang == "ru" else "O'rta",
        "vocational": "Среднее спец." if lang == "ru" else "O'rta maxsus",
        "higher": "Высшее" if lang == "ru" else "Oliy",
        "studying": "Студент/ка" if lang == "ru" else "Talaba",
    }


def _housing_map(lang: str = "ru") -> dict:
    return {
        "own_house": "Свой дом" if lang == "ru" else "O'z uyi",
        "own_apartment": "Своя квартира" if lang == "ru" else "O'z kvartirasi",
        "with_parents": "С родителями" if lang == "ru" else "Ota-ona bilan",
        "rent": "Аренда" if lang == "ru" else "Ijara",
    }


def _car_map(lang: str = "ru") -> dict:
    return {
        "personal": "Личный автомобиль" if lang == "ru" else "Shaxsiy avtomobil",
        "family": "Семейный автомобиль" if lang == "ru" else "Oilaviy avtomobil",
        "none": "Нет" if lang == "ru" else "Yo'q",
    }


def _rel_map(lang: str = "ru") -> dict:
    return {
        "practicing": "Практикующий/ая" if lang == "ru" else "Amaliyotchi",
        "moderate": "Умеренный/ая" if lang == "ru" else "Mo'tadil",
        "secular": "Светский/ая" if lang == "ru" else "Dunyoviy",
    }


def _marital_map(is_male: bool, lang: str = "ru") -> dict:
    if lang == "ru":
        return {
            "never_married": "Не был женат" if is_male else "Не была замужем",
            "divorced": "Разведён" if is_male else "Разведена",
            "widowed": "Вдовец" if is_male else "Вдова",
        }
    return {
        "never_married": "Uylanmagan" if is_male else "Turmush qurmagan",
        "divorced": "Ajrashgan",
        "widowed": "Beva",
    }


# ── Публичные обёртки над enum-картами (аналог occupation_label) ──

def education_label(code, lang: str = "ru") -> str:
    """Человекочитаемая метка уровня образования.

    None / "" / "—" → "—". Неизвестный код → "—".
    """
    if code is None or code == "" or code == "—":
        return "—"
    L = lang if lang in ("ru", "uz") else "ru"
    return _edu_map(L).get(code, "—")


def religiosity_label(code, lang: str = "ru") -> str:
    """Человекочитаемая метка уровня религиозности.

    None / "" / "—" → "—". Неизвестный код → "—".
    """
    if code is None or code == "" or code == "—":
        return "—"
    L = lang if lang in ("ru", "uz") else "ru"
    return _rel_map(L).get(code, "—")


def marital_label(code, is_male: bool, lang: str = "ru") -> str:
    """Человекочитаемая метка семейного положения.

    Учитывает пол (is_male) для корректной формы в RU и "never_married" в UZ.
    None / "" / "—" → "—". Неизвестный код → "—".
    """
    if code is None or code == "" or code == "—":
        return "—"
    L = lang if lang in ("ru", "uz") else "ru"
    return _marital_map(is_male, L).get(code, "—")


def _children_map(lang: str = "ru", is_son: bool = False) -> dict:
    """Map children_status → человеко-читаемый текст.

    is_son учитывается для RU в значении «yes_with_ex»:
    для сына — «с бывшей супругой», для дочери — «с бывшим супругом».
    UZ gender-нейтрален.
    """
    if lang == "ru":
        ex_text = ("Да, живут с бывшей супругой" if is_son
                   else "Да, живут с бывшим супругом")
        return {
            "no": "Детей нет",
            "yes": "Есть дети",
            "yes_with_me": "Да, живут со мной",
            "yes_with_ex": ex_text,
        }
    return {
        "no": "Bolalari yo'q",
        "yes": "Farzand bor",
        "yes_with_me": "Ha, men bilan yashashadi",
        "yes_with_ex": "Ha, sobiq turmush o'rtog'im bilan yashashadi",
    }


def _scope_map(lang: str = "ru") -> dict:
    return {
        "uzbekistan_only": "🇺🇿 Узбекистан" if lang == "ru" else "🇺🇿 O'zbekiston",
        "diaspora": "🌍 Зарубежье" if lang == "ru" else "🌍 Xorij",
        "anywhere": "🔍 Везде" if lang == "ru" else "🔍 Hamma joyda",
    }


def _position_map(lang: str = "ru") -> dict:
    return {
        "oldest": "старший" if lang == "ru" else "katta",
        "middle": "средний" if lang == "ru" else "o'rtancha",
        "youngest": "младший" if lang == "ru" else "kenja",
        "only": "единственный" if lang == "ru" else "yagona",
    }


# ══════════════════════════════════════════════════════
#  format_full_anketa — ПОЛНАЯ анкета для МОДЕРАТОРА
#  Метки на card_lang, данные пользователя — как есть
# ══════════════════════════════════════════════════════

def format_full_anketa(profile: Profile, lang: str = "ru") -> str:
    """Полная анкета для модератора.

    Формат:
    - Уникальная эмодзи перед каждым полем (без нумерации).
    - Обязательные поля (имя, возраст, рост, нац., город, образование,
      семейное положение) — всегда показываются.
    - Опциональные поля скрываются, если значение пустое.
    - Футер (фото, контакты, VIP) — всегда показывается.
    """
    L = _get_card_lang(profile)
    lb = _lb(L)
    is_son = profile.profile_type == ProfileType.SON
    type_label = ("Son" if is_son else "Daughter") if L == "uz" else ("Сын" if is_son else "Дочь")

    age = calculate_age(profile.birth_year) if profile.birth_year else "?"
    age_str = age_text(age, L) if isinstance(age, int) else str(age)

    # Телосложение (без эмодзи — метка 📏 уже есть перед строкой)
    body_type_map = {
        "ru": {"slim": "Стройный/ая", "average": "Среднее", "athletic": "Спортивный/ая", "full": "Плотный/ая"},
        "uz": {"slim": "Ozg'in", "average": "O'rtacha", "athletic": "Sportchilarga xos", "full": "To'ladan kelgan"},
    }
    bt = body_type_map.get(L, body_type_map["ru"]).get(getattr(profile, "body_type", None) or "", "")

    # Фиксированные значения (из enum-map — они теперь без эмодзи)
    edu_raw = _ev(profile, "education")
    edu = _edu_map(L).get(edu_raw, "—")
    if profile.university_info:
        edu += f", {profile.university_info}"

    housing_raw = _ev(profile, "housing")
    housing = _housing_map(L).get(housing_raw, None)
    if housing and profile.parent_housing_type:
        ph_map = {"house": "uy" if L == "uz" else "дом", "apartment": "kvartira" if L == "uz" else "квартира"}
        housing += f" ({ph_map.get(profile.parent_housing_type.value, '')})"

    car_raw = _ev(profile, "car")
    car = _car_map(L).get(car_raw, None)

    scope_raw = _ev(profile, "search_scope")
    scope = _scope_map(L).get(scope_raw, None)

    nat = nationality_label(profile.nationality, L) if profile.nationality else "—"

    rel_raw = _ev(profile, "religiosity")
    rel = _rel_map(L).get(rel_raw, None)

    mar_raw = _ev(profile, "marital_status")
    mar = _marital_map(is_son, L).get(mar_raw, "—")

    ch_raw = _ev(profile, "children_status")
    ch = _children_map(L, is_son).get(ch_raw, None) if ch_raw else None

    position = ""
    if profile.family_position:
        position = _position_map(L).get(profile.family_position.value, "")

    siblings = f"{profile.brothers_count or 0} {lb['brothers']} / {profile.sisters_count or 0} {lb['sisters']}"
    if position:
        siblings += f" ({position})"

    # Геолокация для футера
    loc = "ko'rsatilmagan" if L == "uz" else "не указана"
    if profile.location_link:
        loc = profile.location_link
    elif profile.location_lat and profile.location_lon:
        loc = f"https://maps.google.com/?q={profile.location_lat},{profile.location_lon}"

    vip = "⭐ Да" if profile.vip_status == VipStatus.ACTIVE else "Нет"

    photo_type_map = {
        "regular": "🖼 Обычное" if L == "ru" else "🖼 Oddiy",
        "closed_face": "😊 Закрытое лицо" if L == "ru" else "😊 Yuz yopiq",
        "silhouette": "👤 Силуэт" if L == "ru" else "👤 Siluet",
        "none": "нет" if L == "ru" else "yo'q",
    }
    photo_status = photo_type_map.get(_ev(profile, "photo_type"), "нет")
    if profile.photo_file_id:
        photo_status += " ✅"

    header = "💁‍♀️ Yangi anketa tekshiruvga" if L == "uz" else "💁‍♀️ Новая анкета на проверку"
    addr_empty = "ko'rsatilmagan" if L == "uz" else "не указан"

    lines = [
        f"<b>{header}</b>",
        f"{profile.display_id or '—'} · {type_label}",
        "",
    ]

    # ── Обязательные поля ──
    lines.append(f"👤 {profile.name or '—'}")
    lines.append(f"🎂 {age_str} ({profile.birth_year or '?'})")

    # Рост / Вес / Телосложение — одна строка
    hw_parts = [f"{profile.height_cm or '?'} {lb['cm']}"]
    if profile.weight_kg:
        hw_parts.append(f"{profile.weight_kg} {lb['kg']}")
    if bt:
        hw_parts.append(bt)
    lines.append(f"📏 {' / '.join(hw_parts)}")

    lines.append(f"🎓 {lb['edu']}: {edu}")

    # ── Опциональные (скрываем пустые) ──
    if profile.occupation:
        lines.append(f"💼 {lb['work']}: {occupation_label(profile.occupation, L)}")

    if housing:
        lines.append(f"🏡 {lb['housing']}: {housing}")

    if car:
        lines.append(f"🚗 {car}")

    # Город — обязательное
    city_line = profile.city or "—"
    if profile.district:
        city_line += f", {profile.district}"
    lines.append(f"🏙 {lb['city']}: {city_line}")

    # Адрес (text или карта) — скрыть если нет ни одного
    has_address = bool(profile.address or profile.location_link or (profile.location_lat and profile.location_lon))
    if has_address:
        if profile.address:
            addr_line = profile.address
        elif profile.location_link:
            addr_line = f"🗺 {profile.location_link}"
        else:
            addr_line = f"🗺 https://maps.google.com/?q={profile.location_lat},{profile.location_lon}"
        lines.append(f"🏠 {lb['address']}: {addr_line}")

    if scope:
        lines.append(f"🔍 {scope}")
        if profile.preferred_city:
            lines.append(f"    {profile.preferred_city}")
        if profile.preferred_district:
            lines.append(f"    {profile.preferred_district}")
        if profile.preferred_country:
            lines.append(f"    {profile.preferred_country}")

    if profile.family_region:
        lines.append(f"📍 {lb['region']}: {profile.family_region}")

    # Национальность — обязательное
    lines.append(f"👥 {lb['nat']}: {nat}")

    if profile.father_occupation:
        lines.append(f"👨‍💼 {lb['father']}: {profile.father_occupation}")
    if profile.mother_occupation:
        lines.append(f"👩‍💼 {lb['mother']}: {profile.mother_occupation}")

    lines.append(f"👨‍👩‍👧 {lb['family']}: {siblings}")

    if rel:
        lines.append(f"🕌 {lb['religion']}: {rel}")

    # Семейное положение — обязательное
    lines.append(f"💍 {lb['marital']}: {mar}")

    # Дети: показываем только если marital in (divorced, widowed)
    if mar_raw in ("divorced", "widowed") and ch:
        lines.append(f"👶 {lb['children']}: {ch}")

    if profile.health_notes:
        lines.append(f"🌿 {lb['health']}: {profile.health_notes}")

    if profile.character_hobbies:
        lines.append(f"🌸 {lb['char']}: {profile.character_hobbies}")

    # Совместимость (блок скрывается целиком если все три пусты)
    if profile.ideal_family_life or profile.important_qualities or profile.five_year_plans:
        compat_header = "Moslik" if L == "uz" else "Совместимость"
        lines.append("")
        lines.append(f"💬 <b>{compat_header}:</b>")
        if profile.ideal_family_life:
            lines.append(f"1️⃣ {profile.ideal_family_life}")
        if profile.important_qualities:
            lines.append(f"2️⃣ {profile.important_qualities}")
        if profile.five_year_plans:
            lines.append(f"3️⃣ {profile.five_year_plans}")

    # ── Футер (всегда показывается) ──
    lines.append("━━━━━━━━━━━━━━━")
    lines.append(f"📸 {photo_status}")
    lines.append(f"📞 {lb['phone']}: {profile.parent_phone or addr_empty}")
    lines.append(f"📱 {lb['tg_parents']}: {profile.parent_telegram or addr_empty}")
    lines.append(f"💬 {lb['tg_child']}: {profile.candidate_telegram or addr_empty}")
    lines.append(f"📍 {lb['on_map']}: {loc}")
    lines.append("━━━━━━━━━━━━━━━")
    lines.append(f"⭐ VIP: {vip}")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  format_anketa_public — карточка ДО оплаты
#  Метки на card_lang, данные пользователя — как есть
#  БЕЗ: телефона, адреса, TG, фото
# ══════════════════════════════════════════════════════

def format_anketa_public(profile: Profile, score: int = 50, lang: str = "ru") -> str:
    """Публичная карточка — поля в порядке анкеты, иконка перед каждым."""
    L = _get_card_lang(profile)
    lb = _lb(L)
    is_son = profile.profile_type == ProfileType.SON

    # Значения-мапы
    body_type_map = {
        "ru": {"slim": "🪶 Стройный/ая", "average": "🍃 Среднее", "athletic": "🏃 Спортивный/ая", "full": "🌳 Плотный/ая"},
        "uz": {"slim": "🪶 Ozg'in", "average": "🍃 O'rtacha", "athletic": "🏃 Sportchilarga xos", "full": "🌳 To'ladan kelgan"},
    }
    housing_card_map = {
        "ru": {"own_house": "Свой дом", "own_apartment": "Своя квартира",
               "with_parents": "С родителями", "rent": "Аренда"},
        "uz": {"own_house": "O'z uyi", "own_apartment": "O'z kvartirasi",
               "with_parents": "Ota-ona bilan", "rent": "Ijara"},
    }
    car_card_map = {
        "ru": {"personal": "Личный", "family": "Семейный", "none": "Нет"},
        "uz": {"personal": "Shaxsiy", "family": "Oilaviy", "none": "Yo'q"},
    }
    rel_plain = {
        "ru": {"practicing": "🕌 Практикующий/ая", "moderate": "☪️ Умеренный/ая", "secular": "🌐 Светский/ая"},
        "uz": {"practicing": "🕌 Amaliyotchi", "moderate": "☪️ Mo'tadil", "secular": "🌐 Dunyoviy"},
    }
    lines = []

    # Бейджи: VIP / верификация / популярность / display_id
    badges = []
    if profile.vip_status == VipStatus.ACTIVE:
        badges.append("⭐ VIP")
    if getattr(profile, "is_verified", False):
        badges.append("✅ " + ("Tekshirilgan" if L == "uz" else "Проверено"))
    views = profile.views_count or 0
    if views >= 50:
        badges.append("🔥 " + ("Mashhur" if L == "uz" else "Популярная"))
    elif views >= 20:
        badges.append("👀 " + ("Ko'p ko'rilgan" if L == "uz" else "Много просмотров"))
    if profile.display_id:
        badges.append(f"🔖 {profile.display_id}")
    if badges:
        lines.append("  ".join(badges))
        lines.append("")

    # 1. 🪪 Имя · возраст · рост
    age = calculate_age(profile.birth_year) if profile.birth_year else None
    age_str = age_text(age, L) if age else ""
    header_parts = []
    if profile.name:
        header_parts.append(profile.name)
    if age_str:
        header_parts.append(age_str)
    if profile.height_cm:
        header_parts.append(f"{profile.height_cm} {lb['cm']}")
    if header_parts:
        lines.append("🪪 " + " · ".join(header_parts))

    # 2. Телосложение (иконка уже в значении)
    bt_val = body_type_map.get(L, body_type_map["ru"]).get(getattr(profile, "body_type", None) or "", "")
    if bt_val:
        lines.append(bt_val)

    # 3. Национальность (флаг уже в значении — без доп. иконки)
    if profile.nationality:
        lines.append(nationality_label(profile.nationality, L))

    # 4. 🏡 Город и район
    if profile.city:
        city_part = profile.city
        if profile.district:
            city_part += f", {profile.district}"
        lines.append(f"🏡 {city_part}")

    # 5. Образование (+ ВУЗ/курс)
    edu_raw = _ev(profile, "education")
    if edu_raw:
        edu_label = _edu_map(L).get(edu_raw, edu_raw)
        uni = profile.university_info
        if edu_raw == "studying" and uni:
            lines.append(f"🏛 {uni}")
        else:
            if uni:
                edu_label += f", {uni}"
            lines.append(f"🎓 {edu_label}")

    # 6. Занятость — иконка в значении
    if profile.occupation:
        lines.append(f"💼 {occupation_label(profile.occupation, L)}")

    # 7. Религиозность — иконка в значении
    rel_raw = _ev(profile, "religiosity")
    if rel_raw:
        rel_val = rel_plain.get(L, rel_plain["ru"]).get(rel_raw, rel_raw)
        lines.append(rel_val)

    # 8. Семейное положение (+ дети)
    mar_raw = _ev(profile, "marital_status")
    if mar_raw:
        mar_val = _marital_map(is_son, L).get(mar_raw, mar_raw)
        mar_line = f"💍 {mar_val}"
        ch_raw = _ev(profile, "children_status")
        if ch_raw and ch_raw != "no" and mar_raw != "never_married":
            ch_val = _children_map(L, is_son).get(ch_raw, "")
            if ch_val and ch_val != "—":
                ch_label = lb.get("children", "Дети")
                mar_line += f" · 👶 {ch_label}: {ch_val}"
        lines.append(mar_line)

    # ── Этап 2 ──
    # 9. 👨‍💼 Отец
    if profile.father_occupation:
        lines.append(f"👨‍💼 {lb['father']}: {profile.father_occupation}")

    # 10. 👩‍💼 Мать
    if profile.mother_occupation:
        lines.append(f"👩‍💼 {lb['mother']}: {profile.mother_occupation}")

    # 11. 👨‍👩‍👧‍👦 Братья и сёстры
    brothers = profile.brothers_count
    sisters = profile.sisters_count
    if brothers or sisters:
        fam_parts = []
        if brothers:
            fam_parts.append(f"{brothers} {'aka-uka' if L == 'uz' else 'бр.'}")
        if sisters:
            fam_parts.append(f"{sisters} {'opa-singil' if L == 'uz' else 'сест.'}")
        if fam_parts:
            lines.append(f"👨‍👩‍👧‍👦 {' · '.join(fam_parts)}")

    # 12. 🌸 Характер
    if profile.character_hobbies:
        lines.append(f"🌸 {profile.character_hobbies}")

    # 13. 🌿 Здоровье
    if getattr(profile, "health_notes", None):
        lines.append(f"🌿 {profile.health_notes}")

    # 14. 💭 О себе
    if getattr(profile, "ideal_family_life", None):
        lines.append(f"💭 {profile.ideal_family_life}")

    # 15. 🏡 Жильё
    housing_raw = _ev(profile, "housing")
    if housing_raw:
        housing_val = housing_card_map.get(L, housing_card_map["ru"]).get(housing_raw, "")
        if housing_val:
            lines.append(f"🏡 {housing_val}")

    # 16. 🚘 Автомобиль
    car_raw = _ev(profile, "car")
    if car_raw:
        car_val = car_card_map.get(L, car_card_map["ru"]).get(car_raw, "")
        if car_val:
            lines.append(f"🚘 {car_val}")

    # Футер: просмотры + замок
    lines.append("")
    lines.append(f"👁 {profile.views_count or 0} {lb['views'].lower()}")
    lines.append("")
    lines.append(lb["lock"])

    return "\n".join(lines)


# ══════════════════════════════════════════════════════
#  format_anketa_private — ПОСЛЕ оплаты
#  Контакты + адрес + геолокация
#  Данные введённые вручную — как есть
# ══════════════════════════════════════════════════════

def format_anketa_private(profile: Profile, lang: str = "ru") -> str:
    """Закрытая часть ПОСЛЕ оплаты.
    Метки на card_lang, данные пользователя — как есть.
    """
    L = _get_card_lang(profile)
    lb = _lb(L)

    loc = ""
    if profile.location_link:
        loc = f"\n🗺 {lb['on_map']}: {profile.location_link}"
    elif profile.location_lat and profile.location_lon:
        loc = f"\n🗺 {lb['on_map']}: https://maps.google.com/?q={profile.location_lat},{profile.location_lon}"

    # Телефон, TG, адрес — введены вручную, показываем как есть
    text = (
        f"{lb['contacts_header']}\n\n"
        f"📞 {lb['phone']}: {profile.parent_phone or '—'}\n"
        f"📱 {lb['tg_parents']}: {profile.parent_telegram or '—'}\n"
        f"💬 {lb['tg_child']}: {profile.candidate_telegram or '—'}\n"
        f"📍 {profile.city or '—'}"
    )
    if profile.district:
        text += f", {profile.district}"
    text += f"\n🏠 {lb['address']}: {profile.address or lb['address_empty']}"
    text += loc

    return text
