from __future__ import annotations

from datetime import date
from typing import Any

from decimal import Decimal, InvalidOperation

from .exceptions import ParseScraperError


def to_int(value: Any, *, field: str, empty_as_zero: bool = False) -> int:
    """
    Convertit une valeur en int.
    - Si empty_as_zero=True:
      None, "" ou "   " -> 0
    - Sinon:
      lève ParseScraperError pour les valeurs vides/invalides.
    """
    if value is None:
        if empty_as_zero:
            return 0
        raise ParseScraperError(f"Champ '{field}' invalide (int attendu): {value!r}")
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            if empty_as_zero:
                return 0
            raise ParseScraperError(f"Champ '{field}' invalide (int attendu): {value!r}")
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

def to_decimal(value: Any, *, field: str) -> Decimal:
    """
    Convertit une valeur en Decimal.
    Accepte les nombres en str/int/float, gère les '%' et les virgules décimales.
    Lève ParseScraperError si conversion impossible.
    """
    text = "" if value is None else str(value).strip()
    if text == "":
        raise ParseScraperError(f"Champ '{field}' vide (decimal attendu)")
    # Cas usuels du scrape
    text = text.replace("%", "").replace(",", ".")
    try:
        return Decimal(text)
    except (InvalidOperation, TypeError, ValueError) as e:
        raise ParseScraperError(
            f"Champ '{field}' invalide (decimal attendu): {value!r}"
        ) from e