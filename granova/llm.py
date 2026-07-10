"""Tanki ovoji okoli OpenAI API — edino mesto, ki kliče API.

Vsi ostali moduli kličejo complete() ali parse(); testi te funkcije mockajo.
"""

import logging
from typing import TypeVar

from pydantic import BaseModel

from granova.config import DEFAULT_MODEL, get_client

log = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def complete(system: str, user: str, model: str | None = None) -> str:
    """Navaden tekstovni odgovor."""
    response = get_client().chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content or ""


def parse(system: str, user: str, schema: type[T], model: str | None = None) -> T:
    """Strukturiran odgovor, validiran v podani Pydantic model."""
    response = get_client().chat.completions.parse(
        model=model or DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=schema,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise ValueError(f"Model ni vrnil veljavnega {schema.__name__}")
    return parsed
