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


class GameFullStats(models.Model):
    """
    Un pick (joueur + champion) sur une game gol.gg, rattaché au match (BO) GolGame.
    Les pourcentages : valeur décimale type 12.4 (= 12.4 %), pas 0.124.
    """
    gol_game = models.ForeignKey(
        "GolGame",
        on_delete=models.CASCADE,
        related_name="game_full_stats",
    )
    game_id = models.PositiveIntegerField()
    champion = models.CharField(max_length=200)
    player = models.CharField(max_length=200)
    role = models.CharField(max_length=200)
    # --- Entiers ---
    level = models.PositiveSmallIntegerField(null=True, blank=True)
    kills = models.PositiveSmallIntegerField(null=True, blank=True)
    deaths = models.PositiveSmallIntegerField(null=True, blank=True)
    assists = models.PositiveSmallIntegerField(null=True, blank=True)
    cs = models.PositiveIntegerField(null=True, blank=True)
    cs_in_team_jungle = models.PositiveIntegerField(null=True, blank=True)
    cs_in_enemy_jungle = models.PositiveIntegerField(null=True, blank=True)
    golds = models.PositiveIntegerField(null=True, blank=True)
    gpm = models.PositiveIntegerField(null=True, blank=True)
    vision_score = models.PositiveIntegerField(null=True, blank=True)
    wards_placed = models.PositiveIntegerField(null=True, blank=True)
    wards_destroyed = models.PositiveIntegerField(null=True, blank=True)
    control_wards_purchased = models.PositiveIntegerField(null=True, blank=True)
    detector_wards_placed = models.PositiveIntegerField(null=True, blank=True)
    total_damage_to_champion = models.PositiveIntegerField(null=True, blank=True)
    physical_damage = models.PositiveIntegerField(null=True, blank=True)
    magic_damage = models.PositiveIntegerField(null=True, blank=True)
    true_damage = models.PositiveIntegerField(null=True, blank=True)
    dpm = models.PositiveIntegerField(null=True, blank=True)
    solo_kills = models.PositiveSmallIntegerField(null=True, blank=True)
    double_kills = models.PositiveSmallIntegerField(null=True, blank=True)
    triple_kills = models.PositiveSmallIntegerField(null=True, blank=True)
    quadra_kills = models.PositiveSmallIntegerField(null=True, blank=True)
    penta_kills = models.PositiveSmallIntegerField(null=True, blank=True)
    gd_at_15 = models.IntegerField(null=True, blank=True)
    csd_at_15 = models.IntegerField(null=True, blank=True)
    xpd_at_15 = models.IntegerField(null=True, blank=True)
    lvld_at_15 = models.IntegerField(null=True, blank=True)
    objectives_stolen = models.PositiveSmallIntegerField(null=True, blank=True)
    damage_dealt_to_turrets = models.PositiveIntegerField(null=True, blank=True)
    damage_dealt_to_buildings = models.PositiveIntegerField(null=True, blank=True)
    total_heal = models.PositiveIntegerField(null=True, blank=True)
    total_heals_on_teammates = models.PositiveIntegerField(null=True, blank=True)
    damage_self_mitigated = models.PositiveIntegerField(null=True, blank=True)
    total_damage_shielded_on_teammates = models.PositiveIntegerField(null=True, blank=True)
    time_ccing_others = models.PositiveIntegerField(null=True, blank=True)
    total_time_cc_dealt = models.PositiveIntegerField(null=True, blank=True)
    total_damage_taken = models.PositiveIntegerField(null=True, blank=True)
    total_time_spent_dead = models.PositiveIntegerField(null=True, blank=True)
    consumables_purchased = models.PositiveIntegerField(null=True, blank=True)
    items_purchased = models.PositiveIntegerField(null=True, blank=True)
    shutdown_bounty_collected = models.IntegerField(null=True, blank=True)
    shutdown_bounty_lost = models.IntegerField(null=True, blank=True)
    # --- Décimaux (KDA, minutes, pourcentages affichés, etc.) ---
    kda = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    csm = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    gold_pct = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    vspm = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    wpm = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    vwpm = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    wcpm = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    vs_pct = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    dmg_pct = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    ka_per_minute = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    kp_pct = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    class Meta:
        ordering = ["-gol_game_id", "-game_id", "champion"]
        indexes = [
            models.Index(fields=["gol_game", "game_id"]),
            models.Index(fields=["gol_game", "kills"]),
            models.Index(fields=["gol_game", "deaths"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["gol_game", "game_id", "champion", "player"],
                name="uniq_pick_full_stats_pick",
            ),
        ]
    def __str__(self) -> str:
        return f"{self.gol_game_id} / game {self.game_id} — {self.champion} ({self.player})"