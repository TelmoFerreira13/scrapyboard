from __future__ import annotations
from turtle import mode

from django.core.management.base import BaseCommand, CommandError

import re
import json
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from scraper.models import GolGame, GameFullStats
from scraper.services.validators import to_decimal, to_int


GOL_URL = "https://gol.gg/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://gol.gg/",
}

STAT_MAP = {
    "Level": "level",
    "Kills": "kills",
    "Deaths": "deaths",
    "Assists": "assists",
    "KDA": "kda",
    "CS": "cs",
    "CS in Team's Jungle": "cs_in_team_jungle",
    "CS in Enemy Jungle": "cs_in_enemy_jungle",
    "CSM": "csm",
    "Golds": "golds",
    "GPM": "gpm",
    "GOLD%": "gold_pct",
    "Vision Score": "vision_score",
    "Wards placed": "wards_placed",
    "Wards destroyed": "wards_destroyed",
    "Control Wards Purchased": "control_wards_purchased",
    "Detector Wards Placed": "detector_wards_placed",
    "VSPM": "vspm",
    "WPM": "wpm",
    "VWPM": "vwpm",
    "WCPM": "wcpm",
    "VS%": "vs_pct",
    "Total damage to Champion": "total_damage_to_champion",
    "Physical Damage": "physical_damage",
    "Magic Damage": "magic_damage",
    "True Damage": "true_damage",
    "DPM": "dpm",
    "DMG%": "dmg_pct",
    "K+A Per Minute": "ka_per_minute",
    "KP%": "kp_pct",
    "Solo kills": "solo_kills",
    "Double kills": "double_kills",
    "Triple kills": "triple_kills",
    "Quadra kills": "quadra_kills",
    "Penta kills": "penta_kills",
    "GD@15": "gd_at_15",
    "CSD@15": "csd_at_15",
    "XPD@15": "xpd_at_15",
    "LVLD@15": "lvld_at_15",
    "Objectives Stolen": "objectives_stolen",
    "Damage dealt to turrets": "damage_dealt_to_turrets",
    "Damage dealt to buildings": "damage_dealt_to_buildings",
    "Total heal": "total_heal",
    "Total Heals On Teammates": "total_heals_on_teammates",
    "Damage self mitigated": "damage_self_mitigated",
    "Total Damage Shielded On Teammates": "total_damage_shielded_on_teammates",
    "Time ccing others": "time_ccing_others",
    "Total Time CC Dealt": "total_time_cc_dealt",
    "Total damage taken": "total_damage_taken",
    "Total Time Spent Dead": "total_time_spent_dead",
    "Consumables purchased": "consumables_purchased",
    "Items Purchased": "items_purchased",  # attention: P majuscule
    "Shutdown bounty collected": "shutdown_bounty_collected",
    "Shutdown bounty lost": "shutdown_bounty_lost",
}

