from django.urls import path
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from . import views

urlpatterns = [
    path(
        "password_change/",
        PasswordChangeView.as_view(
            template_name="registration/change_password_form.html"
        ),
        name="password_change",
    ),  # devo overridarle così se no non funziona bene l'admin
    path(
        "password_change/done/",
        PasswordChangeDoneView.as_view(
            template_name="registration/change_password_done.html"
        ),
        name="password_change_done",
    ),
    path("register", views.register, name="register"),
    path("profile", views.profile, name="profile"),
    path("username_change", views.username_change, name="username_change"),
]
