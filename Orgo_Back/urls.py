# Orgo_Back/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Импортируем необходимые классы для документации API
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Настройка схемы для drf-yasg
schema_view = get_schema_view(
    openapi.Info(
        title="School API",
        default_version='v1',
        description="Документация API для школьного приложения",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Админ-панель Django
    
    path('admin/', admin.site.urls),

    # Включаем маршруты приложения 'main'
    path('api/', include('main.urls')),
   
    # Маршруты для аутентификации через browsable API DRF
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Маршруты для документации API с использованием drf-yasg
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Добавляем маршруты для обслуживания медиа-файлов во время разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
