from django.contrib import admin

from .models import GolGame


@admin.register(GolGame)
class GolGameAdmin(admin.ModelAdmin):
    list_display = ("game_date", "game_name", "tournament", "game_id", "scraped_at")
    search_fields = ("game_name", "tournament", "game_id")
    list_filter = ("game_date", "tournament")
