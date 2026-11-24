from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HouseViewSet
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HouseViewSet, ContentAPIView, ConstructorCalculateView 

router = DefaultRouter()
router.register(r'houses', HouseViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/content/', ContentAPIView.as_view()),
    path('api/constructor/', ConstructorCalculateView.as_view()), # <-- Добавили
]

router = DefaultRouter()
router.register(r'houses', HouseViewSet)






