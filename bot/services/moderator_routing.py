"""Маршрутизация заявок к правильному модератору по региону пользователя.

Используется в адресных пушах (VIP-заявки, контакт-запросы, жалобы,
скриншоты оплаты, приглашения на встречу, новые анкеты на проверку).

Guard-ы /ankety /vip /stats /find /requests — НЕ трогаем: доступ для всех
через is_moderator(). /reset — только Ташкент (захардкожено).

Правила:
- residence_status == "usa" → USA (fallback → Самарканд если USA не настроен)
- residence_status in (europe, cis, citizenship_other, other_country,
  residence_permit) → Ташкент
- residence_status == "uzbekistan" → по city_code:
    * tashkent, tashkent_region, jizzakh, sirdarya → Ташкент
    * samarkand, bukhara, navoi, kashkadarya, surkhandarya,
      khorezm, karakalpakstan, nukus → Самарканд
    * fergana, andijan, namangan → Водий (fallback → Ташкент)
- Любое нераспознанное (пустое city_code, неизвестная страна,
  NULL residence_status) → Ташкент (safety-net)

Копия для контроля (control copy):
- Только для VIP-заявок из USA → копия в Ташкент.
- Все другие типы уведомлений — без копии.
"""

from typing import Optional

from bot.config import config, MODERATOR_USERNAMES
from bot.db.models import Profile, ResidenceStatus


REGION_TASHKENT = "tashkent"
REGION_SAMARKAND = "samarkand"
REGION_VODIY = "vodiy"
REGION_USA = "usa"


# city_code (UZ) → region
_UZ_CITY_TO_REGION = {
    # Ташкент
    "tashkent":        REGION_TASHKENT,
    "tashkent_region": REGION_TASHKENT,
    "jizzakh":         REGION_TASHKENT,
    "sirdarya":        REGION_TASHKENT,
    # Самарканд
    "samarkand":       REGION_SAMARKAND,
    "bukhara":         REGION_SAMARKAND,
    "navoi":           REGION_SAMARKAND,
    "kashkadarya":     REGION_SAMARKAND,
    "surkhandarya":    REGION_SAMARKAND,
    "khorezm":         REGION_SAMARKAND,
    "karakalpakstan":  REGION_SAMARKAND,
    "nukus":           REGION_SAMARKAND,
    # Водий
    "fergana":         REGION_VODIY,
    "andijan":         REGION_VODIY,
    "namangan":        REGION_VODIY,
}


# Человеко-читаемые метки для карточек модератору
_REGION_LABELS = {
    REGION_TASHKENT:  "Ташкент",
    REGION_SAMARKAND: "Самарканд",
    REGION_VODIY:     "Водий",
    REGION_USA:       "США",
}


def _region_for_profile(profile: Profile) -> str:
    """Определить регион по residence_status + city_code. Safety-net → Ташкент."""
    if profile is None:
        return REGION_TASHKENT

    res = profile.residence_status
    res_val = res.value if isinstance(res, ResidenceStatus) else res

    if res_val == "usa":
        return REGION_USA
    if res_val in ("europe", "cis", "citizenship_other", "other_country", "residence_permit"):
        return REGION_TASHKENT

    # UZBEKISTAN или NULL → смотрим city_code
    code = (profile.city_code or "").strip().lower()
    return _UZ_CITY_TO_REGION.get(code, REGION_TASHKENT)


def _resolve_id_for_region(region: str) -> Optional[int]:
    """Вернуть telegram_id модератора по региону с учётом fallback."""
    if region == REGION_VODIY:
        return config.mod_vodiy_id or config.mod_tashkent_id
    if region == REGION_USA:
        return config.mod_usa_id or config.mod_samarkand_id
    if region == REGION_SAMARKAND:
        return config.mod_samarkand_id or config.mod_tashkent_id
    # REGION_TASHKENT и default
    return config.mod_tashkent_id


def _username_for_region(region: str) -> str:
    return MODERATOR_USERNAMES.get(region) or MODERATOR_USERNAMES.get("tashkent", "rishta_manager_tashkent")


def resolve_primary_moderator(profile: Profile) -> dict:
    """Основной модератор для адресного пуша по анкете.

    Возвращает: {"telegram_id": int, "username": str, "region": str, "region_label": str}
    region — внутренний ключ (tashkent/samarkand/vodiy/usa),
    region_label — для показа модератору (Ташкент/Самарканд/Водий/США).
    """
    region = _region_for_profile(profile)
    return {
        "telegram_id": _resolve_id_for_region(region),
        "username": _username_for_region(region),
        "region": region,
        "region_label": _REGION_LABELS.get(region, "Ташкент"),
    }


def resolve_control_copy_moderator(profile: Profile) -> Optional[int]:
    """Telegram_id модератора для копии-контроля. Только USA → Ташкент.

    Используется ТОЛЬКО для VIP-заявок. Не для контактов, жалоб, встреч.
    """
    region = _region_for_profile(profile)
    if region != REGION_USA:
        return None
    # Копия в Ташкент; если primary уже Ташкент (fallback сработал на USA без настройки) — не дублируем
    primary_id = _resolve_id_for_region(region)
    if primary_id == config.mod_tashkent_id:
        return None
    return config.mod_tashkent_id or None


def region_label_for_profile(profile: Profile) -> str:
    """Короткая метка региона для пометок в карточке модератору."""
    return _REGION_LABELS.get(_region_for_profile(profile), "Ташкент")
