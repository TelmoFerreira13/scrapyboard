from django.shortcuts import render

from .models import GolGame, GameFullStats

def gol_home_games(request):
    total_count = GolGame.objects.count()
    games = GolGame.objects.all()[:200]
    return render(request, "scraper/gol_home_games.html",
        {
            "games": games,
            "total_count": total_count,
        }
    )

def full_stats_list(request):
    qs = GameFullStats.objects.select_related("gol_game").order_by("-gol_game__match_date", "-game_id")[:200]
    return render(request, "scraper/full_stats_list.html", {
        "stats": qs,
        "total_count": qs.count(),
    })