class Command(BaseCommand):
    help = "Scrape all stats from a game page."


    def _fetch_soup(self, session: requests.Session, url: str) -> BeautifulSoup:
        resp = session.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    def extract_game_ids(self, game_urls: list[str]) -> list[int]:
        game_ids: list[int] = []
        for url in game_urls:
            m = re.search(r"/stats/(\d+)/", url)
            if m:
                game_ids.append(int(m.group(1)))
        game_ids = list(set(game_ids))
        print("game_ids", game_ids)
        return game_ids

    def _discover_game_page_urls(self, menu_soup: BeautifulSoup, current_page_url: str) -> list[str]:
        """
        À partir du HTML déjà parsé d'une page match, retourne les URLs absolues
        des entrées 'Game N' (page-game), dans l'ordre du menu.
        """
        print("current_page_url", current_page_url)
        menu = menu_soup.select_one("#gameMenuToggler")
        if not menu:
            return []

        urls: list[str] = []
        for a in menu.select('a[href*="page-game"]'):
            label = (a.get_text() or "").strip()
            if not re.match(r"^Game\s+\d+$", label):
                continue
            href = a.get("href")
            print("href", href)
            if not href:
                continue
            urls.append(urljoin(GOL_URL, href))

        # dédoublonne en gardant l'ordre
        seen: set[str] = set()
        out: list[str] = []
        print("urls", urls)
        for u in urls:
            if u not in seen:
                seen.add(u)
                out.append(u)
        print("out", out)
        return out

    def _parse_completestats_table(self, soup: BeautifulSoup) -> dict | None:
        """
        Retourne {"picks": [...]} ou None.
        Chaque pick : champion, player, role, stats (dict label -> valeur brute).
        Les structures intermédiaires (colonnes + lignes du tableau) ne sont pas exposées.
        """
        table = soup.select_one("table.completestats")
        if not table:
            return None
        thead = table.find("thead")
        if not thead:
            return None
        # Première ligne du thead : th vides / images champions
        header_row = thead.find("tr")
        champions: list[str] = []
        if header_row:
            for th in header_row.find_all("th")[1:]:  # skip 1ère colonne
                img = th.find("img")
                if img and img.get("alt"):
                    champions.append(img["alt"].strip())
                else:
                    champions.append(th.get_text(strip=True))
        n = len(champions)
        if n == 0:
            return None
        # Lignes du "corps" : souvent sans <tbody> dans le HTML source
        rows: dict[str, list[str]] = {}
        for tr in table.find_all("tr"):
            if tr.find_parent("thead"):
                continue
            tds = tr.find_all("td")
            if not tds:
                continue
            label = tds[0].get_text(" ", strip=True)
            values = [td.get_text(" ", strip=True) for td in tds[1:]]
            if len(values) != n:
                # table partielle ou layout différent — on garde quand même si plus court
                if len(values) < n:
                    values = values + [""] * (n - len(values))
                else:
                    values = values[:n]
            rows[label] = values
        picks: list[dict] = []
        for i in range(n):
            pr = rows.get("Player", [])
            rr = rows.get("Role", [])
            player = pr[i] if i < len(pr) else ""
            role = rr[i] if i < len(rr) else ""
            stats = {
                label: vals[i]
                for label, vals in rows.items()
                if label not in ("Player", "Role") and i < len(vals)
            }
            picks.append(
                {
                    "champion": champions[i],
                    "player": player,
                    "role": role,
                    "stats": stats,
                }
            )
        return {"picks": picks}


    def scrape_all_game_tables(self, start_url: str) -> list[dict]:
        """
        start_url : n'importe quelle page du match qui contient #gameMenuToggler
        (ex: URL 'Game 1' page-game).
        """
        session = requests.Session()
        session.trust_env = False

        first = self._fetch_soup(session, start_url)
        game_urls = self._discover_game_page_urls(first, start_url)
        if not game_urls:
            raise RuntimeError("Aucune URL Game N trouvée dans #gameMenuToggler")

        games_ids = self.extract_game_ids(game_urls)

        results: list[dict] = []
        for game_id in games_ids:
            url = f"https://gol.gg/game/stats/{game_id}/page-fullstats/"
            soup = self._fetch_soup(session, url)
            parsed = self._parse_completestats_table(soup)
            results.append(
                {
                    "url": url,
                    "game_id": game_id,
                    "table": parsed,
                }
            )
        return results

    def save_data_to_model(self, gol_game: GolGame, game_id: int, pick: dict) -> None:
        stats = pick.get("stats") or {}
        payload = {
            "gol_game": gol_game,
            "game_id": game_id,
            "champion": pick.get("champion") or "",
            "player": pick.get("player") or "",
            "role": pick.get("role") or "",
        }
        for json_key, model_field in STAT_MAP.items():
            raw = stats.get(json_key)
            # adapte selon tes types de champs
            if model_field in {"kda", "csm", "gold_pct", "vspm", "wpm", "vwpm", "wcpm", "vs_pct", "dmg_pct", "ka_per_minute", "kp_pct"}:
                payload[model_field] = to_decimal(raw, field=model_field)
            elif model_field in {"gd_at_15", "csd_at_15", "xpd_at_15", "lvld_at_15"}:
                payload[model_field] = to_int(raw, field=model_field, empty_as_zero=True)  # signé
            else:
                payload[model_field] = to_int(raw, field=model_field, empty_as_zero=True)
        GameFullStats.objects.update_or_create(
            gol_game=gol_game,
            game_id=game_id,
            champion=payload["champion"],
            player=payload["player"],
            defaults=payload,
        )

    def add_arguments(self, parser):
        parser.add_argument("game_id", type=int, help="The ID of the game to scrape.")

    def handle(self, *args, **options):
        match_id = options["game_id"]
        print("match_id", match_id)
        START_URL = f"https://gol.gg/game/stats/{match_id}/page-fullstats/"
        results = self.scrape_all_game_tables(START_URL)
        for game in results:
            game_id = game["game_id"]
            gol_game = GolGame.objects.get(match_id=game_id)  # ou match principal, selon ton modèle
            picks = (game.get("table") or {}).get("picks", [])
            for pick in picks:
                self.save_data_to_model(gol_game, game_id, pick)


