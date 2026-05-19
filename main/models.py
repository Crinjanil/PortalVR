from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import datetime


class UserManager(BaseUserManager):
    def create_user(self, phone, name, password=None, **extra_fields):
        if not phone:
            raise ValueError("Номер телефона обязателен")
        user = self.model(phone=phone, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(phone, name, password, **extra_fields)


phone_validator = RegexValidator(
    regex=r"^\+7\d{10}$", message="Номер телефона должен быть в формате +7XXXXXXXXXX"
)


class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(
        "Телефон", max_length=12, unique=True, validators=[phone_validator]
    )
    name = models.CharField("Имя", max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField("Дата регистрации", default=timezone.now)
    loyalty_points = models.PositiveIntegerField("Баллы лояльности", default=0)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def loyalty_level(self):
        if self.loyalty_points >= 1000:
            return "Platinum"
        elif self.loyalty_points >= 500:
            return "Gold"
        elif self.loyalty_points >= 200:
            return "Silver"
        return "Bronze"

    @property
    def discount_percent(self):
        levels = {"Bronze": 0, "Silver": 5, "Gold": 10, "Platinum": 15}
        return levels.get(self.loyalty_level, 0)


class Client(models.Model):
    """Клиент в БД — может быть не зарегистрирован"""

    name = models.CharField("Имя", max_length=100)
    phone = models.CharField("Телефон", max_length=12, validators=[phone_validator])
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="client_profile",
        verbose_name="Связанный аккаунт",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    total_visits = models.PositiveIntegerField("Всего визитов", default=0)

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

    def __str__(self):
        linked = " (зарег.)" if self.user else ""
        return f"{self.name} — {self.phone}{linked}"


class Genre(models.Model):
    name = models.CharField("Название", max_length=100, unique=True)
    slug = models.SlugField("Slug", unique=True)

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Game(models.Model):
    ZONE_CHOICES = [
        ("arena", "VR Арена"),
        ("redroom", "RED Room"),
        ("both", "Обе зоны"),
    ]
    title = models.CharField("Название", max_length=200)
    description = models.TextField("Описание")
    short_description = models.CharField("Краткое описание", max_length=300)
    image = models.ImageField("Изображение", upload_to="games/", blank=True)
    genres = models.ManyToManyField(Genre, verbose_name="Жанры", related_name="games")
    zone = models.CharField("Зона", max_length=10, choices=ZONE_CHOICES, default="both")
    min_players = models.PositiveIntegerField("Мин. игроков", default=1)
    max_players = models.PositiveIntegerField("Макс. игроков", default=10)
    is_popular = models.BooleanField("Популярная", default=False)
    created_at = models.DateTimeField("Добавлена", auto_now_add=True)

    class Meta:
        verbose_name = "Игра"
        verbose_name_plural = "Игры"
        ordering = ["-is_popular", "title"]

    def __str__(self):
        return self.title


class Package(models.Model):
    PACKAGE_CHOICES = [
        ("light", "Light — 2 часа"),
        ("standard", "Standard — 3 часа"),
        ("premium", "Premium — 4 часа"),
    ]
    name = models.CharField(
        "Название", max_length=10, choices=PACKAGE_CHOICES, unique=True
    )
    duration_hours = models.PositiveIntegerField("Длительность (часы)")
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    description = models.TextField("Описание", blank=True)
    includes_dining = models.BooleanField("Включает обеденную зону", default=True)

    class Meta:
        verbose_name = "Пакет"
        verbose_name_plural = "Пакеты"

    def __str__(self):
        return self.get_name_display()


class TimeSlot(models.Model):
    """Временные слоты для бронирования (каждый час)"""

    date = models.DateField("Дата")
    start_time = models.TimeField("Начало")
    end_time = models.TimeField("Конец")

    class Meta:
        verbose_name = "Временной слот"
        verbose_name_plural = "Временные слоты"
        unique_together = ["date", "start_time"]
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time}"

    @property
    def is_past(self):
        now = timezone.localtime(timezone.now())
        slot_dt = timezone.make_aware(
            datetime.datetime.combine(self.date, self.start_time)
        )
        return slot_dt < now


class Booking(models.Model):
    ZONE_CHOICES = [
        ("arena", "VR Арена"),
        ("redroom", "RED Room"),
        ("package", "Пакет (VR Арена)"),
    ]
    STATUS_CHOICES = [
        ("active", "Активна"),
        ("completed", "Завершена"),
        ("cancelled", "Отменена"),
    ]

    zone = models.CharField("Зона", max_length=10, choices=ZONE_CHOICES)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="bookings", verbose_name="Клиент"
    )
    created_by_admin = models.BooleanField("Создана администратором", default=False)
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name="bookings",
        verbose_name="Временной слот",
    )
    num_players = models.PositiveIntegerField("Количество игроков", default=1)
    package = models.ForeignKey(
        Package,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        verbose_name="Пакет",
    )
    game = models.ForeignKey(
        Game,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
        verbose_name="Игра",
    )
    status = models.CharField(
        "Статус", max_length=10, choices=STATUS_CHOICES, default="active"
    )
    loyalty_points_earned = models.PositiveIntegerField("Баллы за бронь", default=0)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлена", auto_now=True)
    notes = models.TextField("Заметки", blank=True)

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ["time_slot__date", "time_slot__start_time"]

    def __str__(self):
        return f"{self.get_zone_display()} — {self.client.name} — {self.time_slot}"

    def save(self, *args, **kwargs):
        # Начисляем баллы лояльности
        if not self.pk:
            if self.zone == "package" and self.package:
                self.loyalty_points_earned = int(self.package.price) // 10
            elif self.zone == "arena":
                self.loyalty_points_earned = 20 * self.num_players
            else:
                self.loyalty_points_earned = 15 * self.num_players
        super().save(*args, **kwargs)

    @property
    def end_time_slot(self):
        """Для пакетов — возвращает конечный слот"""
        if self.package:
            end = datetime.datetime.combine(
                self.time_slot.date, self.time_slot.start_time
            ) + datetime.timedelta(hours=self.package.duration_hours)
            return end.time()
        return self.time_slot.end_time


class LoyaltyTransaction(models.Model):
    """Транзакции баллов лояльности"""

    TYPE_CHOICES = [
        ("earn", "Начисление"),
        ("spend", "Списание"),
        ("bonus", "Бонус"),
    ]
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="loyalty_transactions",
        verbose_name="Пользователь",
    )
    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Бронирование",
    )
    transaction_type = models.CharField("Тип", max_length=5, choices=TYPE_CHOICES)
    points = models.IntegerField("Баллы")
    description = models.CharField("Описание", max_length=300)
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = "Транзакция лояльности"
        verbose_name_plural = "Транзакции лояльности"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.name}: {self.get_transaction_type_display()} {self.points} баллов"
