from rest_framework import serializers
from .models import Lead

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['id', 'name', 'phone', 'email', 'comment', 'type', 'house', 'consent']

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError("Нужно согласие.")
        return value