from django.urls import path
from .views import LeadCreateView

urlpatterns = [
    path('api/leads/', LeadCreateView.as_view()),
]