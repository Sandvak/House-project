from rest_framework import viewsets
from django_filters import rest_framework as filters
from .models import House
from .serializers import HouseSerializer

class HouseFilter(filters.FilterSet):
    price_min = filters.NumberFilter(field_name="price", lookup_expr='gte')
    price_max = filters.NumberFilter(field_name="price", lookup_expr='lte')
    
    class Meta:
        model = House
        fields = ['house_type', 'status', 'rooms', 'price_min', 'price_max']

class HouseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = House.objects.filter(status='sale').order_by('-created_at') 
    serializer_class = HouseSerializer
    filterset_class = HouseFilter