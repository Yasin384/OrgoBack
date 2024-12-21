# main/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static

# Import ViewSets from views.py
from .views import (
    UserViewSet, CustomObtainAuthToken, SchoolClassViewSet, SubjectViewSet,
    ScheduleViewSet, HomeworkViewSet, SubmittedHomeworkViewSet, GradeViewSet,
    AttendanceViewSet, AchievementViewSet, UserProfileViewSet,
    LeaderboardViewSet, NotificationViewSet, logout_view, UserMeView,
)

# Import for Swagger documentation
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Initialize DRF Router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'classes', SchoolClassViewSet, basename='class')
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

# Configure Swagger/OpenAPI schema
schema_view = get_schema_view(
    openapi.Info(
        title="School App API",
        default_version='v1',
        description="API for managing the school system",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="support@schoolapp.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Define API versioning
api_version = 'v1'

urlpatterns = [
    path(f'api/{api_version}/', include([
        # Include all router URLs under /api/v1/
        path('', include(router.urls)),
        
        # Authentication routes
        path('login/', CustomObtainAuthToken.as_view(), name='api_token_auth'),
        path('logout/', logout_view, name='api_logout'),
        path('me/', UserMeView.as_view(), name='user_me'),
        
        # Swagger/OpenAPI documentation
        path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ])),
    
    # Optional: Include API versioning for future versions
    # path(f'api/{api_version}/', include('main.api_urls')),  # If you separate API URLs into another file
]

# Serve static and media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
