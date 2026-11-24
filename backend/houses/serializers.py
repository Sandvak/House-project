from rest_framework import serializers
from .models import House, HousePhoto

class HousePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousePhoto
        fields = ['image']

class HouseSerializer(serializers.ModelSerializer):
    # Переводим наши поля в те названия, которые ждет фронтендер
    area = serializers.FloatField(source='area_house')
    plot = serializers.FloatField(source='area_land')
    material = serializers.CharField(source='get_house_type_display')
    status = serializers.CharField(source='get_status_display')
    
    # Поля, которых у нас пока нет в БД, но они нужны фронтенду (создаем заглушки)
    district = serializers.SerializerMethodField()
    popularity = serializers.IntegerField(default=1)
    
    # Картинки и галерея
    image = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    plan = serializers.SerializerMethodField()

    class Meta:
        model = House
        fields = [
            'id', 'title', 'image', 'gallery', 'price', 'area', 'plot', 
            'rooms', 'floors', 'district', 'material', 'status', 
            'description', 'plan', 'popularity'
        ]

    def get_district(self, obj):
        # Так как в модели пока нет района, отдаем заглушку (или можно добавить поле в модель позже)
        return "Республика Татарстан"

    def get_image(self, obj):
        request = self.context.get('request')
        main_photo = obj.photos.filter(is_main=True).first() or obj.photos.first()
        if main_photo and request:
            # Возвращаем полный путь к картинке (http://127.0.0.1:8000/media/...)
            return request.build_absolute_uri(main_photo.image.url)
        return ""

    def get_gallery(self, obj):
        request = self.context.get('request')
        if request:
            return [request.build_absolute_uri(photo.image.url) for photo in obj.photos.all()]
        return []

    def get_plan(self, obj):
        # Если планировки нет, возвращаем пустую строку
        return ""