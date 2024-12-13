# main/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions

# Импортируем представления (ViewSet'ы) из views.py
from .views import (
    UserViewSet, CustomObtainAuthToken, ClassViewSet, SubjectViewSet,
    ScheduleViewSet, HomeworkViewSet, SubmittedHomeworkViewSet, GradeViewSet,
    AttendanceViewSet, AchievementViewSet, UserProfileViewSet,
    LeaderboardViewSet, NotificationViewSet, logout_view, UserMeView,
)

# Импорт для Swagger-документации (если требуется, можно оставить)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Создаём роутер и регистрируем ViewSet'ы
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'classes', ClassViewSet, basename='class')
router.register(r'subjects', SubjectViewSet, basename='subject')
router.register(r'schedules', ScheduleViewSet, basename='schedule')
router.register(r'homeworks', HomeworkViewSet, basename='homework')
router.register(r'submitted-homeworks', SubmittedHomeworkViewSet, basename='submitted_homework')
router.register(r'grades', GradeViewSet, basename='grade')
router.register(r'attendances', AttendanceViewSet, basename='attendance')
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'user-profiles', UserProfileViewSet, basename='userprofile')
router.register(r'leaderboard', LeaderboardViewSet, basename='leaderboard')
router.register(r'notifications', NotificationViewSet, basename='notification')

# Настройка схемы для Swagger (если требуется)
schema_view = get_schema_view(
    openapi.Info(
        title="School App API",
        default_version='v1',
        description="API для управления школьной системой",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@schoolapp.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Включаем все маршруты из роутера без префикса 'api/'
    path('', include(router.urls)),

    # Маршруты для аутентификации
    path('login/', CustomObtainAuthToken.as_view(), name='api_token_auth'),
    path('logout/', logout_view, name='api_logout'),
    path('me/', UserMeView.as_view(), name='user_me'),
    
    # Если Swagger маршруты уже подключены в основном urls.py, их можно удалить отсюда
    # path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]