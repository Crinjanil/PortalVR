from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum
from .models import (
    Game,
    Genre,
    Booking,
    TimeSlot,
    Client,
    Package,
    User,
    LoyaltyTransaction,
)
from .forms import RegistrationForm, LoginForm, BookingForm, AdminBookingForm
import datetime


def index_view(request):
    popular_games = Game.objects.filter(is_popular=True)[:5]
    return render(
        request,
        "main/index.html",
        {
            "popular_games": popular_games,
            "page_title": "О нас",
        },
    )


def services_view(request):
    packages = Package.objects.all()
    return render(
        request,
        "main/services.html",
        {
            "packages": packages,
            "page_title": "Услуги",
        },
    )


def games_view(request):
    games = Game.objects.prefetch_related("genres").all()
    genres = Genre.objects.all()

    genre_slug = request.GET.get("genre")
    search = request.GET.get("search", "").strip()

    if genre_slug:
        games = games.filter(genres__slug=genre_slug)
    if search:
        games = games.filter(title__icontains=search)

    return render(
        request,
        "main/games.html",
        {
            "games": games.distinct(),
            "genres": genres,
            "current_genre": genre_slug,
            "search_query": search,
            "page_title": "Игры",
        },
    )


def contact_view(request):
    return render(
        request,
        "main/contact.html",
        {
            "page_title": "Где нас найти?",
        },
    )


def _get_or_create_timeslot(date, start_time_str):
    """Получить или создать временной слот"""
    hour = int(start_time_str.split(":")[0])
    start_time = datetime.time(hour, 0)
    end_time = datetime.time(hour + 1, 0)
    slot, _ = TimeSlot.objects.get_or_create(
        date=date, start_time=start_time, defaults={"end_time": end_time}
    )
    return slot


def _check_availability(
    zone, time_slot, num_players, package=None, exclude_booking_id=None
):
    """Проверка доступности мест"""
    errors = []
    date = time_slot.date

    if zone == "arena":
        # Проверяем нет ли пакетной брони на этот слот
        package_bookings = Booking.objects.filter(
            zone="package",
            status="active",
            time_slot__date=date,
        ).exclude(pk=exclude_booking_id)

        for pb in package_bookings:
            pkg_start = pb.time_slot.start_time
            pkg_end = pb.end_time_slot
            if time_slot.start_time >= pkg_start and time_slot.start_time < pkg_end:
                errors.append("Арена полностью забронирована пакетом на это время")
                return errors

        # Считаем занятые места
        arena_bookings = Booking.objects.filter(
            zone="arena",
            status="active",
            time_slot=time_slot,
        ).exclude(pk=exclude_booking_id)
        taken = arena_bookings.aggregate(total=Sum("num_players"))["total"] or 0

        if taken + num_players > 10:
            errors.append(f"Недостаточно мест на арене. Свободно: {10 - taken}")

    elif zone == "redroom":
        redroom_bookings = Booking.objects.filter(
            zone="redroom",
            status="active",
            time_slot=time_slot,
        ).exclude(pk=exclude_booking_id)
        taken = redroom_bookings.aggregate(total=Sum("num_players"))["total"] or 0

        if taken + num_players > 3:
            errors.append(f"Недостаточно мест в RED Room. Свободно: {3 - taken}")

    elif zone == "package":
        if not package:
            errors.append("Выберите пакет")
            return errors

        # Проверяем все слоты на длительность пакета
        start_hour = time_slot.start_time.hour
        for h in range(package.duration_hours):
            check_time = datetime.time(start_hour + h, 0)
            check_slot_qs = TimeSlot.objects.filter(date=date, start_time=check_time)
            if check_slot_qs.exists():
                check_slot = check_slot_qs.first()
            else:
                check_slot = TimeSlot(
                    date=date,
                    start_time=check_time,
                    end_time=datetime.time(start_hour + h + 1, 0),
                )

            # Нет ли других броней арены
            arena_bookings = Booking.objects.filter(
                zone__in=["arena", "package"],
                status="active",
                time_slot__date=date,
                time_slot__start_time=check_time,
            ).exclude(pk=exclude_booking_id)

            if arena_bookings.exists():
                errors.append(f'Арена занята в {check_time.strftime("%H:%M")}')

        # Проверяем что пакет не выходит за рабочее время
        if start_hour + package.duration_hours > 23:
            errors.append("Пакет выходит за рабочее время (до 23:00)")

    return errors


