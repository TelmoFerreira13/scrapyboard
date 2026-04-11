from __future__ import annotations

import time
from typing import Any

import requests
from django.core.management.base import BaseCommand, CommandError

from scraper.models import GolGame

from scraper.services.validators import to_int, to_iso_date, to_str
from scraper.services.http_client import post_json_with_retry
from scraper.services.exceptions import ParseScraperError
from scraper.services.runlog import log_run_start, log_run_end, log_page_request, log_page_rows, log_page_empty, log_retry, log_fatal



GOL_HOME_URL = "https://gol.gg/esports/home/"
GOL_AJAX_URL = "https://gol.gg/esports/ajax.home.php"

SCRAPER_NAME = "scrape_gol_home"


def _extract_picks(row: dict[str, Any], side: str) -> list[dict[str, Any]]:
    roles = [("top", "top"), ("jgl", "jungle"), ("mid", "mid"), ("bot", "bot"), ("sup", "support")]
    picks: list[dict[str, Any]] = []
    for short, role in roles:
        champ_id = to_int(row.get(f"{side}{short}_id"), field=f"{side}{short}_id")
        name = to_str(row.get(f"{side}{short}_name"), field=f"{side}{short}_name", allow_empty=True)
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
        pages_ok = 0
        pages_empty = 0
        t0 = time.perf_counter()
        log_run_start(
            self.stdout,
            scraper=SCRAPER_NAME,
            start=start,
            step=step,
            max_pages=max_pages,
            sleep=sleep_s,
    )

        for page_idx in range(max_pages):
            current_start = start + page_idx * step

            log_page_request(
                self.stdout,
                scraper=SCRAPER_NAME,
                url=GOL_AJAX_URL,
                start=current_start,
                page_idx=page_idx,
            )

            payload = post_json_with_retry(
                session=session,
                url=GOL_AJAX_URL,
                data={"start": str(current_start)},
                headers={
                    "User-Agent": "scrapyboard/0.1 (+local dev; requests)",
                    "Accept": "application/json,text/plain,*/*",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Origin": "https://gol.gg",
                    "Referer": GOL_HOME_URL,
                }
            )

            if not payload:
                pages_empty += 1
                log_page_empty(
                    self.stdout,
                    scraper=SCRAPER_NAME,
                    start=current_start,
                )
                break

            page_created = 0
            page_updated = 0

            for row in payload:
                try:
                    game_id = to_int(row.get("game_id"), field="game_id")
                    game_date = to_iso_date(row.get("game_date"), field="game_date")
                    game_name = to_str(row.get("game_name"), field="game_name")
                    tournament = to_str(row.get("tournament"), field="tournament")
                    blue = _extract_picks(row, "blue")
                    red = _extract_picks(row, "red")
                    _, was_created = GolGame.objects.update_or_create(
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
                except ParseScraperError as e:
                    self.stdout.write(self.style.WARNING(f"→ ligne ignorée: {e}"))
                    continue
                if was_created:
                    created += 1
                    page_created += 1
                else:
                    updated += 1
                    page_updated += 1
            pages_ok += 1
            log_page_rows(
                self.stdout,
                scraper=SCRAPER_NAME,
                start=current_start,
                row_count=len(payload),
                created=page_created,
                updated=page_updated,
            )

            if sleep_s:
                time.sleep(sleep_s)
            
        duration_s = time.perf_counter() - t0
        log_run_end(
            self.stdout,
            scraper=SCRAPER_NAME,
            pages_ok=pages_ok,
            pages_empty=pages_empty,
            created=created,
            updated=updated,
            duration_s=duration_s,
        )

        self.stdout.write(self.style.SUCCESS(f"OK: {created} créés, {updated} mis à jour"))
