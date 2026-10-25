from django.db import models

class House(models.Model):
    STATUS_CHOICES = (
        ('sale', 'Продаётся'),
        ('sold', 'Продан'),
        ('reserved', 'Зарезервирован'),
    )
    TYPE_CHOICES = (
        ('brick', 'Кирпич'),
        ('block', 'Блок'),
        ('wood', 'Дерево'),
        ('frame', 'Каркас'),
    )

    title = models.CharField("Название", max_length=255)
    price = models.DecimalField("Цена", max_digits=12, decimal_places=2)
    area_house = models.FloatField("Площадь дома (кв.м)")
    area_land = models.FloatField("Площадь участка (соток)", default=0)
    rooms = models.IntegerField("Количество комнат")
    floors = models.IntegerField("Этажность")
    house_type = models.CharField("Тип дома", max_length=20, choices=TYPE_CHOICES)
    description = models.TextField("Описание")
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='sale')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.price} руб."

class HousePhoto(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField("Фото", upload_to='houses/')
    is_main = models.BooleanField("Главное фото", default=False)