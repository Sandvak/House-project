from django.db import models
from houses.models import House

class Request(models.Model):
    STATUS_CHOICES = (
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('meeting', 'Назначена встреча'),
        ('closed', 'Закрыта'),
    )

    name = models.CharField("Имя", max_length=100)
    phone = models.CharField("Телефон", max_length=20)
    email = models.EmailField("Email", blank=True, null=True)
    comment = models.TextField("Комментарий", blank=True, null=True)
    house = models.ForeignKey(House, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Дом")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')
    meeting_date = models.DateTimeField("Дата и время встречи", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Заявка от {self.name}"

class ConstructorCalculation(models.Model):
    MATERIAL_CHOICES = (
        ('frame', 'Каркас'),
        ('timber', 'Брус'),
        ('aerated', 'Газобетон'),
        ('brick', 'Кирпич'),
    )
    material = models.CharField("Материал", max_length=20, choices=MATERIAL_CHOICES)
    area = models.FloatField("Площадь (кв.м)")
    floors = models.IntegerField("Этажность", default=1)
    has_heated_floor = models.BooleanField("Теплый пол", default=False)
    has_insulation = models.BooleanField("Утепление", default=False)
    has_light = models.BooleanField("Свет", default=False)
    has_water = models.BooleanField("Вода", default=False)
    has_septic = models.BooleanField("Септик", default=False)
    total_price = models.DecimalField("Итоговая стоимость", max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)