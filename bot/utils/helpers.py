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
    if lang == "ru":
        return {
            "no": "Нет",
            "yes_with_me": "Да, живут со мной",
            "yes_with_ex": "Да, живут отдельно",
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


def _get_card_lang(profile: Profile) -> str:
    """Get the language the anketa was filled in."""
    return getattr(profile, "anketa_lang", None) or "ru"


# ── Полная анкета для модератора ──

def format_full_anketa(profile: Profile, lang: str = "ru") -> str:
    """Полная анкета для модератора — все 25 полей.
    Модератор всегда видит на русском (lang='ru').
    """
    is_son = profile.profile_type == ProfileType.SON
    icon = "👦" if is_son else "👧"
    type_label = "Сын" if is_son else "Дочь"

    age = calculate_age(profile.birth_year) if profile.birth_year else "?"
    age_str = age_text(age, "ru") if isinstance(age, int) else str(age)

    edu = _edu_map("ru").get(_ev(profile, "education"), "—")
    if profile.university_info:
        edu += f", {profile.university_info}"

    housing = _housing_map("ru").get(_ev(profile, "housing"), "—")
    if profile.parent_housing_type:
        ph = "дом" if profile.parent_housing_type.value == "house" else "квартира"
        housing += f" ({ph})"

    car = _car_map("ru").get(_ev(profile, "car"), "—")
    scope = _scope_map("ru").get(_ev(profile, "search_scope"), "—")
    nat = _nat_map("ru").get(profile.nationality or "", profile.nationality or "—")
    rel = _rel_map("ru").get(_ev(profile, "religiosity"), "—")
    mar = _marital_map(is_son, "ru").get(_ev(profile, "marital_status"), "—")
    ch = _children_map("ru").get(_ev(profile, "children_status"), "—")

    position = ""
    if profile.family_position:
        position = _position_map("ru").get(profile.family_position.value, "")

    # Геолокация
    loc = "не указана"
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

    # Язык анкеты
    anketa_lang = _get_card_lang(profile)
    lang_label = "🇺🇿 UZ" if anketa_lang == "uz" else "🇷🇺 RU"

    text = (
        f"<b>🆕 НОВАЯ АНКЕТА НА ПРОВЕРКУ</b>\n\n"
        f"🔖 <b>{profile.display_id or '—'}</b>\n"
        f"{icon} <b>Тип: {type_label}</b> · {lang_label}\n"
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
    Язык карточки = язык заполнения анкеты.
    """
    card_lang = _get_card_lang(profile)

    is_son = profile.profile_type == ProfileType.SON
    icon = "👦" if is_son else "👧"

    vip = "⭐ VIP · " if profile.vip_status == VipStatus.ACTIVE else ""
    verified = "✅ "

    age = calculate_age(profile.birth_year) if profile.birth_year else "?"
    age_str = age_text(age, card_lang) if isinstance(age, int) else str(age)

    edu_label = "🎓 " + ("Ma'lumoti" if card_lang == "uz" else "Образование")
    edu = _edu_map(card_lang).get(_ev(profile, "education"), "—")
    if profile.university_info:
        edu += f", {profile.university_info}"

    work_label = "💼" if card_lang == "uz" else "💼"
    work_empty = "ko'rsatilmagan" if card_lang == "uz" else "не указано"

    housing = _housing_map(card_lang).get(_ev(profile, "housing"), "—")
    car = _car_map(card_lang).get(_ev(profile, "car"), "")
    nat = _nat_map(card_lang).get(profile.nationality or "", profile.nationality or "—")
    rel = _rel_map(card_lang).get(_ev(profile, "religiosity"), "—")
    mar = _marital_map(is_son, card_lang).get(_ev(profile, "marital_status"), "—")
    ch = _children_map(card_lang).get(_ev(profile, "children_status"), "—")

    health_label = "Sog'lig'ining xususiyatlari" if card_lang == "uz" else "Здоровье"

    position = ""
    if profile.family_position:
        position = _position_map(card_lang).get(profile.family_position.value, "")

    if card_lang == "uz":
        siblings = f"{profile.brothers_count or 0} aka-uka / {profile.sisters_count or 0} opa-singil"
    else:
        siblings = f"{profile.brothers_count or 0} бр. / {profile.sisters_count or 0} сестр."
    if position:
        siblings += f" ({position})"

    # Labels
    father_l = "👨 Otasi" if card_lang == "uz" else "👨 Отец"
    mother_l = "👩 Onasi" if card_lang == "uz" else "👩 Мать"
    children_l = "👶 Farzandlari" if card_lang == "uz" else "👶 Дети"
    views_l = "👁 Ko'rishlar" if card_lang == "uz" else "👁 Просмотров"
    dindorlik_l = "🕌 Dindorlik" if card_lang == "uz" else "🕌 Религиозность"

    lines = [
        f"━━━━━━━━━━━━━━━",
        f"{vip}{verified}· 🔥 {score}%",
        f"🔖 {profile.display_id or '—'}",
        f"{icon} {age_str} · {profile.height_cm or '?'} {'sm' if card_lang == 'uz' else 'см'} / {profile.weight_kg or '?'} {'kg' if card_lang == 'uz' else 'кг'}",
        f"🎓 {edu}",
        f"💼 {profile.occupation or work_empty}",
        f"🏠 {housing}",
    ]

    if car and "🚫" not in car:
        lines.append(car)

    # Город/район (без адреса — адрес в платной части)
    city_line = f"🏙 {profile.city or '—'}"
    if profile.district:
        city_line += f", {profile.district}"
    lines.append(city_line)

    if profile.family_region:
        lines.append(f"🗺 {profile.family_region}")

    lines.append(f"🌍 {nat}")

    if profile.father_occupation:
        lines.append(f"{father_l}: {profile.father_occupation}")
    if profile.mother_occupation:
        lines.append(f"{mother_l}: {profile.mother_occupation}")

    lines.append(f"👨‍👩‍👧‍👦 {siblings}")
    lines.append(f"{rel}")
    lines.append(f"💍 {mar}")
    lines.append(f"{children_l}: {ch}")

    if profile.health_notes:
        lines.append(f"❤️ {health_label}: {profile.health_notes}")

    if profile.character_hobbies:
        lines.append(f"✨ {profile.character_hobbies}")

    lines.append(f"")
    lines.append(f"{views_l}: {profile.views_count or 0}")
    lines.append(f"")

    lock_text = "🔒 Kontaktlar · manzil · foto — to'lovdan keyin" if card_lang == "uz" \
        else "🔒 Контакты · адрес · фото — после оплаты"
    lines.append(lock_text)

    return "\n".join(lines)


# ── Приватная часть анкеты (после оплаты) ──

def format_anketa_private(profile: Profile, lang: str = "ru") -> str:
    """Закрытая часть анкеты ПОСЛЕ оплаты — контакты, адрес, геолокация."""
    card_lang = _get_card_lang(profile)

    is_son = profile.profile_type == ProfileType.SON
    child = ("O'g'il" if is_son else "Qiz") if card_lang == "uz" \
        else ("сына" if is_son else "дочери")

    loc = ""
    if profile.location_link:
        loc_label = "Xaritada" if card_lang == "uz" else "На карте"
        loc = f"\n🗺 {loc_label}: {profile.location_link}"
    elif profile.location_lat and profile.location_lon:
        loc_label = "Xaritada" if card_lang == "uz" else "На карте"
        loc = f"\n🗺 {loc_label}: https://maps.google.com/?q={profile.location_lat},{profile.location_lon}"

    if card_lang == "uz":
        header = "✅ <b>Oila kontaktlari:</b>"
        tg_parents_l = "📱 Ota-onaning TG"
        tg_child_l = f"💬 {child}ning TG"
        address_l = "🏠 Manzil"
        address_empty = "ko'rsatilmagan"
    else:
        header = "✅ <b>Контакты семьи:</b>"
        tg_parents_l = "📱 TG родителей"
        tg_child_l = f"💬 TG {child}"
        address_l = "🏠 Адрес"
        address_empty = "не указан"

    text = (
        f"{header}\n\n"
        f"📞 {profile.parent_phone or '—'}\n"
        f"{tg_parents_l}: {profile.parent_telegram or '—'}\n"
        f"{tg_child_l}: {profile.candidate_telegram or '—'}\n"
        f"📍 {profile.city or '—'}"
    )
    if profile.district:
        text += f", {profile.district}"
    text += f"\n{address_l}: {profile.address or address_empty}"
    text += loc

    return text
