from django.contrib import admin

from .models import GolGame


@admin.register(GolGame)
class GolGameAdmin(admin.ModelAdmin):
    list_display = ("match_date", "match_name", "tournament", "match_id", "scraped_at")
    search_fields = ("match_name", "tournament", "match_id")
    list_filter = ("match_date", "tournament")
