# scraper/services/http_client.py

from __future__ import annotations

import json
import time
from typing import Any

import requests

from .exceptions import FatalScraperError, ParseScraperError, TransientScraperError

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _sleep_for_attempt(attempt: int, backoff_seconds: tuple[float, ...]) -> None:
    """
    attempt est 1-indexé.
    Ex: backoff=(1,2,4) -> attempt1=1s, attempt2=2s, attempt3=4s
    """
    idx = min(attempt - 1, len(backoff_seconds) - 1)
    delay = backoff_seconds[idx]
    if delay > 0:
        time.sleep(delay)


def post_json_with_retry(
    session: requests.Session,
    *,
    url: str,
    data: dict[str, str],
    headers: dict[str, str] | None = None,
    timeout: int = 30,
    max_retries: int = 3,
    backoff_seconds: tuple[float, ...] = (1, 2, 4),
) -> list[dict[str, Any]]:
    """
    POST un formulaire et retourne un payload JSON attendu comme list[dict].

    Politique:
    - retry sur timeout/connexion + statuts retryables (429, 5xx)
    - fatal sur 4xx (hors 429)
    - fatal si JSON invalide ou format inattendu
    """
    if max_retries <= 0:
        raise ValueError("max_retries must be > 0")

    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = session.post(
                url,
                data=data,
                headers=headers or {},
                timeout=timeout,
            )

            status = resp.status_code

            if status in RETRYABLE_STATUS_CODES:
                raise TransientScraperError(f"Retryable HTTP {status} on {url}")

            if 400 <= status < 500:
                raise FatalScraperError(f"Fatal HTTP {status} on {url}")

            try:
                payload = resp.json()
            except json.JSONDecodeError as e:
                raise ParseScraperError(f"Non-JSON response from {url}") from e

            if not isinstance(payload, list):
                raise ParseScraperError(
                    f"Unexpected payload type from {url}: {type(payload).__name__}"
                )

            # Optionnel strict: vérifier que chaque item est dict
            if any(not isinstance(item, dict) for item in payload):
                raise ParseScraperError(f"Payload items must be dict from {url}")

            return payload

        except (requests.Timeout, requests.ConnectionError, TransientScraperError) as e:
            last_error = e
            if attempt == max_retries:
                break
            _sleep_for_attempt(attempt, backoff_seconds)

        except (FatalScraperError, ParseScraperError):
            # Erreurs non retryables: on propage immédiatement
            raise

    raise TransientScraperError(
        f"Retry exhausted after {max_retries} attempts: {last_error or 'unknown transient error'}"
    )