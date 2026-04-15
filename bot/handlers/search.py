"""Шаг 10 — Поиск анкет, Шаг 11 — Уведомление семье."""

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from sqlalchemy import select, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import (
    User, Profile, ProfileStatus, ProfileType, VipStatus,
    Requirement, Favorite, ContactRequest, RequestStatus,
)
from bot.texts import t
from bot.keyboards.inline import profile_card_kb, search_nav_kb, back_kb, main_menu_kb, get_contact_kb
from bot.utils.helpers import age_text, calculate_age
from bot.config import config

router = Router()

PROFILES_PER_PAGE = 3


async def get_lang(session: AsyncSession, user_id: int) -> str:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    return user.language.value if user and user.language else "ru"


def compute_match_score(profile: Profile, req: Requirement) -> int:
    """Простой расчёт процента совместимости."""
    if not req:
        return 50
    score = 50  # базовый

    if profile.birth_year and req.age_from and req.age_to:
        age = calculate_age(profile.birth_year)
        if req.age_from <= age <= req.age_to:
            score += 15
        else:
            score -= 10

    if req.nationality and req.nationality != "any" and profile.nationality:
        if profile.nationality == req.nationality:
            score += 10

    if req.religiosity and req.religiosity != "any" and profile.religiosity:
        if profile.religiosity.value == req.religiosity:
            score += 10

    if req.education and req.education != "any" and profile.education:
        if profile.education.value == req.education or req.education == "vocational":
            score += 5

    if req.marital_status and req.marital_status != "any" and profile.marital_status:
        if profile.marital_status.value == req.marital_status:
            score += 5

    if req.children and req.children != "any" and profile.children_status:
        if req.children == "no_children" and profile.children_status.value == "no":
            score += 5

    return min(max(score, 10), 99)


async def get_search_results(session: AsyncSession, user_id: int):
    """Получить подходящие анкеты для пользователя."""
    # Находим анкету пользователя и его требования
    result = await session.execute(
        select(Profile).where(
            Profile.user_id == user_id,
            Profile.status != ProfileStatus.DELETED,
        ).limit(1)
    )
    user_profile = result.scalar_one_or_none()

    user_req = None
    if user_profile:
        result = await session.execute(
            select(Requirement).where(Requirement.profile_id == user_profile.id)
        )
        user_req = result.scalar_one_or_none()

    # Ищем противоположный пол
    target_type = ProfileType.DAUGHTER if (user_profile and user_profile.profile_type == ProfileType.SON) else ProfileType.SON

    query = select(Profile).where(
        Profile.status == ProfileStatus.PUBLISHED,
        Profile.is_active == True,
        Profile.profile_type == target_type,
        Profile.user_id != user_id,
    ).order_by(
        # VIP первыми
        case((Profile.vip_status == VipStatus.ACTIVE, 0), else_=1),
        desc(Profile.published_at),
    )

    result = await session.execute(query)
    profiles = result.scalars().all()

    # Считаем совместимость и сортируем
    scored = []
    for p in profiles:
        score = compute_match_score(p, user_req)
        scored.append((p, score))

    # VIP первые, потом по score
    scored.sort(key=lambda x: (
        0 if x[0].vip_status == VipStatus.ACTIVE else 1,
        -x[1],
    ))

    return scored


