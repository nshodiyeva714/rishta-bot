"""Safe Telegram send wrappers with typed error handling.

Use these in broadcast loops and addressed pushes instead of a raw
``bot.send_*`` + ``except Exception``. Correctly handles:

- ``TelegramRetryAfter`` — sleeps ``retry_after`` seconds and retries once
- ``TelegramForbiddenError`` — user blocked bot / deleted account (log INFO, skip)
- ``TelegramNotFound`` — chat/message not found (log INFO, skip)
- ``TelegramBadRequest`` — e.g. message too long (log WARNING, skip)
- ``TelegramServerError`` / ``TelegramNetworkError`` — transient (sleep + retry)
- other ``TelegramAPIError`` / ``Exception`` — log ERROR, skip

Each helper returns ``True`` on delivery, ``False`` on any failure — so
callers can count successes/skips if needed.

Not intended for callback.answer / edit_text fallback / delete_message —
those keep their local ``except Exception`` because swallowing minor
``TelegramBadRequest`` (message not modified etc.) there is the intended
behaviour.
"""

import asyncio
import logging
from typing import Any

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramNotFound,
    TelegramRetryAfter,
    TelegramServerError,
)

logger = logging.getLogger(__name__)


async def _safe_call(
    coro_factory,
    *,
    chat_id: int,
    label: str,
    retry_on_flood: bool = True,
) -> bool:
    """Общий обработчик. ``coro_factory`` — lambda без аргументов,
    создающая свежую coroutine при каждой попытке."""
    for attempt in (1, 2):
        try:
            await coro_factory()
            return True
        except TelegramRetryAfter as e:
            if retry_on_flood and attempt == 1:
                logger.warning(
                    "[%s] flood control on %s: sleeping %ss",
                    label, chat_id, e.retry_after,
                )
                await asyncio.sleep(e.retry_after + 1)
                continue
            logger.error("[%s] flood limit exceeded for %s", label, chat_id)
            return False
        except TelegramForbiddenError:
            logger.info("[%s] user %s blocked/deleted bot", label, chat_id)
            return False
        except TelegramNotFound:
            logger.info("[%s] chat %s not found", label, chat_id)
            return False
        except TelegramBadRequest as e:
            logger.warning("[%s] bad request for %s: %s", label, chat_id, e)
            return False
        except (TelegramServerError, TelegramNetworkError) as e:
            if attempt == 1:
                logger.warning(
                    "[%s] transient error for %s: %s — retrying in 2s",
                    label, chat_id, e,
                )
                await asyncio.sleep(2)
                continue
            logger.error("[%s] server/network error for %s: %s", label, chat_id, e)
            return False
        except TelegramAPIError as e:
            logger.error("[%s] telegram api error for %s: %s", label, chat_id, e)
            return False
        except Exception as e:
            logger.error("[%s] unexpected error for %s: %s", label, chat_id, e)
            return False
    return False


async def safe_send_message(
    bot: Bot,
    chat_id: int,
    text: str,
    *,
    label: str = "send_message",
    retry_on_flood: bool = True,
    **kwargs: Any,
) -> bool:
    """Отправить текст. См. модуль-docstring."""
    return await _safe_call(
        lambda: bot.send_message(chat_id, text, **kwargs),
        chat_id=chat_id, label=label, retry_on_flood=retry_on_flood,
    )


async def safe_send_photo(
    bot: Bot,
    chat_id: int,
    photo: Any,
    *,
    label: str = "send_photo",
    retry_on_flood: bool = True,
    protect_content: bool = False,
    **kwargs: Any,
) -> bool:
    """Отправить фото с опциональной защитой от пересылки/сохранения.

    ``protect_content=True`` включает Telegram-флаг, блокирующий
    forward, save, screenshot notification (клиенты Telegram его
    уважают: mobile — без сохранения, desktop — без Save As).
    По умолчанию False для обратной совместимости. Используется для
    фото кандидатов (PII) — см. payment.py, moderator.py:confirm_pay.
    """
    if protect_content:
        kwargs["protect_content"] = True
    return await _safe_call(
        lambda: bot.send_photo(chat_id, photo, **kwargs),
        chat_id=chat_id, label=label, retry_on_flood=retry_on_flood,
    )


async def safe_send_document(
    bot: Bot,
    chat_id: int,
    document: Any,
    *,
    label: str = "send_document",
    retry_on_flood: bool = True,
    **kwargs: Any,
) -> bool:
    return await _safe_call(
        lambda: bot.send_document(chat_id, document, **kwargs),
        chat_id=chat_id, label=label, retry_on_flood=retry_on_flood,
    )


async def safe_send_voice(
    bot: Bot,
    chat_id: int,
    voice: Any,
    *,
    label: str = "send_voice",
    retry_on_flood: bool = True,
    **kwargs: Any,
) -> bool:
    return await _safe_call(
        lambda: bot.send_voice(chat_id, voice, **kwargs),
        chat_id=chat_id, label=label, retry_on_flood=retry_on_flood,
    )


async def safe_send_video(
    bot: Bot,
    chat_id: int,
    video: Any,
    *,
    label: str = "send_video",
    retry_on_flood: bool = True,
    **kwargs: Any,
) -> bool:
    return await _safe_call(
        lambda: bot.send_video(chat_id, video, **kwargs),
        chat_id=chat_id, label=label, retry_on_flood=retry_on_flood,
    )
