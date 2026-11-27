from rest_framework import serializers
from .models import Lead
import urllib.request
import urllib.parse
import json
from django.conf import settings

class LeadSerializer(serializers.ModelSerializer):
    # 1. Добавляем поле для токена капчи (оно не сохраняется в БД, только для проверки)
    recaptcha_token = serializers.CharField(write_only=True)

    class Meta:
        model = Lead
        # 2. Добавляем 'recaptcha_token' в список полей
        fields = ['id', 'name', 'phone', 'email', 'comment', 'type', 'house', 'consent', 'recaptcha_token']

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError("Нужно согласие.")
        return value

    # 3. Добавляем общий метод validate для проверки капчи
    def validate(self, data):
        token = data.get('recaptcha_token')
        
        if not token:
            print("❌ ОШИБКА: Фронтенд не прислал токен капчи!")
            raise serializers.ValidationError({"captcha": "Токен капчи отсутствует."})
            
        secret_key = settings.RECAPTCHA_SECRET_KEY
        url = 'https://www.google.com/recaptcha/api/siteverify'
        params = {'secret': secret_key, 'response': token}
        
        data_encoded = urllib.parse.urlencode(params).encode('utf-8')
        req = urllib.request.Request(url, data=data_encoded)
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                
            # ВЫВОДИМ ОТВЕТ ОТ ГУГЛА В ТЕРМИНАЛ
            print("🔍 ОТВЕТ ОТ GOOGLE:", result)
                
            if not result.get('success'):
                raise serializers.ValidationError({"captcha": "Неверная капча."})
        except Exception as e:
            print(f"❌ ОШИБКА СЕТИ: {e}")
            raise serializers.ValidationError({"captcha": "Ошибка проверки капчи на сервере."})

        return data    

    def create(self, validated_data):
        # Вырезаем токен капчи, чтобы он не мешал сохранять заявку
        validated_data.pop('recaptcha_token', None)
        return super().create(validated_data)