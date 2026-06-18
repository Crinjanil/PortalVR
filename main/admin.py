from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    Client,
    Genre,
    Game,
    Package,
    TimeSlot,
    Booking,
    LoyaltyTransaction,
    Review,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "phone",
        "name",
        "loyalty_points",
        "loyalty_level",
        "is_staff",
        "is_active",
        "date_joined",
    )
    list_filter = ("is_staff", "is_active", "date_joined")
    search_fields = ("phone", "name")
    ordering = ("-date_joined",)
    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        ("Персональные данные", {"fields": ("name", "loyalty_points")}),
        (
            "Права",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "phone",
                    "name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    readonly_fields = ("date_joined", "last_login")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "user", "total_visits", "created_at")
    list_filter = ("created_at",)
    search_fields = ("name", "phone")
    raw_id_fields = ("user",)
    readonly_fields = ("created_at",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "zone",
        "min_players",
        "max_players",
        "is_popular",
        "created_at",
    )
    list_filter = ("zone", "is_popular", "genres")
    search_fields = ("title", "description")
    filter_horizontal = ("genres",)
    list_editable = ("is_popular",)
    readonly_fields = ("created_at",)


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_hours", "price", "includes_dining")
    list_filter = ("includes_dining",)


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ("date", "start_time", "end_time", "is_past")
    list_filter = ("date",)
    ordering = ("date", "start_time")
    date_hierarchy = "date"


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "zone",
        "client",
        "time_slot",
        "num_players",
        "package",
        "game",
        "status",
        "loyalty_points_earned",
        "created_by_admin",
        "created_at",
    )
    list_filter = ("zone", "status", "created_by_admin", "time_slot__date")
    search_fields = ("client__name", "client__phone", "notes")
    raw_id_fields = ("client", "time_slot")
    list_editable = ("status",)
    readonly_fields = ("created_at", "updated_at", "loyalty_points_earned")
    fieldsets = (
        ("Основное", {"fields": ("zone", "client", "time_slot", "num_players")}),
        ("Детали", {"fields": ("package", "game", "notes")}),
        ("Статус", {"fields": ("status", "created_by_admin", "loyalty_points_earned")}),
        ("Даты", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "transaction_type",
        "points",
        "description",
        "booking",
        "created_at",
    )
    list_filter = ("transaction_type", "created_at")
    search_fields = ("user__name", "description")
    raw_id_fields = ("user", "booking")
    readonly_fields = ("created_at",)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("name", "rating", "is_active", "created_at")
    list_filter = ("rating", "is_active", "created_at")
    search_fields = ("name", "text")
    readonly_fields = ("created_at",)
