from django.db import models
from houses.models import House 

class Lead(models.Model):
    STATUS_CHOICES = (('new', 'Новая'), ('in_work', 'В работе'), ('meeting', 'Назначена встреча'), ('closed', 'Закрыта'))
    TYPE_CHOICES = (('consult', 'Консультация'), ('callback', 'Обратный звонок'), ('question', 'Вопрос по объекту'))

    name = models.CharField("Имя", max_length=100)
    phone = models.CharField("Телефон", max_length=20)
    email = models.EmailField("Email", blank=True, null=True)
    comment = models.TextField("Комментарий", blank=True)
    type = models.CharField("Тип", max_length=20, choices=TYPE_CHOICES, default='consult')
    house = models.ForeignKey(House, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='new')
    consent = models.BooleanField("Согласие", default=False)
    created_at = models.DateTimeField(auto_now_add=True)