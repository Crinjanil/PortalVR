from django.core.management.base import BaseCommand
from main.models import Genre, Game, Package, User


class Command(BaseCommand):
    help = "Заполняет БД начальными данными"

    def handle(self, *args, **options):
        # Жанры
        genres_data = [
            ("Шутер", "shooter"),
            ("Хоррор", "horror"),
            ("Приключения", "adventure"),
            ("Спорт", "sport"),
            ("Головоломка", "puzzle"),
            ("Симулятор", "simulator"),
            ("Фэнтези", "fantasy"),
            ("Sci-Fi", "sci-fi"),
            ("Кооператив", "coop"),
            ("Аркада", "arcade"),
        ]
        genres = {}
        for name, slug in genres_data:
            g, _ = Genre.objects.get_or_create(name=name, slug=slug)
            genres[slug] = g
            self.stdout.write(f"  Жанр: {name}")

        # Игры
        games_data = [
            {
                "title": "Arizona Sunshine",
                "short_description": "Зомби-шутер в жарких пустынях Аризоны",
                "description": "Сражайтесь с ордами зомби в солнечной Аризоне. Кооперативный режим до 4 игроков. Используйте разнообразное оружие и исследуйте открытый мир.",
                "zone": "arena",
                "min_players": 1,
                "max_players": 4,
                "is_popular": True,
                "genres": ["shooter", "coop", "horror"],
            },
            {
                "title": "Beat Saber",
                "short_description": "Ритм-игра с световыми мечами",
                "description": "Разрубайте блоки в такт музыке световыми мечами. Множество треков и уровней сложности. Идеальная игра для разминки!",
                "zone": "redroom",
                "min_players": 1,
                "max_players": 1,
                "is_popular": True,
                "genres": ["arcade", "sport"],
            },
            {
                "title": "Half-Life: Alyx",
                "short_description": "Легендарный VR-шутер от Valve",
                "description": "Погрузитесь в мир Half-Life как никогда раньше. Потрясающая графика, захватывающий сюжет и революционный VR-геймплей.",
                "zone": "redroom",
                "min_players": 1,
                "max_players": 1,
                "is_popular": True,
                "genres": ["shooter", "sci-fi", "adventure"],
            },
            {
                "title": "Contractors Showdown",
                "short_description": "Тактический мультиплеерный шутер",
                "description": "Командный тактический шутер с реалистичной механикой стрельбы. До 10 игроков на арене. Различные режимы игры.",
                "zone": "arena",
                "min_players": 2,
                "max_players": 10,
                "is_popular": True,
                "genres": ["shooter", "coop"],
            },
            {
                "title": "The Room VR: A Dark Matter",
                "short_description": "Мистическая головоломка в VR",
                "description": "Разгадывайте загадки в мрачной викторианской атмосфере. Каждая комната — новая тайна. Потрясающая детализация окружения.",
                "zone": "redroom",
                "min_players": 1,
                "max_players": 1,
                "is_popular": True,
                "genres": ["puzzle", "horror", "adventure"],
            },
            {
                "title": "Pavlov VR",
                "short_description": "VR-аналог Counter-Strike",
                "description": "Реалистичный мультиплеерный шутер с физикой оружия. Множество карт и режимов. Командная игра на арене.",
                "zone": "arena",
                "min_players": 2,
                "max_players": 10,
                "is_popular": False,
                "genres": ["shooter", "coop"],
            },
            {
                "title": "Superhot VR",
                "short_description": "Время движется только когда двигаетесь вы",
                "description": "Уникальная механика замедления времени. Уклоняйтесь от пуль, хватайте оружие врагов и чувствуйте себя героем боевика.",
                "zone": "redroom",
                "min_players": 1,
                "max_players": 1,
                "is_popular": False,
                "genres": ["shooter", "puzzle", "arcade"],
            },
            {
                "title": "Blade & Sorcery",
                "short_description": "Средневековый боевой симулятор",
                "description": "Физически реалистичные бои на мечах, топорах и магии. Песочница для средневековых сражений с продвинутой физикой.",
                "zone": "both",
                "min_players": 1,
                "max_players": 1,
                "is_popular": False,
                "genres": ["fantasy", "simulator", "adventure"],
            },
            {
                "title": "Phasmophobia VR",
                "short_description": "Кооперативная охота на призраков",
                "description": "Исследуйте дома с привидениями в команде до 4 человек. Используйте оборудование для обнаружения призраков. Невероятно страшно в VR!",
                "zone": "arena",
                "min_players": 1,
                "max_players": 4,
                "is_popular": False,
                "genres": ["horror", "coop", "simulator"],
            },
            {
                "title": "Eleven Table Tennis",
                "short_description": "Самый реалистичный VR настольный теннис",
                "description": "Физика мяча и ракетки воссозданы с невероятной точностью. Играйте с ИИ или другими игроками онлайн.",
                "zone": "redroom",
                "min_players": 1,
                "max_players": 2,
                "is_popular": False,
                "genres": ["sport", "simulator"],
            },
            {
                "title": "Zero Caliber VR",
                "short_description": "Военный тактический шутер",
                "description": "Кооперативная военная кампания в VR. Кастомизация оружия, тактические миссии и напряжённый геймплей.",
                "zone": "arena",
                "min_players": 1,
                "max_players": 4,
                "is_popular": False,
                "genres": ["shooter", "coop", "adventure"],
            },
            {
                "title": "Moss",
                "short_description": "Сказочное приключение с мышонком Квиллом",
                "description": "Управляйте храбрым мышонком в волшебном мире. Комбинация платформера и головоломки в уникальной VR-перспективе.",
                "zone": "redroom",
                "min_players": 1,
                "max_players": 1,
                "is_popular": False,
                "genres": ["adventure", "puzzle", "fantasy"],
            },
            {
                "title": "Population: One",
                "short_description": "VR Battle Royale",
                "description": "Королевская битва в виртуальной реальности. Стройте, летайте и стреляйте. До 6 игроков в команде.",
                "zone": "arena",
                "min_players": 1,
                "max_players": 6,
                "is_popular": False,
                "genres": ["shooter", "coop", "adventure"],
            },
            {
                "title": "Cooking Simulator VR",
                "short_description": "Станьте шеф-поваром в VR",
                "description": "Готовьте блюда в полностью интерактивной кухне. Реалистичная физика продуктов и кухонной утвари.",
                "zone": "redroom",
                "min_players": 1,
                "max_players": 1,
                "is_popular": False,
                "genres": ["simulator", "arcade"],
            },
            {
                "title": "Onward",
                "short_description": "Тактический милитари-шутер",
                "description": "Реалистичный военный симулятор с командной работой. Координация, тактика и точная стрельба — ключ к победе.",
                "zone": "arena",
                "min_players": 2,
                "max_players": 10,
                "is_popular": False,
                "genres": ["shooter", "coop", "simulator"],
            },
        ]

        for gd in games_data:
            genre_slugs = gd.pop("genres")
            game, created = Game.objects.get_or_create(title=gd["title"], defaults=gd)
            if created:
                for slug in genre_slugs:
                    if slug in genres:
                        game.genres.add(genres[slug])
                self.stdout.write(f"  Игра: {game.title}")

        # Пакеты
        packages_data = [
            {
                "name": "light",
                "duration_hours": 2,
                "price": 8000,
                "description": "Пакет Light — 2 часа полной аренды VR Арены + обеденная зона. Идеально для небольших мероприятий.",
            },
            {
                "name": "standard",
                "duration_hours": 3,
                "price": 11000,
                "description": "Пакет Standard — 3 часа полной аренды VR Арены + обеденная зона. Оптимальный выбор для дней рождений.",
            },
            {
                "name": "premium",
                "duration_hours": 4,
                "price": 14000,
                "description": "Пакет Premium — 4 часа полной аренды VR Арены + обеденная зона. Максимум впечатлений для корпоративов.",
            },
        ]
        for pd in packages_data:
            pkg, created = Package.objects.get_or_create(name=pd["name"], defaults=pd)
            if created:
                self.stdout.write(f"  Пакет: {pkg}")

        # Суперпользователь
        if not User.objects.filter(phone="+70000000000").exists():
            User.objects.create_superuser(
                phone="+70000000000", name="Администратор", password="admin123"
            )
            self.stdout.write("  Суперпользователь создан: +70000000000 / admin123")

        self.stdout.write(self.style.SUCCESS("Данные успешно загружены!"))
