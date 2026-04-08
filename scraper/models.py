from django.db import models
from django.utils import timezone

class GolGame(models.Model):
    source_url = models.URLField(max_length=2048)

    game_id = models.PositiveIntegerField(unique=True)
    game_date = models.DateField()
    game_name = models.CharField(max_length=300)
    tournament = models.CharField(max_length=200)

    blue_champions = models.JSONField(default=list)
    red_champions = models.JSONField(default=list)

    raw = models.JSONField(default=dict)
    scraped_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-game_date", "-game_id"]

    @property
    def match_url(self) -> str:
        return f"https://gol.gg/game/stats/{self.game_id}/page-game/"

    def __str__(self) -> str:
        return f"{self.game_date} — {self.game_name}"
