from rest_framework import generics, permissions
from .models import Lead
from rest_framework.authentication import SessionAuthentication
from .serializers import LeadSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Visit
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


class VisitCreateView(APIView):
    def post(self, request):
        # Сохраняем визит (IP берем из запроса)
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        Visit.objects.create(ip_address=ip, user_agent=user_agent)
        return Response({"status": "ok"})

class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Просто возвращаем пустоту, токен не проверяется


@method_decorator(csrf_exempt, name='dispatch')     
class LeadCreateView(generics.CreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = [CsrfExemptSessionAuthentication]


    def perform_create(self, serializer):
        lead = serializer.save()