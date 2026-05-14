"""
Best-effort Telegram progress notifications for R57.

Reads `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from the environment.
Inside Modal these come from the `r57-secrets` Modal secret. Locally they
come from `.env`.

Hard rule: a notification failure NEVER raises. The pipeline must not be
gated on Telegram availability.

Operator setup (Modal):
    modal secret update r57-secrets \\
        TELEGRAM_BOT_TOKEN=<bot token> \\
        TELEGRAM_CHAT_ID=1077552316
"""

from __future__ import annotations

import os

import requests


_TIMEOUT_S = 5
_API = "https://api.telegram.org/bot{token}/sendMessage"


def notify_progress(
    pipeline: str,
    step: str,
    current: int,
    total: int,
    message: str = "",
    emoji: str = "🔄",
) -> bool:
    """Send a one-line progress update to Telegram.

    Returns True if the message was delivered, False otherwise.
    Failures are swallowed — never raise.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False

    suffix = f" — {message}" if message else ""
    text = f"{emoji} {pipeline} | {step}: {current}/{total}{suffix}"
    try:
        resp = requests.post(
            _API.format(token=token),
            json={"chat_id": chat_id, "text": text},
            timeout=_TIMEOUT_S,
        )
        return resp.ok
    except Exception:
        return False
