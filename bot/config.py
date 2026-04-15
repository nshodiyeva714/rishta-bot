import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])
    database_url: str = field(default_factory=lambda: os.environ["DATABASE_URL"])
    moderator_chat_id: int = field(
        default_factory=lambda: int(os.environ.get("MODERATOR_CHAT_ID", "8400995899"))
    )
    moderator_tashkent: str = field(
        default_factory=lambda: os.environ.get("MODERATOR_TASHKENT", "@rishta_manager_tashkent")
    )
    mod_tashkent_id: int = field(
        default_factory=lambda: int(os.environ.get("MOD_TASHKENT_ID", "8400995899"))
    )
    mod_samarkand_id: int = field(
        default_factory=lambda: int(os.environ.get("MOD_SAMARKAND_ID", "8400995899"))
    )
    main_moderator_id: int = field(
        default_factory=lambda: int(os.environ.get("MAIN_MODERATOR_ID", "8400995899"))
    )
    moderator_usa: str = field(
        default_factory=lambda: os.environ.get("MODERATOR_USA", "@rishta_manager_usa")
    )
    moderator_cis: str = field(
        default_factory=lambda: os.environ.get("MODERATOR_CIS", "@rishta_manager_cis")
    )
    moderator_europe: str = field(
        default_factory=lambda: os.environ.get("MODERATOR_EUROPE", "@rishta_manager_europe")
    )
    payme_token: str = field(default_factory=lambda: os.environ.get("PAYME_TOKEN", ""))
    click_token: str = field(default_factory=lambda: os.environ.get("CLICK_TOKEN", ""))
    stripe_secret_key: str = field(default_factory=lambda: os.environ.get("STRIPE_SECRET_KEY", ""))


config = Config()


def is_moderator(user_id: int) -> bool:
    """Проверяет, является ли пользователь модератором."""
    return user_id in (
        config.moderator_chat_id,
        config.mod_tashkent_id,
        config.mod_samarkand_id,
        config.main_moderator_id,
    )


# Usernames модераторов (для кнопок с живыми ссылками)
MODERATOR_USERNAMES = {
    "tashkent": os.environ.get("MOD_TASHKENT_USERNAME", "rishta_manager_tashkent"),
    "samarkand": os.environ.get("MOD_SAMARKAND_USERNAME", "rishta_manager_tashkent"),
    "usa": os.environ.get("MOD_USA_USERNAME", ""),
    "cis": os.environ.get("MOD_CIS_USERNAME", ""),
    "europe": os.environ.get("MOD_EUROPE_USERNAME", ""),
}


def get_moderator_username(region: str = "tashkent") -> str:
    return MODERATOR_USERNAMES.get(region, "rishta_manager_tashkent") or "rishta_manager_tashkent"
