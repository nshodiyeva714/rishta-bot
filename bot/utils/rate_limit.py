"""Sliding-window rate limits for user actions.

Counts user-initiated records in the database for the past
``window_hours`` and returns ``(allowed, current_count)``.
Moderators are NOT filtered here — callers must skip the
rate-limit check via ``is_moderator()`` guard on their side.

Used in:
- bot/handlers/search.py: contact requests (express_interest,
  request_contact — both create ContactRequest rows, counted
  under a single "contact_request" action).
- bot/handlers/complaint.py: complaint submissions.

Uses ``datetime.utcnow()`` (naive) to match the naive
``created_at`` timestamps stored in the DB by SQLAlchemy's
``server_default=func.now()``.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import ContactRequest, Complaint

logger = logging.getLogger(__name__)


# ── Лимиты (per-user, скользящее окно 24 часа) ──
CONTACT_REQUEST_LIMIT_PER_DAY = 15
COMPLAINT_LIMIT_PER_DAY = 3


async def check_rate_limit(
    session: AsyncSession,
    user_id: int,
    action: str,
    limit: int,
    window_hours: int = 24,
) -> tuple[bool, int]:
    """Проверяет, не превышен ли лимит действий пользователя.

    ``action`` — ``"contact_request"`` или ``"complaint"``.

    Returns:
        (allowed, current_count)
        - ``allowed``: ``True`` если ``count < limit``, иначе ``False``.
        - ``current_count``: сколько уже создано в скользящем окне.
    """
    threshold = datetime.utcnow() - timedelta(hours=window_hours)

    if action == "contact_request":
        model = ContactRequest
        user_col = ContactRequest.requester_user_id
    elif action == "complaint":
        model = Complaint
        user_col = Complaint.reporter_user_id
    else:
        # Fail-open для неизвестного action, чтобы не ломать логику вызова.
        logger.warning("check_rate_limit: unknown action %r", action)
        return (True, 0)

    result = await session.execute(
        select(func.count(model.id))
        .where(user_col == user_id, model.created_at >= threshold)
    )
    count = result.scalar() or 0
    return (count < limit, count)
