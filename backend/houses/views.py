from rest_framework import viewsets
from django_filters import rest_framework as filters
from .models import House
from .serializers import HouseSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response

class ContentAPIView(APIView):
    def get(self, request):
        return Response({}) # Пока возвращаем пустой объект, фронтенд возьмет текст из HTML
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



class ConstructorCalculateView(APIView):
    authentication_classes = []
    def post(self, request):
        area = float(request.data.get('area', 0))
        material = request.data.get('material', 'frame')
        floors = int(request.data.get('floors', 1))
        warm_floor = request.data.get('warm_floor', False)
        insulation = request.data.get('insulation', False)
        electricity = request.data.get('electricity', False)
        water = request.data.get('water', False)
        septic = request.data.get('septic', False)
        

        prices = {
            'frame': {'name': 'Каркас', 'base': 25000, 'warm': 3500, 'insul': 3000},
            'timber': {'name': 'Брус', 'base': 35000, 'warm': 3500, 'insul': 4000},
            'gas': {'name': 'Газобетон', 'base': 50000, 'warm': 5000, 'insul': 4000},
            'brick': {'name': 'Кирпич', 'base': 80000, 'warm': 5000, 'insul': 4000}
        }

        if material not in prices:
            return Response({"error": "Неверный материал"}, status=400)

        breakdown = []
        
        # Базовая стоимость
        base_cost = area * prices[material]['base']
        breakdown.append({"label": "Базовая стоимость", "value": base_cost})

        # Скидка за 1 этаж
        if floors == 1:
            discount = - (base_cost * 0.05)
            breakdown.append({"label": "Скидка за один этаж (5 %)", "value": discount})

        # Опции
        if insulation:
            breakdown.append({"label": "Утепление", "value": area * prices[material]['insul']})
        if warm_floor:
            breakdown.append({"label": "Тёплый пол", "value": area * prices[material]['warm']})
        
        # Коммуникации
        if electricity: breakdown.append({"label": "Электричество", "value": 150000})
        if water: breakdown.append({"label": "Вода", "value": 250000})
        if septic: breakdown.append({"label": "Септик", "value": 200000})

        # Считаем итог
        total_price = sum(item['value'] for item in breakdown)

        return Response({
            "total_price": int(total_price),
            "breakdown": breakdown
        })