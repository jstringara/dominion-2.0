from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('tavola_elo', views.elo_table, name='elo_table'),
    path('nuovo_torneo', views.new_tournament, name='new_tournament'),
    path('torneo/<int:id>', views.modify_tournament, name='modify_tournament'),
    path('gestici_tornei', views.manage_tournaments, name='manage_tournaments'),
    path('classifica', views.leaderboard, name='leaderboard'),
    path('variazioni', views.variations, name='variations'),
    path('albo', views.album, name='album'),
    path('nuovo_albo', views.new_album, name='new_album'),
]
