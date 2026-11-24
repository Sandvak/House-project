from django.urls import path
from .views import LeadCreateView
from .views import LeadCreateView, VisitCreateView

urlpatterns = [
    path('api/leads/', LeadCreateView.as_view()),
    path('api/visit/', VisitCreateView.as_view()), # <-- Добавили
]

urlpatterns = [
    path('api/leads/', LeadCreateView.as_view()),
]