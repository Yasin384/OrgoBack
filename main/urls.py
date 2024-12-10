# main/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Импортируем представления (ViewSet'ы) из views.py
from .views import (
    UserViewSet, CustomObtainAuthToken, ClassViewSet, SubjectViewSet,
    ScheduleViewSet, HomeworkViewSet, SubmittedHomeworkViewSet, GradeViewSet,
    AttendanceViewSet, AchievementViewSet, UserProfileViewSet,
    LeaderboardViewSet, NotificationViewSet, logout_view,UserMeView,
)

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

urlpatterns = [
    # Включаем все маршруты из роутера
    path('', include(router.urls)),

    # Маршруты для аутентификации
    path('login/', CustomObtainAuthToken.as_view(), name='api_token_auth'),
    path('logout/', logout_view, name='api_logout'),
    path('me/', UserMeView.as_view(), name='user_me'), 
]



