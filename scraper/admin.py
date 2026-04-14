from django.contrib import admin

from .models import GameFullStats, GolGame


@admin.register(GolGame)
class GolGameAdmin(admin.ModelAdmin):
    list_display = ("match_date", "match_name", "tournament", "match_id", "scraped_at")
    search_fields = ("match_name", "tournament", "match_id")
    list_filter = ("match_date", "tournament")


@admin.register(GameFullStats)
class GameFullStatsAdmin(admin.ModelAdmin):
    list_display = (
        "gol_game",
        "game_id",
        "champion",
        "player",
        "role",
        "level",
        "kills",
        "deaths",
        "assists",
        "kda",
    )
    search_fields = (
        "gol_game__match_id",
        "gol_game__match_name",
        "gol_game__tournament",
        "champion",
        "player",
        "role",
    )
    list_filter = ("gol_game__match_date", "gol_game__tournament")
