from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.parse import urljoin

import requests
from django.core.management.base import BaseCommand, CommandError

from scraper.models import GolGame


GOL_HOME_URL = "https://gol.gg/esports/home/"
GOL_AJAX_URL = "https://gol.gg/esports/ajax.home.php"


@dataclass(frozen=True)
class ChampionPick:
    role: str
    champ_id: int
    name: str


def _to_int(value: Any, *, field: str) -> int:
    try:
        return int(value)
    except Exception as e:  # noqa: BLE001
        raise CommandError(f"Champ {field} invalide: {value!r}") from e


def _to_date(value: Any, *, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except Exception as e:  # noqa: BLE001
        raise CommandError(f"Date {field} invalide: {value!r}") from e


def _extract_picks(row: dict[str, Any], side: str) -> list[dict[str, Any]]:
    roles = [("top", "top"), ("jgl", "jungle"), ("mid", "mid"), ("bot", "bot"), ("sup", "support")]
    picks: list[dict[str, Any]] = []
    for short, role in roles:
        champ_id = _to_int(row.get(f"{side}{short}_id"), field=f"{side}{short}_id")
        name = str(row.get(f"{side}{short}_name") or "")
        picks.append({"role": role, "id": champ_id, "name": name})
    return picks


class Command(BaseCommand):
    help = "Scrape the 'Previous 10 games' feed from gol.gg home via its AJAX endpoint."

    def add_arguments(self, parser):
        parser.add_argument("--start", type=int, default=0, help="Offset initial (défaut: 0)")
        parser.add_argument("--step", type=int, default=10, help="Pas d'incrément (défaut: 10)")
        parser.add_argument(
            "--max-pages",
            type=int,
            default=200,
            help="Nombre max de pages à charger (défaut: 200)",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.2,
            help="Pause entre requêtes, en secondes (défaut: 0.2)",
        )

    def handle(self, *args, **options):
        start: int = options["start"]
        step: int = options["step"]
        max_pages: int = options["max_pages"]
        sleep_s: float = options["sleep"]

        if start < 0:
            raise CommandError("--start doit être >= 0")
        if step <= 0:
            raise CommandError("--step doit être > 0")
        if max_pages <= 0:
            raise CommandError("--max-pages doit être > 0")
        if sleep_s < 0:
            raise CommandError("--sleep doit être >= 0")

        session = requests.Session()
        session.trust_env = False

        created = 0
        updated = 0
        empty_pages = 0

        for page_idx in range(max_pages):
            current_start = start + page_idx * step
            self.stdout.write(f"POST {GOL_AJAX_URL} start={current_start}")

            resp = session.post(
                GOL_AJAX_URL,
                data={"start": str(current_start)},
                headers={
                    "User-Agent": "scrapyboard/0.1 (+local dev; requests)",
                    "Accept": "application/json,text/plain,*/*",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://gol.gg",
                    "Referer": GOL_HOME_URL,
                },
                timeout=30,
            )
            resp.raise_for_status()

            try:
                payload = resp.json()
            except json.JSONDecodeError as e:
                raise CommandError(f"Réponse non-JSON (start={current_start})") from e

            if not isinstance(payload, list):
                raise CommandError(f"Format inattendu (start={current_start}): {type(payload).__name__}")

            if not payload:
                empty_pages += 1
                self.stdout.write("→ page vide, arrêt.")
                break

            for row in payload:
                if not isinstance(row, dict):
                    continue

                game_id = _to_int(row.get("game_id"), field="game_id")
                game_date = _to_date(row.get("game_date"), field="game_date")
                game_name = str(row.get("game_name") or "")
                tournament = str(row.get("tournament") or "")

                blue = _extract_picks(row, "blue")
                red = _extract_picks(row, "red")

                obj, was_created = GolGame.objects.update_or_create(
                    game_id=game_id,
                    defaults={
                        "source_url": GOL_HOME_URL,
                        "game_date": game_date,
                        "game_name": game_name,
                        "tournament": tournament,
                        "blue_champions": blue,
                        "red_champions": red,
                        "raw": row,
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

            if sleep_s:
                time.sleep(sleep_s)

        self.stdout.write(self.style.SUCCESS(f"OK: {created} créés, {updated} mis à jour"))

