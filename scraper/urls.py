from django.urls import path

from . import views

urlpatterns = [
    path("", views.gol_home_games, name="gol_home_games"),
    path("gol/", views.gol_home_games, name="gol_home_games"),
]
