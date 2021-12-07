from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('elo_table', views.elo_table, name='elo_table'),
    path('new_tournament', views.new_tournament, name='new_tournament'),
]
