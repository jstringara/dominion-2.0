from django.urls import path
from . import views

urlpatterns = [
    path('register', views.register, name='register'),
    path('profile', views.profile, name='profile'),
    path('username_change', views.username_change, name='username_change')
]
