from django.core.management.base import BaseCommand
from django.db.models import Count, Min, Max

from scraper.models import GolGame


class Command(BaseCommand):
    help = "Rapport rapide sur les GolGame en base."

    def handle(self, *args, **options):
        total = GolGame.objects.count()
        self.stdout.write(f"TOTAL: {total}")

        dups = (
            GolGame.objects.values("game_id")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
        )
        self.stdout.write(f"DUPLICATS game_id: {dups.count()}")

        self.stdout.write(f"game_name vide: {GolGame.objects.filter(game_name='').count()}")
        self.stdout.write(f"tournament vide: {GolGame.objects.filter(tournament='').count()}")

        agg = GolGame.objects.aggregate(
            dmin=Min("game_date"),
            dmax=Max("game_date"),
            gmin=Min("game_id"),
            gmax=Max("game_id"),
        )
        self.stdout.write(
            f"Dates: {agg['dmin']} .. {agg['dmax']} | game_id: {agg['gmin']} .. {agg['gmax']}"
        )

        if total:
            self.stdout.write("5 plus récents:")
            for g in GolGame.objects.order_by("-game_date", "-game_id")[:5]:
                self.stdout.write(f"  {g.game_id} {g.game_date} {g.game_name}")