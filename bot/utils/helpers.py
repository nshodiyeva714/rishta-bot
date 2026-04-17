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
        "edu": "Ma'lumoti",  # education label — same key, diff value
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
        "lock": "🔒 Контакты · адрес · фото — после оплаты",
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
        "lock": "🔒 Kontakt · manzil · foto — to'lovdan keyin",
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
        "practicing": "🕌 Практикующий" if lang == "ru" else "🕌 Amaliyotchi",
        "moderate": "Умеренный" if lang == "ru" else "Mo'tadil",
        "secular": "Светский" if lang == "ru" else "Dunyoviy",
    }


def _marital_map(is_male: bool, lang: str = "ru") -> dict:
    if lang == "ru":
        return {
            "never_married": "Никогда не был женат" if is_male else "Никогда не была замужем",
            "divorced": "Разведён" if is_male else "Разведена",
            "widowed": "Вдовец" if is_male else "Вдова",
        }
    return {
        "never_married": "Hech uylanmagan" if is_male else "Hech turmushga chiqmagan",
        "divorced": "Ajrashgan",
        "widowed": "Beva",
    }


def _children_map(lang: str = "ru") -> dict:
    if lang == "ru":
        return {
            "no": "Нет",
            "yes_with_me": "Да, живут со мной",
            "yes_with_ex": "Да, живут с бывшим супругом",
        }
    return {
        "no": "Yo'q",
        "yes_with_me": "Ha, men bilan yashaydi",
        "yes_with_ex": "Ha, sobiq turmush o'rtoq bilan yashaydi",
    }


def _scope_map(lang: str = "ru") -> dict:
    return {
        "uzbekistan_only": "🇺🇿 Узбекистан" if lang == "ru" else "🇺🇿 O'zbekiston",
        "diaspora": "🌍 Зарубежье" if lang == "ru" else "🌍 Xorij",
        "anywhere": "🔍 Везде" if lang == "ru" else "🔍 Hamma joyda",
    }


