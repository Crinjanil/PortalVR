from django import forms
from django.core.validators import RegexValidator
from .models import User, Booking, Client, Package, Game, TimeSlot
import re

phone_validator = RegexValidator(regex=r"^\+7\d{10}$", message="Формат: +7XXXXXXXXXX")

cyrillic_validator = RegexValidator(
    regex=r"^[а-яА-ЯёЁ\s\-]+$", message="Разрешены только кириллические символы"
)


class RegistrationForm(forms.Form):
    name = forms.CharField(
        label="Имя",
        max_length=100,
        validators=[cyrillic_validator],
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Ваше имя (кириллица)",
            }
        ),
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=12,
        validators=[phone_validator],
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "+7XXXXXXXXXX",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        min_length=6,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Минимум 6 символов",
            }
        ),
    )
    password_confirm = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Повторите пароль",
            }
        ),
    )
    agree = forms.BooleanField(
        label="Я согласен с правилами регистрации",
        widget=forms.CheckboxInput(attrs={"class": "form-checkbox"}),
    )

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if User.objects.filter(phone=phone).exists():
            raise forms.ValidationError("Этот номер уже зарегистрирован")
        return phone

    def clean_name(self):
        name = self.cleaned_data["name"]
        if not re.match(r"^[а-яА-ЯёЁ\s\-]+$", name):
            raise forms.ValidationError("Только кириллица")
        return name

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get("password")
        pw2 = cleaned_data.get("password_confirm")
        if pw and pw2 and pw != pw2:
            self.add_error("password_confirm", "Пароли не совпадают")
        return cleaned_data


class LoginForm(forms.Form):
    phone = forms.CharField(
        label="Телефон",
        max_length=12,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "+7XXXXXXXXXX",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-input",
                "placeholder": "Пароль",
            }
        ),
    )


class BookingForm(forms.Form):
    ZONE_CHOICES = [
        ("arena", "VR Арена (до 10 чел.)"),
        ("redroom", "RED Room (до 3 чел.)"),
        ("package", "Пакет (полная аренда VR Арены)"),
    ]

    zone = forms.ChoiceField(
        label="Зона",
        choices=ZONE_CHOICES,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_zone"}),
    )
    date = forms.DateField(
        label="Дата",
        widget=forms.DateInput(
            attrs={
                "class": "form-input",
                "type": "date",
            }
        ),
    )
    time_slot = forms.ChoiceField(
        label="Время начала",
        choices=[],
        widget=forms.Select(attrs={"class": "form-select", "id": "id_time_slot"}),
    )
    num_players = forms.IntegerField(
        label="Количество игроков",
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={"class": "form-input", "id": "id_num_players"}),
    )
    package = forms.ModelChoiceField(
        label="Пакет",
        queryset=Package.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_package"}),
    )
    game = forms.ModelChoiceField(
        label="Игра",
        queryset=Game.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_game"}),
    )
    notes = forms.CharField(
        label="Заметки",
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-input",
                "rows": 2,
                "placeholder": "Дополнительные пожелания...",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hours = []
        for h in range(10, 23):
            val = f"{h:02d}:00"
            label = f"{h:02d}:00 — {h + 1:02d}:00"
            hours.append((val, label))
        self.fields["time_slot"].choices = [("", "Выберите время")] + hours


class AdminBookingForm(BookingForm):
    """Форма для администратора — с полями клиента"""

    client_name = forms.CharField(
        label="Имя клиента",
        max_length=100,
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "Имя клиента",
            }
        ),
    )
    client_phone = forms.CharField(
        label="Телефон клиента",
        max_length=12,
        validators=[phone_validator],
        widget=forms.TextInput(
            attrs={
                "class": "form-input",
                "placeholder": "+7XXXXXXXXXX",
            }
        ),
    )