def booking_list_view(request):
    today = timezone.localtime(timezone.now()).date()
    date_str = request.GET.get("date", "")

    if date_str:
        try:
            selected_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    bookings = Booking.objects.filter(
        time_slot__date=selected_date, status="active"
    ).select_related("client", "time_slot", "package", "game")

    # Формируем расписание
    schedule_arena = {}
    schedule_redroom = {}

    for h in range(10, 23):
        t = datetime.time(h, 0)
        time_label = f"{h:02d}:00"

        arena_bookings = bookings.filter(
            zone__in=["arena", "package"], time_slot__start_time=t
        )
        # Для пакетов — проверяем покрытие
        package_bookings = Booking.objects.filter(
            zone="package",
            status="active",
            time_slot__date=selected_date,
        )
        is_package_time = False
        for pb in package_bookings:
            pkg_start = pb.time_slot.start_time.hour
            pkg_end = pkg_start + (pb.package.duration_hours if pb.package else 1)
            if pkg_start <= h < pkg_end:
                is_package_time = True
                arena_bookings = arena_bookings | Booking.objects.filter(pk=pb.pk)
                break

        arena_taken = arena_bookings.aggregate(total=Sum("num_players"))["total"] or 0

        redroom_bookings = bookings.filter(zone="redroom", time_slot__start_time=t)
        redroom_taken = (
            redroom_bookings.aggregate(total=Sum("num_players"))["total"] or 0
        )

        schedule_arena[time_label] = {
            "bookings": arena_bookings.distinct(),
            "taken": min(arena_taken, 10),
            "free": max(0, 10 - arena_taken),
            "is_package": is_package_time,
        }
        schedule_redroom[time_label] = {
            "bookings": redroom_bookings,
            "taken": min(redroom_taken, 3),
            "free": max(0, 3 - redroom_taken),
        }

    # Даты для навигации
    dates = [today + datetime.timedelta(days=i) for i in range(14)]

    return render(
        request,
        "main/booking.html",
        {
            "schedule_arena": schedule_arena,
            "schedule_redroom": schedule_redroom,
            "selected_date": selected_date,
            "dates": dates,
            "today": today,
            "page_title": "Бронирование",
        },
    )


