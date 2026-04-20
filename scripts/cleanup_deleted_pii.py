"""Одноразовая очистка PII у Profile со status=DELETED.

Применяет задним числом ту же санитизацию, что коммит a68cc3d делает
для новых удалений (через _soft_delete_profile helper в menu.py):

  - photo_file_id / photo_type
  - parent_phone / parent_telegram / candidate_telegram
  - address / location_lat / location_lon / location_link
  - health_notes

Demographic data (имя, возраст, рост, образование и т.д.) и счётчики
(views_count / requests_count) сохраняются — они нужны для статистики.

Использование:

  # Dry-run (ничего не меняет, показывает сколько записей затронет):
  railway run python scripts/cleanup_deleted_pii.py --dry-run

  # Применить:
  railway run python scripts/cleanup_deleted_pii.py

Скрипт идемпотентен — повторный запуск ничего не испортит (все поля
уже None → SQLAlchemy не отправит UPDATE).
"""

import argparse
import asyncio
import os
import sys

# Импорт `bot.*` работает при запуске из корня проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, or_

from bot.db.engine import async_session
from bot.db.models import Profile, ProfileStatus, PhotoType


# Поля, которые обнуляем. Должны совпадать с _soft_delete_profile в
# bot/handlers/menu.py — при изменениях синхронизировать оба места.
PII_FIELDS_TO_NONE = (
    "photo_file_id",
    "parent_phone",
    "parent_telegram",
    "candidate_telegram",
    "address",
    "location_lat",
    "location_lon",
    "location_link",
    "health_notes",
)


async def cleanup(dry_run: bool) -> None:
    async with async_session() as session:
        # Все DELETED-анкеты, у которых ЕЩЁ есть хотя бы одно PII-поле.
        # Это критерий "что ещё нужно почистить" — идемпотентность.
        conditions = [getattr(Profile, f).isnot(None) for f in PII_FIELDS_TO_NONE]
        conditions.append(Profile.photo_type != PhotoType.NONE)

        stmt = (
            select(Profile)
            .where(Profile.status == ProfileStatus.DELETED)
            .where(or_(*conditions))
        )
        result = await session.execute(stmt)
        profiles = result.scalars().all()

        total = len(profiles)
        if total == 0:
            print("✅ Ничего чистить не нужно — все DELETED-анкеты уже без PII.")
            return

        # Для отчётности — посчитаем, какие поля не-None у найденных записей
        field_counts: dict[str, int] = {f: 0 for f in PII_FIELDS_TO_NONE}
        field_counts["photo_type (non-NONE)"] = 0

        for p in profiles:
            for f in PII_FIELDS_TO_NONE:
                if getattr(p, f) is not None:
                    field_counts[f] += 1
            if p.photo_type is not None and p.photo_type != PhotoType.NONE:
                field_counts["photo_type (non-NONE)"] += 1

        print(f"📋 Найдено DELETED-анкет с остатками PII: {total}")
        print("   Распределение по полям:")
        for f, n in field_counts.items():
            if n > 0:
                print(f"     - {f}: {n}")

        if dry_run:
            print("\n🔍 DRY-RUN — изменения НЕ применены. Запусти без --dry-run.")
            return

        # Применяем
        for p in profiles:
            for f in PII_FIELDS_TO_NONE:
                setattr(p, f, None)
            p.photo_type = PhotoType.NONE

        await session.commit()
        print(f"\n✅ Обработано: {total} анкет. PII очищена.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Почистить PII у DELETED-анкет (ретроспективно).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Показать, сколько записей будет обновлено, без реальных изменений.",
    )
    args = parser.parse_args()
    asyncio.run(cleanup(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
