from __future__ import annotations

import hashlib
import json
import os
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


def _resolve_library_path(path: str) -> Path:
    file_path = Path(path)
    if file_path.exists():
        return file_path

    if file_path.suffix.lower() == ".md":
        json_path = file_path.with_suffix(".json")
        if json_path.exists():
            return json_path

    return file_path


def load_message_library(path: str) -> list[str]:
    file_path = _resolve_library_path(path)
    if not file_path.exists():
        return []

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []

    if not isinstance(data, list):
        return []

    return [item.strip() for item in data if isinstance(item, str) and item.strip()]


def _message_run_salt() -> str:
    if os.getenv("GITHUB_ACTIONS") != "true":
        return ""

    run_id = os.getenv("GITHUB_RUN_ID", "")
    run_attempt = os.getenv("GITHUB_RUN_ATTEMPT", "")
    return f"{run_id}|{run_attempt}"


def pick_daily_message(
    candidates: list[str], account_username: str, friend_name: str
) -> str:
    if not candidates:
        return ""

    day = _current_china_date().isoformat()
    seed_parts = [day, account_username, friend_name]
    run_salt = _message_run_salt()
    if run_salt:
        seed_parts.append(run_salt)
    seed = "|".join(seed_parts)
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    index = int(digest, 16) % len(candidates)
    return candidates[index]