def format_profile_card(profile: Profile, score: int, lang: str = "ru") -> str:
    """Форматирование карточки анкеты."""
    vip = "⭐ VIP · " if profile.vip_status == VipStatus.ACTIVE else ""
    verified = "✅ Проверено" if lang == "ru" else "✅ Tekshirilgan"

    age = calculate_age(profile.birth_year) if profile.birth_year else "?"
    age_str = age_text(age) if isinstance(age, int) else str(age)

    edu_map = {
        "secondary": "Среднее" if lang == "ru" else "O'rta",
        "vocational": "Среднее спец." if lang == "ru" else "O'rta maxsus",
        "higher": "Высшее" if lang == "ru" else "Oliy",
        "studying": profile.university_info or ("Учится" if lang == "ru" else "O'qiydi"),
    }
    edu = edu_map.get(profile.education.value, "—") if profile.education else "—"

    car_map = {
        "personal": "🚗 Личный" if lang == "ru" else "🚗 Shaxsiy",
        "family": "🚗 Семейный" if lang == "ru" else "🚗 Oilaviy",
        "none": "",
    }
    car = car_map.get(profile.car.value, "") if profile.car else ""

    icon = "👧" if profile.profile_type == ProfileType.DAUGHTER else "👦"

    lines = [
        f"━━━━━━━━━━━━━━━",
        f"{vip}{verified} · 🔥 {score}%",
        f"🔖 {profile.display_id}",
        f"{icon} {age_str} · {profile.height_cm or '?'} см / {profile.weight_kg or '?'} кг",
        f"🎓 {edu}",
    ]
    if car:
        lines.append(car)
    if profile.city:
        lines.append(f"🏙 {profile.city}" + (f", {profile.district}" if profile.district else ""))
    if profile.nationality:
        nat_map = {"uzbek": "🇺🇿 Узбек", "russian": "🇷🇺 Русский", "korean": "🇰🇷 Кореец",
                   "tajik": "🇹🇯 Таджик", "kazakh": "🇰🇿 Казах", "other": "🌍 Другая"}
        nat = nat_map.get(profile.nationality, profile.nationality)
        lines.append(nat)
    if profile.father_occupation:
        lines.append(f"👨 Отец: {profile.father_occupation}")
    if profile.mother_occupation:
        lines.append(f"👩 Мать: {profile.mother_occupation}")
    if profile.brothers_count is not None or profile.sisters_count is not None:
        siblings = f"👨‍👩‍👧‍👦 {profile.brothers_count or 0} брат. / {profile.sisters_count or 0} сестр."
        if profile.family_position:
            pos_map = {"oldest": "старший", "middle": "средний", "youngest": "младший", "only": "единственный"}
            siblings += f" ({pos_map.get(profile.family_position.value, '')})"
        lines.append(siblings)

    lines.append(f"👁 Просмотров: {profile.views_count or 0}")

    return "\n".join(lines)


@router.callback_query(F.data == "search:browse")
@router.callback_query(F.data.startswith("search_page:"))
async def search_profiles(callback: CallbackQuery, session: AsyncSession):
    """Показать результаты поиска."""
    lang = await get_lang(session, callback.from_user.id)

    # Определяем страницу
    if callback.data.startswith("search_page:"):
        page = int(callback.data.split(":")[1])
    else:
        page = 0

    scored = await get_search_results(session, callback.from_user.id)

    if not scored:
        await callback.message.edit_text(t("search_empty", lang), reply_markup=back_kb(lang))
        await callback.answer()
        return

    total_pages = (len(scored) + PROFILES_PER_PAGE - 1) // PROFILES_PER_PAGE
    page = min(page, total_pages - 1)
    start = page * PROFILES_PER_PAGE
    page_profiles = scored[start:start + PROFILES_PER_PAGE]

    header = t("search_found", lang, count=len(scored))

    # Отправляем первую карточку с навигацией, остальные отдельно
    for i, (profile, score) in enumerate(page_profiles):
        # Увеличиваем просмотры
        profile.views_count = (profile.views_count or 0) + 1

        card_text = format_profile_card(profile, score, lang)

        if i == 0:
            text = header + "\n\n" + card_text
        else:
            text = card_text

        if i == 0 and callback.message:
            try:
                await callback.message.edit_text(text, reply_markup=profile_card_kb(profile.id, lang))
            except Exception:
                await callback.message.answer(text, reply_markup=profile_card_kb(profile.id, lang))
        else:
            await callback.message.answer(text, reply_markup=profile_card_kb(profile.id, lang))

    # Навигация
    if total_pages > 1:
        await callback.message.answer("📄", reply_markup=search_nav_kb(page, total_pages, lang))

    await session.commit()
    await callback.answer()


