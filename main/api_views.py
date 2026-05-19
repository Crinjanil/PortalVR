from rest_framework import viewsets, permissions, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.db.models import Q, Sum
from .models import Game, Genre, Booking, Package, TimeSlot, Client, User
from .serializers import (
    GameSerializer,
    GenreSerializer,
    BookingSerializer,
    PackageSerializer,
    BookingCreateSerializer,
    UserProfileSerializer,
)
from .views import _get_or_create_timeslot, _check_availability
import datetime


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Game.objects.prefetch_related("genres").all()
    serializer_class = GameSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = super().get_queryset()
        genre = self.request.query_params.get("genre")
        search = self.request.query_params.get("search")
        popular = self.request.query_params.get("popular")

        if genre:
            qs = qs.filter(genres__slug=genre)
        if search:
            qs = qs.filter(title__icontains=search)
        if popular:
            qs = qs.filter(is_popular=True)
        return qs.distinct()


class GenreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.AllowAny]


class PackageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer
    permission_classes = [permissions.AllowAny]


class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = Booking.objects.select_related("client", "time_slot", "package", "game")
        date = self.request.query_params.get("date")
        zone = self.request.query_params.get("zone")
        if date:
            qs = qs.filter(time_slot__date=date)
        if zone:
            qs = qs.filter(zone=zone)
        return qs.filter(status="active")

    def create(self, request, *args, **kwargs):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        zone = data["zone"]
        date = data["date"]
        time_str = data["start_time"]
        num_players = data["num_players"]
        package_id = data.get("package_id")
        game_id = data.get("game_id")
        notes = data.get("notes", "")

        package = None
        game = None
        if package_id:
            try:
                package = Package.objects.get(pk=package_id)
            except Package.DoesNotExist:
                return Response({"error": "Пакет не найден"}, status=400)
        if game_id:
            try:
                game = Game.objects.get(pk=game_id)
            except Game.DoesNotExist:
                return Response({"error": "Игра не найдена"}, status=400)

        time_slot = _get_or_create_timeslot(date, time_str)
        errors = _check_availability(zone, time_slot, num_players, package)
        if errors:
            return Response({"errors": errors}, status=400)

        if (
            request.user.is_staff
            and data.get("client_name")
            and data.get("client_phone")
        ):
            client, _ = Client.objects.get_or_create(
                phone=data["client_phone"], defaults={"name": data["client_name"]}
            )
        else:
            client, _ = Client.objects.get_or_create(
                phone=request.user.phone,
                defaults={"name": request.user.name, "user": request.user},
            )

        booking = Booking.objects.create(
            zone=zone,
            client=client,
            created_by_admin=request.user.is_staff,
            time_slot=time_slot,
            num_players=num_players,
            package=package,
            game=game,
            notes=notes,
        )

        return Response(
            BookingSerializer(booking, context={"request": request}).data, status=201
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if not request.user.is_staff:
            if (
                not hasattr(request.user, "client_profile")
                or booking.client != request.user.client_profile
            ):
                return Response({"error": "Нельзя отменить чужую бронь"}, status=403)
        booking.status = "cancelled"
        booking.save()
        return Response({"status": "cancelled"})


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def availability_view(request):
    """API для проверки доступности мест"""
    date_str = request.query_params.get("date")
    zone = request.query_params.get("zone", "arena")

    if not date_str:
        return Response({"error": "Укажите дату"}, status=400)

    try:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "Неверный формат даты"}, status=400)

    result = {}
    max_capacity = 10 if zone in ["arena", "package"] else 3

    for h in range(10, 23):
        time_label = f"{h:02d}:00"
        t = datetime.time(h, 0)

        if zone in ["arena", "package"]:
            # Проверяем пакетные брони
            package_bookings = Booking.objects.filter(
                zone="package",
                status="active",
                time_slot__date=date,
            )
            is_blocked = False
            for pb in package_bookings:
                pkg_start = pb.time_slot.start_time.hour
                pkg_end = pkg_start + (pb.package.duration_hours if pb.package else 1)
                if pkg_start <= h < pkg_end:
                    is_blocked = True
                    break

            if is_blocked:
                result[time_label] = {"free": 0, "taken": 10, "blocked": True}
                continue

            taken = (
                Booking.objects.filter(
                    zone="arena",
                    status="active",
                    time_slot__date=date,
                    time_slot__start_time=t,
                ).aggregate(total=Sum("num_players"))["total"]
                or 0
            )
        else:
            taken = (
                Booking.objects.filter(
                    zone="redroom",
                    status="active",
                    time_slot__date=date,
                    time_slot__start_time=t,
                ).aggregate(total=Sum("num_players"))["total"]
                or 0
            )

        result[time_label] = {
            "free": max(0, max_capacity - taken),
            "taken": min(taken, max_capacity),
            "blocked": False,
        }

    return Response(result)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def my_profile_view(request):
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)
