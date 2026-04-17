"""Добавляет 5 тестовых анкет (3 дочери + 2 сына) в БД.

Запуск: railway run python scripts/add_test_profiles.py
Скрипт идемпотентен — можно запускать несколько раз,
дубли по display_id пропускаются.
"""

import asyncio
import os
import sys

# Чтобы импорт `bot.*` работал при запуске из корня проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from bot.db.models import (
    User, Language, Profile, ProfileType, ProfileStatus,
    Education, Religiosity, MaritalStatus, ChildrenStatus,
)


# Технический пользователь-владелец тестовых анкет.
# Telegram id=0 не существует — такой юзер не будет конфликтовать с реальными.
TECHNICAL_USER_ID = 0


def _test_profiles(owner_user_id: int) -> list[Profile]:
    """Список тестовых анкет — 3 дочери + 2 сына."""
    return [
        Profile(
            user_id=owner_user_id,
            name="Малика",
            birth_year=2000,
            height_cm=165,
            body_type="slim",
            nationality="🇺🇿 Узбечка",
            city="Ташкент",
            city_code="tashkent",
            district="Юнусабад",
            country="uzbekistan",
            education=Education.HIGHER,
            occupation="works",
            religiosity=Religiosity.MODERATE,
            marital_status=MaritalStatus.NEVER_MARRIED,
            children_status=ChildrenStatus.NO,
            father_occupation="Врач",
            mother_occupation="Учитель",
            profile_type=ProfileType.DAUGHTER,
            status=ProfileStatus.PUBLISHED,
            is_active=True,
            display_id="ДД-2026-00010",
            views_count=15,
        ),
        Profile(
            user_id=owner_user_id,
            name="Нилуфар",
            birth_year=1998,
            height_cm=162,
            body_type="average",
            nationality="🇺🇿 Узбечка",
            city="Самарканд",
            city_code="samarkand",
            district="Центр",
            country="uzbekistan",
            education=Education.HIGHER,
            occupation="works",
            religiosity=Religiosity.PRACTICING,
            marital_status=MaritalStatus.NEVER_MARRIED,
            children_status=ChildrenStatus.NO,
            father_occupation="Предприниматель",
            mother_occupation="Домохозяйка",
            profile_type=ProfileType.DAUGHTER,
            status=ProfileStatus.PUBLISHED,
            is_active=True,
            display_id="ДД-2026-00011",
            views_count=8,
        ),
        Profile(
            user_id=owner_user_id,
            name="Зарина",
            birth_year=2002,
            height_cm=168,
            body_type="athletic",
            nationality="🇺🇿 Узбечка",
            city="Фергана",
            city_code="fergana",
            district="",
            country="uzbekistan",
            education=Education.STUDYING,
            occupation="student",
            religiosity=Religiosity.MODERATE,
            marital_status=MaritalStatus.NEVER_MARRIED,
            children_status=ChildrenStatus.NO,
            father_occupation="Инженер",
            mother_occupation="Бухгалтер",
            profile_type=ProfileType.DAUGHTER,
            status=ProfileStatus.PUBLISHED,
            is_active=True,
            display_id="ДД-2026-00012",
            views_count=22,
        ),
        Profile(
            user_id=owner_user_id,
            name="Алишер",
            birth_year=1997,
            height_cm=178,
            body_type="athletic",
            nationality="🇺🇿 Узбек",
            city="Ташкент",
            city_code="tashkent",
            district="Чиланзар",
            country="uzbekistan",
            education=Education.HIGHER,
            occupation="business",
            religiosity=Religiosity.MODERATE,
            marital_status=MaritalStatus.NEVER_MARRIED,
            children_status=ChildrenStatus.NO,
            father_occupation="Директор",
            mother_occupation="Учитель",
            profile_type=ProfileType.SON,
            status=ProfileStatus.PUBLISHED,
            is_active=True,
            display_id="СН-2026-00010",
            views_count=30,
        ),
        Profile(
            user_id=owner_user_id,
            name="Бобур",
            birth_year=1999,
            height_cm=175,
            body_type="average",
            nationality="🇺🇿 Узбек",
            city="Андижан",
            city_code="andijan",
            district="",
            country="uzbekistan",
            education=Education.HIGHER,
            occupation="works",
            religiosity=Religiosity.PRACTICING,
            marital_status=MaritalStatus.NEVER_MARRIED,
            children_status=ChildrenStatus.NO,
            father_occupation="Врач",
            mother_occupation="Врач",
            profile_type=ProfileType.SON,
            status=ProfileStatus.PUBLISHED,
            is_active=True,
            display_id="СН-2026-00011",
            views_count=12,
        ),
    ]


async def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("❌ DATABASE_URL не установлен. Запускай через `railway run`.")
        sys.exit(1)

    # Postgres-схема URL → asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(url)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        # 1. Технический владелец
        owner = await session.get(User, TECHNICAL_USER_ID)
        if not owner:
            owner = User(id=TECHNICAL_USER_ID, language=Language.RU)
            session.add(owner)
            await session.commit()
            print(f"✅ Создан технический user id={TECHNICAL_USER_ID}")
        else:
            print(f"ℹ️  Технический user id={TECHNICAL_USER_ID} уже существует")

        # 2. Анкеты — пропускаем дубли по display_id
        created = 0
        skipped = 0
        for p in _test_profiles(owner_user_id=TECHNICAL_USER_ID):
            res = await session.execute(
                select(Profile).where(Profile.display_id == p.display_id)
            )
            existing = res.scalar_one_or_none()
            if existing:
                print(f"⏭  {p.display_id} уже существует — пропущено")
                skipped += 1
                continue
            session.add(p)
            created += 1

        if created:
            await session.commit()
        print(f"\n✅ Готово: создано {created}, пропущено {skipped} из 5 анкет")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
