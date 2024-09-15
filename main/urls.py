from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("tavola_elo", views.elo_table, name="elo_table"),
    path("nuovo_torneo", views.new_tournament, name="new_tournament"),
    path("torneo/<int:tournament_id>", views.modify_tournament, name="modify_tournament"),
    path("ultimo_torneo", views.last_tournament, name="last_tournament"),
    path("gestici_tornei", views.manage_tournaments, name="manage_tournaments"),
    path("classifica", views.leaderboard, name="leaderboard"),
    path("variazioni", views.variations, name="variations"),
    path("vinte_e_disputate", views.wins, name="wins"),
    path("percentuali", views.win_rates, name="percentages"),
    path("albo", views.album, name="album"),
    path("punteggi_attesi", views.get_expected, name="get_expected"),
    path("torneo_eliminato", views.tournament_deleted, name="tournament_deleted"),
    path(
        "get/ajax/refresh_tour/<int:tournament_id>",
        views.refresh_tour,
        name="refresh_tour",
    ),
    path(
        "post/ajax/update_tour/<int:tournament_id>",
        views.update_tour,
        name="update_tour",
    ),
    path("season_management", views.season_management, name="season_management"),
    path("create_season/", views.create_season, name="create_season"),
    path("season_action", views.season_action, name="season_action"),
    path("get/ajax/refresh_graph", views.refresh_graph, name="refresh_graph"),
    path("get/ajax/expected_scores", views.expected_ajax, name="expected_ajax"),
    path("get/ajax/win_rates/<str:kind>", views.win_rates_ajax, name="win_rates_ajax"),
]
