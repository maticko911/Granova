"""Tanki ovoji okoli OpenAI API — edino mesto, ki kliče API.

Vsi ostali moduli kličejo complete() ali parse(); testi te funkcije mockajo.
"""

import logging
import time
from typing import Callable, TypeVar

import openai
from pydantic import BaseModel

from granova.config import DEFAULT_MODEL, get_client

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
R = TypeVar("R")

# Prehodne napake, ki jih velja ponoviti. AuthenticationError je tu namenoma:
# protivirusno HTTPS skeniranje (npr. Norton) občasno povzroči lažni 401, ki ob
# ponovnem poskusu izgine. Trajno napačen ključ vseeno odpove — le nekaj sekund
# kasneje in z jasnim zapisom v dnevniku.
_TRANSIENT = (
    openai.APIConnectionError,
    openai.APITimeoutError,
    openai.RateLimitError,
    openai.InternalServerError,
    openai.AuthenticationError,
)
_MAX_TRIES = 4


def _with_retry(what: str, call: Callable[[], R]) -> R:
    delay = 0.5
    last: Exception | None = None
    for attempt in range(1, _MAX_TRIES + 1):
        try:
            return call()
        except _TRANSIENT as exc:
            last = exc
            log.warning(
                "OpenAI %s: prehodna napaka %s (poskus %d/%d)",
                what, type(exc).__name__, attempt, _MAX_TRIES,
            )
            if attempt < _MAX_TRIES:
                time.sleep(delay)
                delay = min(delay * 2, 4.0)
    raise last  # type: ignore[misc]


def complete(system: str, user: str, model: str | None = None) -> str:
    """Navaden tekstovni odgovor."""
    def _call():
        return get_client().chat.completions.create(
            model=model or DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )

    response = _with_retry("complete", _call)
    return response.choices[0].message.content or ""


def parse(system: str, user: str, schema: type[T], model: str | None = None) -> T:
    """Strukturiran odgovor, validiran v podani Pydantic model."""
    def _call():
        return get_client().chat.completions.parse(
            model=model or DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=schema,
        )

    response = _with_retry("parse", _call)
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise ValueError(f"Model ni vrnil veljavnega {schema.__name__}")
    return parsed
