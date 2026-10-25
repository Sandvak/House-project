from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('manager', 'Менеджер'),
        ('content', 'Контент-менеджер'),
    )
    role = models.CharField("Роль", max_length=20, choices=ROLE_CHOICES, default='manager')
    email_code = models.CharField("Код подтверждения", max_length=6, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"