def _nat_map(lang: str = "ru") -> dict:
    return {
        "uzbek": "🇺🇿 Узбек" if lang == "ru" else "🇺🇿 O'zbek",
        "russian": "🇷🇺 Русский" if lang == "ru" else "🇷🇺 Rus",
        "korean": "🇰🇷 Кореец" if lang == "ru" else "🇰🇷 Koreys",
        "tajik": "🇹🇯 Таджик" if lang == "ru" else "🇹🇯 Tojik",
        "kazakh": "🇰🇿 Казах" if lang == "ru" else "🇰🇿 Qozoq",
        "other": "🌍 Другая" if lang == "ru" else "🌍 Boshqa",
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
    """Полная анкета для модератора — все 25 полей.
    Метки на card_lang (язык анкеты), данные пользователя — как есть.
    """
    L = _get_card_lang(profile)
    lb = _lb(L)
    is_son = profile.profile_type == ProfileType.SON
    icon = "👦" if is_son else "👧"
    type_label = ("Son" if is_son else "Daughter") if L == "uz" else ("Сын" if is_son else "Дочь")

    age = calculate_age(profile.birth_year) if profile.birth_year else "?"
    age_str = age_text(age, L) if isinstance(age, int) else str(age)

    # Телосложение
    body_type_map = {
        "ru": {"slim": "Стройный", "average": "Среднее", "athletic": "Спортивный", "full": "Плотный"},
        "uz": {"slim": "Ozg'in", "average": "O'rtacha", "athletic": "Sportcha", "full": "To'liq"},
    }
    bt = body_type_map.get(L, body_type_map["ru"]).get(getattr(profile, "body_type", None) or "", "")

    # Фиксированные значения — переводим
    edu = _edu_map(L).get(_ev(profile, "education"), "—")
    # university_info — введено вручную, добавляем как есть
    if profile.university_info:
        edu += f", {profile.university_info}"

    housing = _housing_map(L).get(_ev(profile, "housing"), "—")
    if profile.parent_housing_type:
        ph_map = {"house": "uy" if L == "uz" else "дом", "apartment": "kvartira" if L == "uz" else "квартира"}
        housing += f" ({ph_map.get(profile.parent_housing_type.value, '')})"

    car = _car_map(L).get(_ev(profile, "car"), "—")
    scope = _scope_map(L).get(_ev(profile, "search_scope"), "—")
    nat = _nat_map(L).get(profile.nationality or "", profile.nationality or "—")
    rel = _rel_map(L).get(_ev(profile, "religiosity"), "—")
    mar = _marital_map(is_son, L).get(_ev(profile, "marital_status"), "—")
    ch = _children_map(L).get(_ev(profile, "children_status"), "—")

    position = ""
    if profile.family_position:
        position = _position_map(L).get(profile.family_position.value, "")

    siblings = f"{profile.brothers_count or 0} {lb['brothers']} / {profile.sisters_count or 0} {lb['sisters']}"
    if position:
        siblings += f" ({position})"

    # Геолокация
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

    # Совместимость — введена вручную, показываем как есть
    compat = ""
    if profile.ideal_family_life or profile.important_qualities or profile.five_year_plans:
        compat_header = "Moslik" if L == "uz" else "Совместимость"
        compat = f"\n💬 <b>{compat_header}:</b>\n"
        if profile.ideal_family_life:
            compat += f"1️⃣ {profile.ideal_family_life}\n"
        if profile.important_qualities:
            compat += f"2️⃣ {profile.important_qualities}\n"
        if profile.five_year_plans:
            compat += f"3️⃣ {profile.five_year_plans}\n"

    lang_badge = "🇺🇿 UZ" if L == "uz" else "🇷🇺 RU"
    header = "💁‍♀️ Yangi anketa tekshiruvga" if L == "uz" else "💁‍♀️ Новая анкета на проверку"
    not_specified = "ko'rsatilmagan" if L == "uz" else "не указано"
    addr_empty = "ko'rsatilmagan" if L == "uz" else "не указан"

    text = (
        f"<b>{header}</b>\n"
        f"{profile.display_id or '—'} · {type_label}\n\n"
        # Имя — введено вручную
        f"1. {profile.name or '—'}\n"
        # Возраст — фиксированный формат
        f"2. {age_str} ({profile.birth_year or '?'})\n"
        f"3. {profile.height_cm or '?'} {lb['cm']}"
        f"{(' / ' + str(profile.weight_kg) + ' ' + lb['kg']) if profile.weight_kg else ''}"
        f"{(' / ' + bt) if bt else ''}\n"
        f"4. {lb['edu']}: {edu}\n"
        # Работа — введена вручную
        f"5. {lb['work']}: {profile.occupation or not_specified}\n"
        f"6. {lb['housing']}: {housing}\n"
        f"7. {car}\n"
        # Город — введён вручную
        f"8. {lb['city']}: {profile.city or '—'}"
    )
    if profile.district:
        text += f", {profile.district}"
    # Адрес — введён вручную
    text += f"\n9. {lb['address']}: {profile.address or addr_empty}\n"
    text += f"10. {scope}\n"
    if profile.preferred_city:
        text += f"    {profile.preferred_city}\n"
    if profile.preferred_district:
        text += f"    {profile.preferred_district}\n"
    if profile.preferred_country:
        text += f"    {profile.preferred_country}\n"
    # Регион — введён вручную (выбор из кнопок)
    text += f"11. {lb['region']}: {profile.family_region or '—'}\n"
    text += f"12. {lb['nat']}: {nat}\n"
    # Отец, Мать — введено вручную
    text += f"13. {lb['father']}: {profile.father_occupation or '—'}\n"
    text += f"14. {lb['mother']}: {profile.mother_occupation or '—'}\n"
    text += f"15. {lb['family']}: {siblings}\n"
    text += f"16. {lb['religion']}: {rel}\n"
    text += f"17. {lb['marital']}: {mar}\n"
    text += f"18. {lb['children']}: {ch}\n"
    # Здоровье — введено вручную
    text += f"19. {lb['health']}: {profile.health_notes or not_specified}\n"
    # Характер — введён вручную
    text += f"20. {lb['char']}: {profile.character_hobbies or not_specified}\n"
    text += compat
    text += (
        f"━━━━━━━━━━━━━━━\n"
        f"📸 {photo_status}\n"
        f"📞 {lb['phone']}: {profile.parent_phone or addr_empty}\n"
        f"📱 {lb['tg_parents']}: {profile.parent_telegram or addr_empty}\n"
        f"💬 {lb['tg_child']}: {profile.candidate_telegram or addr_empty}\n"
        f"📍 {lb['on_map']}: {loc}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⭐ VIP: {vip}\n"
    )
    return text


# ══════════════════════════════════════════════════════
#  format_anketa_public — карточка ДО оплаты
#  Метки на card_lang, данные пользователя — как есть
#  БЕЗ: телефона, адреса, TG, фото
# ══════════════════════════════════════════════════════

def format_anketa_public(profile: Profile, score: int = 50, lang: str = "ru") -> str:
    """Публичная карточка — компактный формат."""
    L = _get_card_lang(profile)
    lb = _lb(L)
    is_son = profile.profile_type == ProfileType.SON

    vip = "⭐ VIP  " if profile.vip_status == VipStatus.ACTIVE else ""

    age = calculate_age(profile.birth_year) if profile.birth_year else "?"
    age_str = age_text(age, L) if isinstance(age, int) else str(age)

    body_type_map = {
        "ru": {"slim": "Стройный", "average": "Среднее", "athletic": "Спортивный", "full": "Плотный"},
        "uz": {"slim": "Ozg'in", "average": "O'rtacha", "athletic": "Sportcha", "full": "To'liq"},
    }

    edu = _edu_map(L).get(_ev(profile, "education"), "—")
    if profile.university_info:
        edu += f", {profile.university_info}"

    nat = _nat_map(L).get(profile.nationality or "", profile.nationality or "—")
    rel = _rel_map(L).get(_ev(profile, "religiosity"), "—")
    mar = _marital_map(is_son, L).get(_ev(profile, "marital_status"), "—")
    ch = _children_map(L).get(_ev(profile, "children_status"), "")

    lines = [
        f"{vip}✅",
        f"{profile.display_id or '—'}",
        f"",
    ]

    # Line: age · height · body type (or weight for old profiles)
    bt_pub = body_type_map.get(L, body_type_map["ru"]).get(getattr(profile, "body_type", None) or "", "")
    parts = [age_str, f"{profile.height_cm or '?'} {lb['cm']}"]
    if bt_pub:
        parts.append(bt_pub)
    elif profile.weight_kg:
        parts.append(f"{profile.weight_kg} {lb['kg']}")
    age_hw = " · ".join(parts)
    lines.append(age_hw)

    # Line: education · city
    city_edu = edu
    if profile.city:
        city_part = profile.city
        if profile.district:
            city_part += f", {profile.district}"
        city_edu += f" · {city_part}"
    lines.append(city_edu)

    # Line: nationality · region
    nat_region = nat
    if profile.family_region:
        fam_label = "oilasi" if L == "uz" else "семья"
        nat_region += f" · {profile.family_region} {fam_label}"
    lines.append(nat_region)

    # Line: father · mother (if present)
    parents = []
    if profile.father_occupation:
        father_l = lb['father']
        parents.append(f"{father_l}: {profile.father_occupation}")
    if profile.mother_occupation:
        mother_l = lb['mother']
        parents.append(f"{mother_l}: {profile.mother_occupation}")
    if parents:
        lines.append(" · ".join(parents))

    # Line: religion · marital · children
    status_parts = [rel, mar]
    if ch and ch != "—":
        ch_label = lb.get("children", "Дети")
        status_parts.append(f"{ch_label}: {ch}")
    lines.append(" · ".join(status_parts))

    # Character if present
    if profile.character_hobbies:
        lines.append(f"")
        lines.append(profile.character_hobbies)

    lines.append(f"")
    lines.append(f"👁 {profile.views_count or 0} {lb['views'].lower()}")
    lines.append(f"")
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
