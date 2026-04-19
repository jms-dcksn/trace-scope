"""Shared markdown report helpers."""
from datetime import datetime
from pathlib import Path

REPORTS_DIR = Path(__file__).parent


def md_escape(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def write_report(prefix: str, body: str) -> Path:
    """Write `body` to `<prefix>-<timestamp>.md` next to this file."""
    ts = timestamp().replace(":", "-")
    path = REPORTS_DIR / f"{prefix}-{ts}.md"
    path.write_text(body if body.endswith("\n") else body + "\n")
    return path
