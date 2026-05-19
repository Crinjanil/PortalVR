from rest_framework import serializers
from .models import Game, Genre, Booking, Package, TimeSlot, Client, User


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name", "slug"]


class GameSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)

    class Meta:
        model = Game
        fields = [
            "id",
            "title",
            "description",
            "short_description",
            "image",
            "genres",
            "zone",
            "min_players",
            "max_players",
            "is_popular",
        ]


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "duration_hours",
            "price",
            "description",
            "includes_dining",
        ]


class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ["id", "date", "start_time", "end_time", "is_past"]


class ClientPublicSerializer(serializers.ModelSerializer):
    """Для обычных пользователей — только имя"""

    class Meta:
        model = Client
        fields = ["name"]


class ClientAdminSerializer(serializers.ModelSerializer):
    """Для администратора — имя и телефон"""

    class Meta:
        model = Client
        fields = ["id", "name", "phone", "total_visits"]


class BookingSerializer(serializers.ModelSerializer):
    time_slot = TimeSlotSerializer(read_only=True)
    package = PackageSerializer(read_only=True)
    game = GameSerializer(read_only=True)
    client = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id",
            "zone",
            "client",
            "time_slot",
            "num_players",
            "package",
            "game",
            "status",
            "loyalty_points_earned",
            "created_at",
        ]

    def get_client(self, obj):
        request = self.context.get("request")
        if request and request.user.is_staff:
            return ClientAdminSerializer(obj.client).data
        return ClientPublicSerializer(obj.client).data


class BookingCreateSerializer(serializers.Serializer):
    zone = serializers.ChoiceField(choices=["arena", "redroom", "package"])
    date = serializers.DateField()
    start_time = serializers.CharField(max_length=5)
    num_players = serializers.IntegerField(min_value=1, max_value=10)
    package_id = serializers.IntegerField(required=False, allow_null=True)
    game_id = serializers.IntegerField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    # Для администратора
    client_name = serializers.CharField(required=False, max_length=100)
    client_phone = serializers.CharField(required=False, max_length=12)


class UserProfileSerializer(serializers.ModelSerializer):
    loyalty_level = serializers.ReadOnlyField()
    discount_percent = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "phone",
            "name",
            "loyalty_points",
            "loyalty_level",
            "discount_percent",
            "date_joined",
        ]
