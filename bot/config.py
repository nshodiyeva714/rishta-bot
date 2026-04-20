import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])
    database_url: str = field(default_factory=lambda: os.environ["DATABASE_URL"])
    moderator_chat_id: int = field(
        default_factory=lambda: int(os.environ.get("MODERATOR_CHAT_ID", "0")) or 8400995899
    )
    moderator_tashkent: str = field(
        default_factory=lambda: os.environ.get("MODERATOR_TASHKENT", "@rishta_manager_tashkent")
    )
    mod_tashkent_id: int = field(
        default_factory=lambda: int(os.environ.get("MOD_TASHKENT_ID", "0")) or 8400995899
    )
    mod_samarkand_id: int = field(
        default_factory=lambda: int(os.environ.get("MOD_SAMARKAND_ID", "0")) or 6235004229
    )
    mod_vodiy_id: int = field(
        default_factory=lambda: int(os.environ.get("MOD_VODIY_ID", "0"))
    )
    mod_usa_id: int = field(
        default_factory=lambda: int(os.environ.get("MOD_USA_ID", "0"))
    )
    main_moderator_id: int = field(
        default_factory=lambda: int(os.environ.get("MAIN_MODERATOR_ID", "0")) or 8400995899
    )
    moderator_usa: str = field(
        default_factory=lambda: os.environ.get("MODERATOR_USA", "@rishta_manager_usa")
    )
    payme_token: str = field(default_factory=lambda: os.environ.get("PAYME_TOKEN", ""))
    click_token: str = field(default_factory=lambda: os.environ.get("CLICK_TOKEN", ""))
    stripe_secret_key: str = field(default_factory=lambda: os.environ.get("STRIPE_SECRET_KEY", ""))


# ── Реквизиты для оплаты ─────────────────────────────────
CARD_NUMBER = "5614 6887 0899 8959"
CARD_OWNER = "SHODIYEVA NASIBA"

# ── Тарифы: получение контакта ───────────────────────────
PRICE_UZB = 30_000       # сум — Узбекистан
PRICE_SNG = 30_000       # сум — СНГ
PRICE_USA_EUR = 1500     # центы ($15) — США/Европа

# ── Тарифы VIP (в сумах) — Узбекистан ────────────────────
VIP_PRICES_UZB = {
    "7":   35_000,
    "14":  45_000,
    "30":  50_000,
    "90":  120_000,
    "180": 210_000,
    "365": 360_000,
}

# ── Тарифы VIP (в центах) — США/Европа ──────────────────
VIP_PRICES_USD = {
    "7":   300,
    "14":  500,
    "30":  1000,
    "90":  2400,
    "180": 4200,
    "365": 7200,
}

# ── Тарифы VIP (в сумах) — СНГ ───────────────────────────
VIP_PRICES_SNG = {
    "7":   50_000,
    "14":  70_000,
    "30":  75_000,
    "90":  180_000,
    "180": 315_000,
    "365": 540_000,
}

# Метки длительности
VIP_DURATION_LABELS = {
    7:   {"ru": "7 дней",    "uz": "7 kun"},
    14:  {"ru": "14 дней",   "uz": "14 kun"},
    30:  {"ru": "1 месяц",   "uz": "1 oy"},
    90:  {"ru": "3 месяца",  "uz": "3 oy"},
    180: {"ru": "6 месяцев", "uz": "6 oy"},
    365: {"ru": "1 год",     "uz": "1 yil"},
}

config = Config()


def is_moderator(user_id: int) -> bool:
    """Проверяет, является ли пользователь модератором.

    Учитывает всех настроенных модераторов (0 = не настроен, игнорируется).
    """
    mods = {m for m in (
        config.moderator_chat_id,
        config.mod_tashkent_id,
        config.mod_samarkand_id,
        config.main_moderator_id,
        config.mod_vodiy_id,
        config.mod_usa_id,
    ) if m}
    return user_id in mods


# Usernames модераторов (для кнопок с живыми ссылками)
MODERATOR_USERNAMES = {
    "tashkent": os.environ.get("MOD_TASHKENT_USERNAME", "rishta_manager_tashkent"),
    "samarkand": os.environ.get("MOD_SAMARKAND_USERNAME", "rishta_manager_samarkand"),
    "vodiy": os.environ.get("MOD_VODIY_USERNAME", ""),
    "usa": os.environ.get("MOD_USA_USERNAME", ""),
    "cis": os.environ.get("MOD_CIS_USERNAME", ""),
    "europe": os.environ.get("MOD_EUROPE_USERNAME", ""),
}


def get_all_moderator_ids() -> list[int]:
    """Все ID модераторов (для рассылки уведомлений). Фильтрует 0 (не настроен)."""
    ids = {
        config.moderator_chat_id,
        config.mod_tashkent_id,
        config.mod_samarkand_id,
        config.main_moderator_id,
        config.mod_vodiy_id,
        config.mod_usa_id,
    }
    return [mid for mid in ids if mid]


def get_moderator_username(region: str = "tashkent") -> str:
    return MODERATOR_USERNAMES.get(region, "rishta_manager_tashkent") or "rishta_manager_tashkent"
