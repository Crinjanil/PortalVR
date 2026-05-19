from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import api_views

router = DefaultRouter()
router.register(r"games", api_views.GameViewSet)
router.register(r"genres", api_views.GenreViewSet)
router.register(r"packages", api_views.PackageViewSet)
router.register(r"bookings", api_views.BookingViewSet, basename="booking")

urlpatterns = [
    path("", include(router.urls)),
    path("availability/", api_views.availability_view, name="api-availability"),
    path("profile/", api_views.my_profile_view, name="api-profile"),
]
