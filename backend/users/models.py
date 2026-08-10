from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)


class UserPreferences(models.Model):
    class Theme(models.TextChoices):
        LIGHT = "light", "Claro"
        DARK = "dark", "Escuro"
        SYSTEM = "system", "Sistema"

    class Language(models.TextChoices):
        PT_BR = "pt-BR", "Português (Brasil)"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="preferences")
    theme = models.CharField(max_length=10, choices=Theme.choices, default=Theme.SYSTEM)
    language = models.CharField(max_length=10, choices=Language.choices, default=Language.PT_BR)
    daily_study_goal_minutes = models.PositiveIntegerField(default=60)
