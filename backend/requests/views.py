from rest_framework import generics
from .models import Lead
from .serializers import LeadSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Visit

class VisitCreateView(APIView):
    def post(self, request):
        # Сохраняем визит (IP берем из запроса)
        ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT')
        Visit.objects.create(ip_address=ip, user_agent=user_agent)
        return Response({"status": "ok"})
        
class LeadCreateView(generics.CreateAPIView):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer