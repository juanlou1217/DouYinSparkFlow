from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None


LIST_PREFIX_RE = re.compile(r"^(?:[-*+]\s+|\d+\.\s+)")


def _current_china_date() -> datetime.date:
    if ZoneInfo is not None:
        return datetime.now(ZoneInfo("Asia/Shanghai")).date()
    return datetime.now(timezone(timedelta(hours=8))).date()


def load_message_library(path: str) -> list[str]:
    file_path = Path(path)
    if not file_path.exists():
        return []

    lines = file_path.read_text(encoding="utf-8").splitlines()
    candidates: list[str] = []
    in_frontmatter = False
    in_comment_block = False

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()

        if index == 0 and line == "---":
            in_frontmatter = True
            continue
        if in_frontmatter:
            if line == "---":
                in_frontmatter = False
            continue

        if line == "%%":
            in_comment_block = not in_comment_block
            continue
        if in_comment_block:
            continue

        if not line or line.startswith("#") or line.startswith("> [!"):
            continue

        line = re.sub(r"%%.*?%%", "", line).strip()
        line = LIST_PREFIX_RE.sub("", line).strip()
        if line:
            candidates.append(line)

    return candidates


def pick_daily_message(
    candidates: list[str], account_username: str, friend_name: str
) -> str:
    if not candidates:
        return ""

    day = _current_china_date().isoformat()
    seed = f"{day}|{account_username}|{friend_name}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    index = int(digest, 16) % len(candidates)
    template = candidates[index]
    return template.format(friend=friend_name, date=day)
