"""Audit log for financial / moderator actions.

Single-line key=value format with ``[AUDIT]`` prefix — grep-friendly.
Uses the shared logger at INFO level, so audit events appear in the
same Railway stream as other INFO logs but can be filtered with one
grep::

    grep "^.*\\[AUDIT\\]" railway.log
    grep "\\[AUDIT\\] action=payment_confirmed" railway.log
    grep "\\[AUDIT\\].*actor=mod:8400995899" railway.log

Use for: payment confirm/reject, VIP request approve/reject, manual
VIP grant/remove, profile publish/block, contact request early reject,
user-side payment/VIP submission, auto VIP expiry.

Do NOT use for general debug/info logs — this module is a narrow
feed of state-changing events for compliance and debugging.
"""

import logging

logger = logging.getLogger(__name__)


def audit(action: str, **fields) -> None:
    """Write one audit-event line.

    ``action`` — short snake_case verb, e.g. ``payment_confirmed``.
    ``**fields`` — key=value pairs. ``None`` values are dropped.

    Example::

        audit("payment_confirmed",
              actor="mod:8400995899",
              target="user:12345",
              payment_id=42,
              amount=30000,
              currency="UZS",
              display_id="ЗАП-007")

    Produces::

        [AUDIT] action=payment_confirmed actor=mod:8400995899 target=user:12345 payment_id=42 amount=30000 currency=UZS display_id=ЗАП-007
    """
    parts = [f"{k}={_fmt(v)}" for k, v in fields.items() if v is not None]
    logger.info("[AUDIT] action=%s %s", action, " ".join(parts))


def _fmt(val) -> str:
    """Format one field value. Strings with spaces get quoted to stay
    on one grep-able line."""
    s = str(val)
    return f'"{s}"' if " " in s else s
