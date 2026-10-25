from django.contrib import admin
from .models import House, HousePhoto

class HousePhotoInline(admin.TabularInline):
    model = HousePhoto
    extra = 1

@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'status', 'house_type')
    list_filter = ('status', 'house_type')
    inlines = [HousePhotoInline]