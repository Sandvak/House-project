from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import os

# Указываем путь к папке frontend (поднимаемся из backend на уровень выше)
FRONTEND_DIR = os.path.join(settings.BASE_DIR, '..', 'frontend')

urlpatterns = [
    # 1. Админка
    path('admin/', admin.site.urls),
    
    # 2. API для домов и заявок
    path('', include('houses.urls')),
    path('', include('requests.urls')),
]

# Раздача картинок и файлов сайта (только для разработки)
if settings.DEBUG:
    # Отдаем загруженные фото (media)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Отдаем файлы твоего фронтенда (index.html, css, js, images)
    urlpatterns += [
        re_path(r'^$', serve, {'path': 'index.html', 'document_root': FRONTEND_DIR}),
        re_path(r'^(?P<path>.*)$', serve, {'document_root': FRONTEND_DIR}),
    ]