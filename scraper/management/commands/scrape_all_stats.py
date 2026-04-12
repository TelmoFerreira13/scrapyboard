from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

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

class Command(BaseCommand):
    help = "Scrape all stats from a game page."


    def _fetch_soup(self, session: requests.Session, url: str) -> BeautifulSoup:
        resp = session.get(url, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    def extract_match_ids(self, game_urls: list[str]) -> list[int]:
        match_ids: list[int] = []
        for url in game_urls:
            m = re.search(r"/stats/(\d+)/", url)
            if m:
                match_ids.append(int(m.group(1)))
        match_ids = list(set(match_ids))
        print("match_ids", match_ids)
        return match_ids

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
        Retourne un dict:
        {
            "champions": [...],       # noms champions (thead, img alt)
            "rows": { "Kills": [...], ... },  # label de ligne -> valeurs par colonne
            "by_champion": [         # une entrée par colonne = un pick
                {
                    "champion": str,
                    "player": str,
                    "role": str,
                    "stats": { "Level": "...", "Kills": "...", ... },
                },
                ...
            ],
        }
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

        by_champion: list[dict] = []
        for i in range(n):
            player = rows["Player"][i] if "Player" in rows and i < len(rows["Player"]) else ""
            role = rows["Role"][i] if "Role" in rows and i < len(rows["Role"]) else ""
            stats = {
                label: vals[i]
                for label, vals in rows.items()
                if label not in ("Player", "Role") and i < len(vals)
            }
            by_champion.append(
                {
                    "champion": champions[i],
                    "player": player,
                    "role": role,
                    "stats": stats,
                }
            )

        return {
            "champions": champions,
            "rows": rows,
            "by_champion": by_champion,
        }

    def scrape_all_game_tables(self, start_url: str) -> list[dict]:
        """
        start_url : n'importe quelle page du match qui contient #gameMenuToggler
        (ex: URL 'Game 1' page-game).
        """
        print("start_url", start_url)
        session = requests.Session()
        session.trust_env = False
        print("ça bug pas a sessions")

        first = self._fetch_soup(session, start_url)
        print("ça bug pas a first fetch soup")
        game_urls = self._discover_game_page_urls(first, start_url)
        if not game_urls:
            raise RuntimeError("Aucune URL Game N trouvée dans #gameMenuToggler")

        match_ids = self.extract_match_ids(game_urls)

        results: list[dict] = []
        for mid in match_ids:
            url = f"https://gol.gg/game/stats/{mid}/page-fullstats/"
            soup = self._fetch_soup(session, url)
            print("url juste avant parse completestats", url)
            parsed = self._parse_completestats_table(soup)
            results.append(
                {
                    "url": url,
                    "table": parsed,
                }
            )
        return results

    def add_arguments(self, parser):
        parser.add_argument(
            "match_id",
            type=int,
            help="ID gol.gg du match (segment /stats/<id>/ dans l'URL).",
        )

    def handle(self, *args, **options):
        match_id = options["match_id"]
        START_URL = f"https://gol.gg/game/stats/{match_id}/page-fullstats/"
        for item in self.scrape_all_game_tables(START_URL):
            print("===", item["url"], "===")
            t = item["table"]
            if not t:
                print("Pas de table completestats")
                continue
            print("Champions:", t["champions"])
            print("Nb stats (lignes):", len(t["rows"]))
            if t.get("by_champion"):
                print("Ex. pick 0:", t["by_champion"][0])
            for k in list(t["rows"].keys())[:3]:
                print(k, "->", t["rows"][k][:5], "...")