@login_required
def booking_create_view(request):
    is_admin = request.user.is_staff

    if request.method == "POST":
        form = AdminBookingForm(request.POST) if is_admin else BookingForm(request.POST)

        if form.is_valid():
            zone = form.cleaned_data["zone"]
            date = form.cleaned_data["date"]
            time_str = form.cleaned_data["time_slot"]
            num_players = form.cleaned_data["num_players"]
            package = form.cleaned_data.get("package")
            game = form.cleaned_data.get("game")
            notes = form.cleaned_data.get("notes", "")

            # Валидация количества игроков
            if zone == "arena" and num_players > 10:
                messages.error(request, "Максимум 10 игроков на арене")
                return render(
                    request,
                    "main/booking_create.html",
                    {"form": form, "is_admin": is_admin, "page_title": "Создать бронь"},
                )
            if zone == "redroom" and num_players > 3:
                messages.error(request, "Максимум 3 игрока в RED Room")
                return render(
                    request,
                    "main/booking_create.html",
                    {"form": form, "is_admin": is_admin, "page_title": "Создать бронь"},
                )

            time_slot = _get_or_create_timeslot(date, time_str)

            # Проверка доступности
            errors = _check_availability(zone, time_slot, num_players, package)
            if errors:
                for err in errors:
                    messages.error(request, err)
                return render(
                    request,
                    "main/booking_create.html",
                    {"form": form, "is_admin": is_admin, "page_title": "Создать бронь"},
                )

            # Получаем/создаём клиента
            if is_admin:
                client_name = form.cleaned_data["client_name"]
                client_phone = form.cleaned_data["client_phone"]
                client, created = Client.objects.get_or_create(
                    phone=client_phone, defaults={"name": client_name}
                )
                if not created:
                    client.name = client_name
                    client.save()
                # Связываем с пользователем если есть
                try:
                    user = User.objects.get(phone=client_phone)
                    client.user = user
                    client.save()
                except User.DoesNotExist:
                    pass
            else:
                client, _ = Client.objects.get_or_create(
                    phone=request.user.phone,
                    defaults={"name": request.user.name, "user": request.user},
                )
                if not client.user:
                    client.user = request.user
                    client.save()

            # Для пакетов создаём слоты на всю длительность
            if zone == "package" and package:
                start_hour = time_slot.start_time.hour
                for h in range(package.duration_hours):
                    slot = _get_or_create_timeslot(date, f"{start_hour + h:02d}:00")
                    if h == 0:
                        booking = Booking.objects.create(
                            zone=zone,
                            client=client,
                            created_by_admin=is_admin,
                            time_slot=slot,
                            num_players=num_players,
                            package=package,
                            game=game,
                            notes=notes,
                        )
                    # Остальные слоты покрываются через end_time_slot
            else:
                booking = Booking.objects.create(
                    zone=zone,
                    client=client,
                    created_by_admin=is_admin,
                    time_slot=time_slot,
                    num_players=num_players,
                    game=game,
                    notes=notes,
                )

            # Начисляем баллы лояльности
            if client.user:
                points = booking.loyalty_points_earned
                client.user.loyalty_points += points
                client.user.save()
                LoyaltyTransaction.objects.create(
                    user=client.user,
                    booking=booking,
                    transaction_type="earn",
                    points=points,
                    description=f"Бронирование {booking.get_zone_display()}",
                )

            client.total_visits += 1
            client.save()

            messages.success(request, "Бронирование создано успешно!")
            return redirect("main:booking_list")
    else:
        form = AdminBookingForm() if is_admin else BookingForm()

    return render(
        request,
        "main/booking_create.html",
        {
            "form": form,
            "is_admin": is_admin,
            "page_title": "Создать бронь",
        },
    )


