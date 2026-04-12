from django.db import models
from django.utils import timezone

class GolGame(models.Model):
    source_url = models.URLField(max_length=2048)

    match_id = models.PositiveIntegerField(unique=True)
    match_date = models.DateField()
    match_name = models.CharField(max_length=300)
    tournament = models.CharField(max_length=200)

    blue_champions = models.JSONField(default=list)
    red_champions = models.JSONField(default=list)

    raw = models.JSONField(default=dict)
    scraped_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-match_date", "-match_id"]

    @property
    def match_url(self) -> str:
        return f"https://gol.gg/game/stats/{self.match_id}/page-game/"

    def __str__(self) -> str:
        return f"{self.match_date} — {self.match_name}"
