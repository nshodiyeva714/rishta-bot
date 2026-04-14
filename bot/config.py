import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: os.environ["BOT_TOKEN"])
    database_url: str = field(default_factory=lambda: os.environ["DATABASE_URL"])
    moderator_chat_id: int = field(
        default_factory=lambda: int(os.environ.get("MODERATOR_CHAT_ID", "0"))
    )
    moderator_tashkent: str = field(
        default_factory=lambda: os.environ.get("MODERATOR_TASHKENT", "@rishta_manager_tashkent")
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
