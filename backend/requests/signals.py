from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import Lead

User = get_user_model()

@receiver(post_save, sender=Lead)
def send_lead_notification(sender, instance, created, **kwargs):
    if created:
        subject = f"Новая заявка на сайте: {instance.get_type_display()}"
        
        house_info = f"Дом ID: {instance.house.id} ({instance.house.title})" if instance.house else "Не привязан к дому"
        
        message = f"""
        Поступила новая заявка!
        
        Имя: {instance.name}
        Телефон: {instance.phone}
        Email: {instance.email if instance.email else 'Не указан'}
        Тип заявки: {instance.get_type_display()}
        Объект: {house_info}
        Комментарий: {instance.comment if instance.comment else 'Нет'}
        
        Зайдите в админку для обработки: http://127.0.0.1:8000/admin/
        """
        
        # Ищем всех пользователей с ролями 'admin' и 'manager' и с заполненной почтой
        managers = User.objects.filter(role__in=['admin', 'manager']).exclude(email='')
        
        # Собираем их почты в список
        recipient_list = [user.email for user in managers]
        
        if not recipient_list:
            print("⚠️ Внимание: Нет менеджеров или админов с указанной почтой!")
            return

        try:
            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                recipient_list,
                fail_silently=False,
            )
            print(f"✅ Письмо успешно отправлено менеджерам: {recipient_list}")
        except Exception as e:
            print(f"❌ Ошибка отправки письма: {e}")