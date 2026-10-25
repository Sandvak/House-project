from django.contrib import admin
from .models import Request, ConstructorCalculation

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'status', 'meeting_date')
    list_filter = ('status',)

admin.site.register(ConstructorCalculation)