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


def age_text(age: int) -> str:
    if age % 10 == 1 and age % 100 != 11:
        return f"{age} год"
    elif age % 10 in (2, 3, 4) and age % 100 not in (12, 13, 14):
        return f"{age} года"
    return f"{age} лет"


# ── Маппинги для отображения ──

def _edu_map(lang: str = "ru") -> dict:
    return {
        "secondary": "📚 Среднее" if lang == "ru" else "📚 O'rta",
        "vocational": "📖 Среднее спец." if lang == "ru" else "📖 O'rta maxsus",
        "higher": "🎓 Высшее" if lang == "ru" else "🎓 Oliy",
        "studying": "🏛 Учится в вузе" if lang == "ru" else "🏛 OTMda o'qiydi",
    }


def _housing_map(lang: str = "ru") -> dict:
    return {
        "own_house": "🏠 Свой дом" if lang == "ru" else "🏠 O'z uyi",
        "own_apartment": "🏢 Своя квартира" if lang == "ru" else "🏢 O'z kvartirasi",
        "with_parents": "👨‍👩‍👧 С родителями" if lang == "ru" else "👨‍👩‍👧 Ota-onasi bilan",
        "rent": "🔑 Аренда" if lang == "ru" else "🔑 Ijara",
    }


def _car_map(lang: str = "ru") -> dict:
    return {
        "personal": "🚗 Личный" if lang == "ru" else "🚗 Shaxsiy",
        "family": "🚗 Семейный" if lang == "ru" else "🚗 Oilaviy",
        "none": "🚫 Нет" if lang == "ru" else "🚫 Yo'q",
    }


