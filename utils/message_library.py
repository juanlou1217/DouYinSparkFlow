from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None


def _current_china_date() -> datetime.date:
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo("Asia/Shanghai")).date()
    return datetime.now(timezone(timedelta(hours=8))).date()


def load_message_library(path: str) -> list[str]:
    file_path = Path(path)
    if not file_path.exists():
        return []

    return [
        line.strip()
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def pick_daily_message(
    candidates: list[str], account_username: str, friend_name: str
) -> str:
    if not candidates:
        return ""

    day = _current_china_date().isoformat()
    seed = f"{day}|{account_username}|{friend_name}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    index = int(digest, 16) % len(candidates)
    return candidates[index]
