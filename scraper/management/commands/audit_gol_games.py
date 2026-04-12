from django.core.management.base import BaseCommand
from django.db.models import Count, Min, Max

from scraper.models import GolGame


class Command(BaseCommand):
    help = "Rapport rapide sur les GolGame en base."

    def handle(self, *args, **options):
        total = GolGame.objects.count()
        self.stdout.write(f"TOTAL: {total}")

        dups = (
            GolGame.objects.values("match_id")
            .annotate(c=Count("id"))
            .filter(c__gt=1)
        )
        self.stdout.write(f"DUPLICATS match_id: {dups.count()}")

        self.stdout.write(f"match_name vide: {GolGame.objects.filter(match_name='').count()}")
        self.stdout.write(f"tournament vide: {GolGame.objects.filter(tournament='').count()}")

        agg = GolGame.objects.aggregate(
            dmin=Min("match_date"),
            dmax=Max("match_date"),
            gmin=Min("match_id"),
            gmax=Max("match_id"),
        )
        self.stdout.write(
            f"Dates: {agg['dmin']} .. {agg['dmax']} | match_id: {agg['gmin']} .. {agg['gmax']}"
        )

        if total:
            self.stdout.write("5 plus récents:")
            for g in GolGame.objects.order_by("-match_date", "-match_id")[:5]:
                self.stdout.write(f"  {g.match_id} {g.match_date} {g.match_name}")
