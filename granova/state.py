"""Obstojnost sej: transkript se shrani na disk PRED obdelavo.

Če aplikacija ali internet med izdelavo zapiskov odpove, se ob naslednjem
zagonu čakajoča opravila samodejno ponovijo. Po uspešnem zapisu v Google Doc
se datoteka izbriše.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path

from granova.config import APP_DIR

logger = logging.getLogger(__name__)

JOBS_DIR = APP_DIR / "jobs"


def save_job(transcript: str, title: str, raw_notes: str = "") -> Path:
    """Shrani opravilo na disk in vrne pot (kliči PRED obdelavo)."""
    JOBS_DIR.mkdir(parents=True, exist_ok=True)
    path = JOBS_DIR / f"{int(time.time())}-{uuid.uuid4().hex[:8]}.json"
    path.write_text(
        json.dumps(
            {"transcript": transcript, "title": title, "raw_notes": raw_notes},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def load_jobs() -> list[tuple[Path, dict]]:
    """Vrne čakajoča opravila (najstarejša najprej); pokvarjene datoteke preskoči."""
    if not JOBS_DIR.exists():
        return []
    jobs = []
    for path in sorted(JOBS_DIR.glob("*.json")):
        try:
            jobs.append((path, json.loads(path.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            logger.warning("Pokvarjeno opravilo preskočeno: %s", path)
    return jobs


def delete_job(path: Path) -> None:
    """Izbriše opravilo po uspešni obdelavi."""
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Brisanje opravila ni uspelo: %s", path)
