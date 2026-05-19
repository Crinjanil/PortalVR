from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("", views.index_view, name="index"),
    path("services/", views.services_view, name="services"),
    path("games/", views.games_view, name="games"),
    path("contact/", views.contact_view, name="contact"),
    path("booking/", views.booking_list_view, name="booking_list"),
    path("booking/create/", views.booking_create_view, name="booking_create"),
    path("booking/<int:pk>/cancel/", views.booking_cancel_view, name="booking_cancel"),
    path("booking/<int:pk>/edit/", views.booking_edit_view, name="booking_edit"),
    path("profile/", views.profile_view, name="profile"),
    path("profile/<int:pk>/", views.profile_detail_view, name="profile_detail"),
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
]