# ── Избранное ──
@router.callback_query(F.data.startswith("fav:"))
async def add_favorite(callback: CallbackQuery, session: AsyncSession):
    profile_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    # Проверяем нет ли уже
    result = await session.execute(
        select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.profile_id == profile_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        await callback.answer("❤️ Уже в избранном")
        return

    fav = Favorite(user_id=user_id, profile_id=profile_id)
    session.add(fav)
    await session.commit()
    await callback.answer("❤️ Добавлено в избранное")


# ── Шаг 11: Интерес к анкете + уведомление семье ──
@router.callback_query(F.data.startswith("interest:"))
async def express_interest(callback: CallbackQuery, session: AsyncSession, bot: Bot):
    """Пользователь нажал «Узнать подробнее» — уведомляем семью."""
    target_profile_id = int(callback.data.split(":")[1])
    user_id = callback.from_user.id
    lang = await get_lang(session, user_id)

    target_profile = await session.get(Profile, target_profile_id)
    if not target_profile:
        await callback.answer("Анкета не найдена")
        return

    # Создаём запрос на контакт
    cr = ContactRequest(
        requester_user_id=user_id,
        target_profile_id=target_profile_id,
        status=RequestStatus.PENDING,
    )
    session.add(cr)
    target_profile.requests_count = (target_profile.requests_count or 0) + 1
    await session.commit()

    # Находим анкету запрашивающего
    result = await session.execute(
        select(Profile).where(Profile.user_id == user_id).limit(1)
    )
    requester_profile = result.scalar_one_or_none()

    # Уведомляем семью девушки/парня
    if target_profile.user_id:
        target_lang = "ru"
        result = await session.execute(select(User).where(User.id == target_profile.user_id))
        target_user = result.scalar_one_or_none()
        if target_user and target_user.language:
            target_lang = target_user.language.value

        age_str = "?"
        edu_str = "—"
        occ_str = "—"
        req_city = "—"
        res_str = "—"

        if requester_profile:
            if requester_profile.birth_year:
                age_str = age_text(calculate_age(requester_profile.birth_year))
            edu_map = {"secondary": "среднее", "vocational": "среднее спец.", "higher": "высшее", "studying": "учится"}
            if requester_profile.education:
                edu_str = edu_map.get(requester_profile.education.value, "—")
            occ_str = requester_profile.occupation or "—"
            req_city = requester_profile.city or "—"
            if requester_profile.residence_status:
                res_map = {"uzbekistan": "🇺🇿 Узбекистан", "cis": "🇷🇺 СНГ", "usa": "🇺🇸 США", "europe": "🌍 Европа"}
                res_str = res_map.get(requester_profile.residence_status.value, "—")

        try:
            await bot.send_message(
                target_profile.user_id,
                t("notify_interest", target_lang,
                    display_id=target_profile.display_id,
                    city=req_city,
                    age=age_str,
                    education=edu_str,
                    occupation=occ_str,
                    requester_city=req_city,
                    residence=res_str,
                ),
            )
        except Exception:
            pass

    # Шаг 12 — направляем к модератору
    from bot.handlers.menu import get_lang as get_lang_fn
    region = "🇺🇿 Узбекистан"
    moderator = config.moderator_tashkent
    hours = "09:00–21:00 (UZT)"

    if requester_profile and requester_profile.residence_status:
        res = requester_profile.residence_status.value
        if res == "cis":
            region = "🇷🇺 СНГ"
            moderator = config.moderator_cis
            hours = "09:00–21:00 (MSK)"
        elif res == "usa":
            region = "🇺🇸 США"
            moderator = config.moderator_usa
            hours = "09:00–21:00 (EST)"
        elif res == "europe":
            region = "🌍 Европа"
            moderator = config.moderator_europe
            hours = "09:00–21:00 (CET)"

    await callback.message.answer(
        t("contact_moderator", lang, region=region, moderator=moderator, hours=hours),
    )

    # Шаг 13 — предлагаем получить контакт и адрес (оплата)
    await callback.message.answer(
        t("payment_prompt", lang, display_id=target_profile.display_id or "—"),
        reply_markup=get_contact_kb(target_profile_id, lang),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("getcontact:"))
async def get_contact_payment(callback: CallbackQuery, session: AsyncSession):
    """Шаг 13 — переход к оплате для получения контакта."""
    profile_id = int(callback.data.split(":")[1])
    lang = await get_lang(session, callback.from_user.id)

    profile = await session.get(Profile, profile_id)
    if not profile:
        await callback.answer("Анкета не найдена")
        return

    # Определяем регион пользователя для выбора способа оплаты
    result = await session.execute(
        select(Profile).where(Profile.user_id == callback.from_user.id).limit(1)
    )
    user_profile = result.scalar_one_or_none()

    display_id = profile.display_id or "—"
    residence = user_profile.residence_status.value if user_profile and user_profile.residence_status else "uzbekistan"

    from bot.keyboards.inline import payment_uz_kb, payment_cis_kb, payment_intl_kb

    if residence in ("usa", "europe", "citizenship_other", "other_country"):
        text = t("payment_intl", lang, display_id=display_id)
        kb = payment_intl_kb(profile_id, lang)
    elif residence == "cis":
        text = t("payment_cis", lang, display_id=display_id)
        kb = payment_cis_kb(profile_id, lang)
    else:
        text = t("payment_uz", lang, display_id=display_id)
        kb = payment_uz_kb(profile_id, lang)

    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("skip_profile:"))
async def skip_profile(callback: CallbackQuery):
    await callback.answer("❌ Пропущено")
