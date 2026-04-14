import datetime
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import Profile, ProfileType


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