def _rel_map(lang: str = "ru") -> dict:
    return {
        "practicing": "🕌 Практикующий" if lang == "ru" else "🕌 Amaliyotchi",
        "moderate": "☪️ Умеренный" if lang == "ru" else "☪️ Mo'tadil",
        "secular": "🌐 Светский" if lang == "ru" else "🌐 Dunyoviy",
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
    return {
        "no": "Нет" if lang == "ru" else "Yo'q",
        "yes_with_me": "Да, живут со мной" if lang == "ru" else "Ha, men bilan yashaydi",
        "yes_with_ex": "Да, живут отдельно" if lang == "ru" else "Ha, alohida yashaydi",
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
        "middle": "средний" if lang == "ru" else "o'rta",
        "youngest": "младший" if lang == "ru" else "kichik",
        "only": "единственный" if lang == "ru" else "yagona",
    }


def _ev(obj, attr: str) -> str:
    """Safe extract enum value or plain value."""
    val = getattr(obj, attr, None)
    if val is None:
        return ""
    return val.value if hasattr(val, "value") else str(val)


# ── Полная анкета для модератора ──

def format_full_anketa(profile: Profile, lang: str = "ru") -> str:
    """Полная анкета для модератора — все 25 полей."""
    is_son = profile.profile_type == ProfileType.SON
    icon = "👦" if is_son else "👧"
    type_label = ("Сын" if is_son else "Дочь") if lang == "ru" else ("O'g'il" if is_son else "Qiz")

    age = calculate_age(profile.birth_year) if profile.birth_year else "?"
    age_str = age_text(age) if isinstance(age, int) else str(age)

    edu = _edu_map(lang).get(_ev(profile, "education"), "—")
    if profile.university_info:
        edu += f", {profile.university_info}"

    housing = _housing_map(lang).get(_ev(profile, "housing"), "—")
    if profile.parent_housing_type:
        ph = "дом" if profile.parent_housing_type.value == "house" else "квартира"
        housing += f" ({ph})"

    car = _car_map(lang).get(_ev(profile, "car"), "—")
    scope = _scope_map(lang).get(_ev(profile, "search_scope"), "—")
    nat = _nat_map(lang).get(profile.nationality or "", profile.nationality or "—")
    rel = _rel_map(lang).get(_ev(profile, "religiosity"), "—")
    mar = _marital_map(is_son, lang).get(_ev(profile, "marital_status"), "—")
    ch = _children_map(lang).get(_ev(profile, "children_status"), "—")

    position = ""
    if profile.family_position:
        position = _position_map(lang).get(profile.family_position.value, "")

    # Геолокация
    loc = "не указана" if lang == "ru" else "ko'rsatilmagan"
    if profile.location_link:
        loc = profile.location_link
    elif profile.location_lat and profile.location_lon:
        loc = f"https://maps.google.com/?q={profile.location_lat},{profile.location_lon}"

    # VIP
    vip = "⭐ Да" if profile.vip_status == VipStatus.ACTIVE else "Нет"

    # Фото
    photo_type_map = {
        "regular": "🖼 Обычное",
        "closed_face": "😊 Закрытое лицо",
        "silhouette": "👤 Силуэт",
        "none": "нет",
    }
    photo_status = photo_type_map.get(_ev(profile, "photo_type"), "нет")
    if profile.photo_file_id:
        photo_status += " ✅"

    # Совместимость
    compat = ""
    if profile.ideal_family_life or profile.important_qualities or profile.five_year_plans:
        compat = "\n💬 <b>Совместимость:</b>\n"
        if profile.ideal_family_life:
            compat += f"1️⃣ {profile.ideal_family_life}\n"
        if profile.important_qualities:
            compat += f"2️⃣ {profile.important_qualities}\n"
        if profile.five_year_plans:
            compat += f"3️⃣ {profile.five_year_plans}\n"

    header = "🆕 НОВАЯ АНКЕТА НА ПРОВЕРКУ" if lang == "ru" else "🆕 YANGI ANKETA TEKSHIRUVGA"

    text = (
        f"<b>{header}</b>\n\n"
        f"🔖 <b>{profile.display_id or '—'}</b>\n"
        f"{icon} <b>Тип: {type_label}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"1. Имя: {profile.name or '—'}\n"
        f"2. Возраст: {age_str} ({profile.birth_year or '?'})\n"
        f"3. Рост: {profile.height_cm or '?'} см\n"
        f"4. Вес: {profile.weight_kg or '?'} кг\n"
        f"5. Образование: {edu}\n"
        f"6. Работа: {profile.occupation or 'не указано'}\n"
        f"7. Жильё: {housing}\n"
        f"8. Автомобиль: {car}\n"
        f"9. Город/район: {profile.city or '—'}"
    )
    if profile.district:
        text += f", {profile.district}"
    text += (
        f"\n10. Адрес: {profile.address or 'не указан'}\n"
        f"11. Поиск: {scope}\n"
    )
    if profile.preferred_city:
        text += f"    Город: {profile.preferred_city}\n"
    if profile.preferred_district:
        text += f"    Район: {profile.preferred_district}\n"
    if profile.preferred_country:
        text += f"    Страна: {profile.preferred_country}\n"
    text += (
        f"12. Регион семьи: {profile.family_region or '—'}\n"
        f"13. Национальность: {nat}\n"
        f"14. Отец: {profile.father_occupation or '—'}\n"
        f"15. Мать: {profile.mother_occupation or '—'}\n"
        f"16. Семья: {profile.brothers_count or 0} братьев / "
        f"{profile.sisters_count or 0} сестёр"
    )
    if position:
        text += f" ({position})"
    text += (
        f"\n17. Религиозность: {rel}\n"
        f"18. Семейное положение: {mar}\n"
        f"19. Дети: {ch}\n"
        f"20. Здоровье: {profile.health_notes or 'не указано'}\n"
        f"21. Характер: {profile.character_hobbies or 'не указано'}\n"
        f"{compat}"
        f"━━━━━━━━━━━━━━━\n"
        f"📸 Фото: {photo_status}\n"
        f"📞 Телефон: {profile.parent_phone or 'не указан'}\n"
        f"📱 TG родителей: {profile.parent_telegram or 'не указан'}\n"
        f"💬 TG кандидата: {profile.candidate_telegram or 'не указан'}\n"
        f"📍 Геолокация: {loc}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⭐ VIP: {vip}\n"
    )
    return text


# ── Публичная анкета (до оплаты) ──

def format_anketa_public(profile: Profile, score: int = 50, lang: str = "ru") -> str:
    """Публичная анкета для пользователей ДО оплаты.
    Показываем всё КРОМЕ: телефона, адреса, TG, фото.
    """
    is_son = profile.profile_type == ProfileType.SON
    icon = "👦" if is_son else "👧"

    vip = "⭐ VIP · " if profile.vip_status == VipStatus.ACTIVE else ""
    verified = "✅ " if lang == "ru" else "✅ "

    age = calculate_age(profile.birth_year) if profile.birth_year else "?"
    age_str = age_text(age) if isinstance(age, int) else str(age)

    edu = _edu_map(lang).get(_ev(profile, "education"), "—")
    if profile.university_info:
        edu += f", {profile.university_info}"

    housing = _housing_map(lang).get(_ev(profile, "housing"), "—")
    car = _car_map(lang).get(_ev(profile, "car"), "")
    nat = _nat_map(lang).get(profile.nationality or "", profile.nationality or "—")
    rel = _rel_map(lang).get(_ev(profile, "religiosity"), "—")
    mar = _marital_map(is_son, lang).get(_ev(profile, "marital_status"), "—")
    ch = _children_map(lang).get(_ev(profile, "children_status"), "—")

    position = ""
    if profile.family_position:
        position = _position_map(lang).get(profile.family_position.value, "")

    siblings = f"{profile.brothers_count or 0} бр. / {profile.sisters_count or 0} сестр."
    if position:
        siblings += f" ({position})"

    lines = [
        f"━━━━━━━━━━━━━━━",
        f"{vip}{verified}· 🔥 {score}%",
        f"🔖 {profile.display_id or '—'}",
        f"{icon} {age_str} · {profile.height_cm or '?'} см / {profile.weight_kg or '?'} кг",
        f"🎓 {edu}",
        f"💼 {profile.occupation or ('не указано' if lang == 'ru' else 'ko`rsatilmagan')}",
        f"🏠 {housing}",
    ]

    if car and car != "🚫 Нет" and car != "🚫 Yo'q":
        lines.append(car)

    city_line = f"🏙 {profile.city or '—'}"
    if profile.district:
        city_line += f", {profile.district}"
    lines.append(city_line)

    if profile.family_region:
        lines.append(f"🗺 {profile.family_region}")

    lines.append(f"🌍 {nat}")

    if profile.father_occupation:
        lines.append(f"👨 Отец: {profile.father_occupation}")
    if profile.mother_occupation:
        lines.append(f"👩 Мать: {profile.mother_occupation}")

    lines.append(f"👨‍👩‍👧‍👦 {siblings}")
    lines.append(f"{rel}")
    lines.append(f"💍 {mar}")
    lines.append(f"👶 Дети: {ch}")

    if profile.character_hobbies:
        lines.append(f"✨ {profile.character_hobbies}")

    lines.append(f"")
    lines.append(f"👁 Просмотров: {profile.views_count or 0}")
    lines.append(f"")

    lock_text = "🔒 Контакты · адрес · фото — после оплаты" if lang == "ru" \
        else "🔒 Kontaktlar · manzil · foto — to'lovdan keyin"
    lines.append(lock_text)

    return "\n".join(lines)


# ── Приватная часть анкеты (после оплаты) ──

def format_anketa_private(profile: Profile, lang: str = "ru") -> str:
    """Закрытая часть анкеты ПОСЛЕ оплаты — контакты и адрес."""
    is_son = profile.profile_type == ProfileType.SON
    child = ("сына" if is_son else "дочери") if lang == "ru" \
        else ("o'g'il" if is_son else "qiz")

    loc = ""
    if profile.location_link:
        loc = f"\n🗺 На карте: {profile.location_link}"
    elif profile.location_lat and profile.location_lon:
        loc = f"\n🗺 На карте: https://maps.google.com/?q={profile.location_lat},{profile.location_lon}"

    header = "✅ <b>Контакты семьи:</b>" if lang == "ru" else "✅ <b>Oila kontaktlari:</b>"

    text = (
        f"{header}\n\n"
        f"📞 {profile.parent_phone or '—'}\n"
        f"📱 TG родителей: {profile.parent_telegram or '—'}\n"
        f"💬 TG {child}: {profile.candidate_telegram or '—'}\n"
        f"📍 {profile.city or '—'}"
    )
    if profile.district:
        text += f", {profile.district}"
    text += f"\n🏠 Адрес: {profile.address or 'не указан'}"
    text += loc

    return text
