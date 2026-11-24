from rest_framework import serializers
from .models import House, HousePhoto

class HousePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousePhoto
        fields = ['id', 'image', 'is_main']

class HouseSerializer(serializers.ModelSerializer):
    photos = HousePhotoSerializer(many=True, read_only=True)
    house_type_display = serializers.CharField(source='get_house_type_display', read_only=True)

    class Meta:
        model = House
        fields = '__all__'