from django.shortcuts import render
# views.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import (
    Class, Subject, Schedule, Homework, SubmittedHomework,
    Grade, Attendance, Achievement, UserProfile,
    UserAchievement, Leaderboard, Notification
)
from .serializers import (
    UserSerializer, ClassSerializer, SubjectSerializer, ScheduleSerializer,
    HomeworkSerializer, SubmittedHomeworkSerializer, GradeSerializer,
    AttendanceSerializer, AchievementSerializer, UserProfileSerializer,
    UserAchievementSerializer, LeaderboardSerializer, NotificationSerializer,
    UserRegistrationSerializer
)

import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .serializers import UserSerializer, UserProfileSerializer
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.timezone import now, localtime
from geopy.distance import geodesic  # For distance calculations
from .models import Attendance, User, Class
from .serializers import AttendanceSerializer
User = get_user_model()
class UserMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_serializer = UserSerializer(request.user)
        user_profile_serializer = UserProfileSerializer(request.user.userprofile)
        return Response({
            **user_serializer.data,
            **user_profile_serializer.data
        })


# Настройка времени истечения токена (24 часа)
TOKEN_EXPIRATION_TIME = datetime.timedelta(hours=24)


def token_is_expired(token):
    """
    Проверяет, истёк ли токен.
    """
    return timezone.now() > token.created + TOKEN_EXPIRATION_TIME


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        Регистрация нового пользователя.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Создание токена вручную, если нужно
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomObtainAuthToken(ObtainAuthToken):
    """
    Кастомный ObtainAuthToken для добавления проверки истечения токена.
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        if not created and token_is_expired(token):
            # Удаляем истёкший токен и создаём новый
            token.delete()
            token = Token.objects.create(user=user)

        return Response({'token': token.key})


class ClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления классами.
    """
    queryset = Class.objects.all()
    serializer_class = ClassSerializer
    permission_classes = [permissions.IsAuthenticated]


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления предметами.
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления расписанием занятий.
    """
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Ограничение доступа: учителя видят только свои расписания,
        студенты и родители — расписания их классов.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            return Schedule.objects.filter(teacher=user)
        elif user.role in [User.STUDENT, User.PARENT]:
            # Предположим, что у пользователя есть связь с классом
            # Здесь требуется реализовать связь студента с классом
            # Для простоты предположим, что у пользователя есть поле class_obj
            return Schedule.objects.filter(class_obj=user.profile.class_obj)
        else:
            return Schedule.objects.none()


class HomeworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления домашними заданиями.
    """
    queryset = Homework.objects.all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        """
        При создании домашнего задания автоматически связываем его с учителем.
        """
        serializer.save()


class SubmittedHomeworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления отправленными домашними заданиями.
    """
    queryset = SubmittedHomework.objects.all()
    serializer_class = SubmittedHomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Учителя видят все отправленные задания по их предметам,
        студенты видят только свои отправленные задания.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            return SubmittedHomework.objects.filter(homework__teacher=user)
        elif user.role == User.STUDENT:
            return SubmittedHomework.objects.filter(student=user)
        else:
            return SubmittedHomework.objects.none()

    def perform_create(self, serializer):
        """
        При создании отправленного задания связываем его с текущим студентом.
        """
        serializer.save(student=self.request.user)


class GradeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления оценками.
    """
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Учителя видят оценки, которые они выставили,
        студенты видят только свои оценки.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            return Grade.objects.filter(teacher=user)
        elif user.role == User.STUDENT:
            return Grade.objects.filter(student=user)
        else:
            return Grade.objects.none()

    def perform_create(self, serializer):
        """
        При создании оценки автоматически связываем её с учителем.
        """
        serializer.save(teacher=self.request.user)


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance records.
    Includes a custom action to mark attendance based on GPS coordinates.
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Teachers see attendance for their classes.
        Students and parents see attendance relevant to them.
        """
        user = self.request.user

        if user.role == User.TEACHER:
            # Teachers see attendance for their classes
            teacher_classes = Class.objects.filter(schedules__teacher=user)
            return Attendance.objects.filter(class_obj__in=teacher_classes)
        elif user.role == User.STUDENT:
            # Students see only their attendance records
            return Attendance.objects.filter(student=user)
        elif user.role == User.PARENT:
            # Parents see attendance for their children (assuming a parent-child relationship exists)
            children = User.objects.filter(parent=user)
            return Attendance.objects.filter(student__in=children)
        else:
            return Attendance.objects.none()

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def mark_attendance(self, request):
        """
        Custom endpoint to mark attendance based on GPS coordinates.
        """
        user = request.user

        if user.role != User.STUDENT:
            return Response({"error": "Only students can mark attendance."}, status=status.HTTP_403_FORBIDDEN)

        # Retrieve the school coordinates
        school = getattr(user, 'school', None)  # Assuming the User model has a `school` attribute
        if not school:
            return Response({"error": "No school assigned to this user."}, status=status.HTTP_400_BAD_REQUEST)

        # Get latitude and longitude from the request
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        if not latitude or not longitude:
            return Response({"error": "Latitude and longitude are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return Response({"error": "Invalid latitude or longitude format."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the student is within a valid range of the school
        student_coords = (latitude, longitude)
        school_coords = (float(school.latitude), float(school.longitude))
        distance = geodesic(student_coords, school_coords).kilometers

        # Define the acceptable proximity radius (e.g., 100 meters = 0.1 km)
        proximity_radius = 0.1  # 100 meters

        # Determine attendance status
        status_value = 'present' if distance <= proximity_radius else 'absent'

        # Create or update the attendance record for today
        attendance, created = Attendance.objects.update_or_create(
            student=user,
            date=localtime(now()).date(),
            defaults={
                'class_obj': user.classes.first(),  # Assuming a student is associated with a class
                'latitude': latitude,
                'longitude': longitude,
                'status': status_value,
            }
        )

        return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def today(self, request):
        """
        Custom endpoint to retrieve today's attendance for the authenticated user.
        """
        user = request.user
        today_date = localtime(now()).date()

        if user.role == User.TEACHER:
            # Retrieve attendance for all students in the teacher's classes
            teacher_classes = Class.objects.filter(schedules__teacher=user)
            attendance_records = Attendance.objects.filter(
                class_obj__in=teacher_classes, date=today_date
            )
        elif user.role == User.STUDENT:
            # Retrieve only the student's attendance for today
            attendance_records = Attendance.objects.filter(student=user, date=today_date)
        elif user.role == User.PARENT:
            # Retrieve attendance for all children of the parent
            children = User.objects.filter(parent=user)
            attendance_records = Attendance.objects.filter(student__in=children, date=today_date)
        else:
            return Response({"error": "You do not have access to this endpoint."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AttendanceSerializer(attendance_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AchievementViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления достижениями.
    """
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAdminUser]


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления профилями пользователей.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == User.ADMIN:
            return UserProfile.objects.all()
        else:
            return UserProfile.objects.filter(user=user)


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly ViewSet для отображения таблицы лидеров.
    """
    queryset = Leaderboard.objects.all().order_by('rank')
    serializer_class = LeaderboardSerializer
    permission_classes = [permissions.IsAuthenticated]


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления уведомлениями.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Пользователи видят только свои уведомления.
        Админы видят все уведомления.
        """
        user = self.request.user
        if user.is_staff:
            return Notification.objects.all()
        return Notification.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        При создании уведомления связываем его с текущим пользователем.
        """
        serializer.save(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def logout_view(request):
    """
    Logout пользователя: удаление токена.
    """
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response(status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)
# Create your views here.
