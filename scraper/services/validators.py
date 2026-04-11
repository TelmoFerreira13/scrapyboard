from __future__ import annotations

from datetime import date
from typing import Any

from .exceptions import ParseScraperError


def to_int(value: Any, *, field: str) -> int:
    """
    Convertit une valeur en int.
    Lève ParseScraperError si conversion impossible.
    """
    try:
        return int(value)
    except (TypeError, ValueError) as e:
        raise ParseScraperError(f"Champ '{field}' invalide (int attendu): {value!r}") from e


def to_iso_date(value: Any, *, field: str) -> date:
    """
    Convertit une date ISO YYYY-MM-DD en datetime.date.
    """
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as e:
        raise ParseScraperError(
            f"Champ '{field}' invalide (date ISO attendue YYYY-MM-DD): {value!r}"
        ) from e


def to_str(value: Any, *, field: str, allow_empty: bool = False) -> str:
    """
    Convertit en str et trim.
    - allow_empty=False: champ vide interdit.
    """
    text = "" if value is None else str(value).strip()
    if not allow_empty and text == "":
        raise ParseScraperError(f"Champ '{field}' vide (texte obligatoire)")
    return text
