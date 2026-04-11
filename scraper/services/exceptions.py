class ScraperError(Exception):
    """Base commune pour toutes les erreurs de scraping."""

class TransientScraperError(ScraperError):
    """Erreur temporaire: retry possible (timeout, 429, 5xx)."""

class FatalScraperError(ScraperError):
    """Erreur fatale: retry inutile immédiat (404, 401, format cassé)."""

class ParseScraperError(FatalScraperError):
    """Payload invalide (JSON non conforme, champ critique absent)."""

class HttpStatusScraperError(ScraperError):
    """
    Erreur HTTP enrichie.
    On décide retry/stop via `is_retryable`.
    """

    def __init__(self, status_code: int, url: str, *, is_retryable: bool):
        self.status_code = status_code
        self.url = url
        self.is_retryable = is_retryable
        super().__init__(f"HTTP {status_code} on {url} (retryable={is_retryable})")