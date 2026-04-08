from django.shortcuts import render

from .models import GolGame

def gol_home_games(request):
    total_count = GolGame.objects.count()
    games = GolGame.objects.all()[:200]
    return render(request, "scraper/gol_home_games.html",
        {
            "games": games,
            "total_count": total_count,
        }
    )