@login_required
def booking_cancel_view(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    # Пользователь может отменить только свою бронь
    if not request.user.is_staff:
        if (
            not hasattr(request.user, "client_profile")
            or booking.client != request.user.client_profile
        ):
            messages.error(request, "Вы можете отменять только свои брони")
            return redirect("main:booking_list")

    booking.status = "cancelled"
    booking.save()

    # Списываем баллы
    if booking.client.user:
        points = booking.loyalty_points_earned
        booking.client.user.loyalty_points = max(
            0, booking.client.user.loyalty_points - points
        )
        booking.client.user.save()
        LoyaltyTransaction.objects.create(
            user=booking.client.user,
            booking=booking,
            transaction_type="spend",
            points=-points,
            description=f"Отмена бронирования #{booking.pk}",
        )

    messages.success(request, "Бронирование отменено")
    return redirect("main:booking_list")


@login_required
def booking_edit_view(request, pk):
    if not request.user.is_staff:
        messages.error(request, "Только администратор может редактировать брони")
        return redirect("main:booking_list")

    booking = get_object_or_404(Booking, pk=pk)

    if request.method == "POST":
        form = AdminBookingForm(request.POST)
        if form.is_valid():
            zone = form.cleaned_data["zone"]
            date = form.cleaned_data["date"]
            time_str = form.cleaned_data["time_slot"]
            num_players = form.cleaned_data["num_players"]
            package = form.cleaned_data.get("package")
            game = form.cleaned_data.get("game")
            notes = form.cleaned_data.get("notes", "")
            client_name = form.cleaned_data["client_name"]
            client_phone = form.cleaned_data["client_phone"]

            time_slot = _get_or_create_timeslot(date, time_str)

            errors = _check_availability(
                zone, time_slot, num_players, package, exclude_booking_id=booking.pk
            )
            if errors:
                for err in errors:
                    messages.error(request, err)
                return render(
                    request,
                    "main/booking_create.html",
                    {
                        "form": form,
                        "is_admin": True,
                        "editing": True,
                        "booking": booking,
                        "page_title": "Редактировать бронь",
                    },
                )

            client = booking.client
            client.name = client_name
            client.phone = client_phone
            client.save()

            booking.zone = zone
            booking.time_slot = time_slot
            booking.num_players = num_players
            booking.package = package
            booking.game = game
            booking.notes = notes
            booking.save()

            messages.success(request, "Бронирование обновлено")
            return redirect("main:booking_list")
    else:
        initial = {
            "zone": booking.zone,
            "date": booking.time_slot.date,
            "time_slot": booking.time_slot.start_time.strftime("%H:%M"),
            "num_players": booking.num_players,
            "package": booking.package,
            "game": booking.game,
            "notes": booking.notes,
            "client_name": booking.client.name,
            "client_phone": booking.client.phone,
        }
        form = AdminBookingForm(initial=initial)

    return render(
        request,
        "main/booking_create.html",
        {
            "form": form,
            "is_admin": True,
            "editing": True,
            "booking": booking,
            "page_title": "Редактировать бронь",
        },
    )


@login_required
def profile_view(request):
    user = request.user
    client = getattr(user, "client_profile", None)

    bookings = []
    if client:
        bookings = (
            Booking.objects.filter(client=client)
            .select_related("time_slot", "package", "game")
            .order_by("-time_slot__date")
        )

    transactions = LoyaltyTransaction.objects.filter(user=user)[:20]

    return render(
        request,
        "main/profile.html",
        {
            "profile_user": user,
            "client": client,
            "bookings": bookings,
            "transactions": transactions,
            "page_title": "Мой профиль",
        },
    )


def profile_detail_view(request, pk):
    """Администратор может смотреть профили других пользователей"""
    if not request.user.is_staff:
        messages.error(request, "Доступ запрещён")
        return redirect("main:index")

    profile_user = get_object_or_404(User, pk=pk)
    client = getattr(profile_user, "client_profile", None)

    bookings = []
    if client:
        bookings = (
            Booking.objects.filter(client=client)
            .select_related("time_slot", "package", "game")
            .order_by("-time_slot__date")
        )

    transactions = LoyaltyTransaction.objects.filter(user=profile_user)[:20]

    return render(
        request,
        "main/profile.html",
        {
            "profile_user": profile_user,
            "client": client,
            "bookings": bookings,
            "transactions": transactions,
            "page_title": f"Профиль: {profile_user.name}",
        },
    )


def register_view(request):
    if request.user.is_authenticated:
        return redirect("main:index")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                phone=form.cleaned_data["phone"],
                name=form.cleaned_data["name"],
                password=form.cleaned_data["password"],
            )
            # Бонус за регистрацию
            user.loyalty_points = 50
            user.save()
            LoyaltyTransaction.objects.create(
                user=user,
                transaction_type="bonus",
                points=50,
                description="Бонус за регистрацию",
            )

            # Связываем с существующим клиентом если есть
            try:
                client = Client.objects.get(phone=user.phone)
                client.user = user
                client.name = user.name
                client.save()
            except Client.DoesNotExist:
                pass

            login(request, user, backend="main.backends.PhoneBackend")
            messages.success(
                request,
                f"Добро пожаловать, {user.name}! Вам начислено 50 бонусных баллов!",
            )
            return redirect("main:index")
        else:
            # AJAX валидация
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                errors = {}
                for field, errs in form.errors.items():
                    errors[field] = [str(e) for e in errs]
                return JsonResponse({"errors": errors}, status=400)
    else:
        form = RegistrationForm()

    return render(
        request,
        "main/register.html",
        {
            "form": form,
            "page_title": "Регистрация",
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect("main:index")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data["phone"]
            password = form.cleaned_data["password"]
            user = authenticate(request, phone=phone, password=password)
            if user:
                login(request, user, backend="main.backends.PhoneBackend")
                messages.success(request, f"С возвращением, {user.name}!")
                next_url = request.GET.get("next", "main:index")
                return redirect(next_url)
            else:
                messages.error(request, "Неверный номер телефона или пароль")
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse(
                        {"errors": {"__all__": ["Неверный номер телефона или пароль"]}},
                        status=400,
                    )
    else:
        form = LoginForm()

    return render(
        request,
        "main/login.html",
        {
            "form": form,
            "page_title": "Вход",
        },
    )


def logout_view(request):
    logout(request)
    messages.info(request, "Вы вышли из системы")
    return redirect("main:index")
