from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('elo_table', views.elo_table, name='elo_table'),
    path('new_tournament', views.new_tournament, name='new_tournament'),
    path('tournament/<int:id>', views.modify_tournament, name='modify_tournament'),
    path('manage_tournaments', views.manage_tournaments, name='manage_tournaments'),
]
