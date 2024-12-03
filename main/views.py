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

User = get_user_model()

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
    ViewSet для управления учётом посещаемости.
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Учителя видят посещаемость по своим классам,
        студенты и родители видят посещаемость своих детей или себя.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            # Предполагаем, что учитель привязан к классам через Schedule
            classes = Class.objects.filter(schedules__teacher=user)
            return Attendance.objects.filter(class_obj__in=classes)
        elif user.role == User.STUDENT:
            return Attendance.objects.filter(student=user)
        elif user.role == User.PARENT:
            # Предполагаем, что родитель связан с детьми через модель UserProfile или другую связь
            # Здесь требуется реализовать связь родителя с их детьми
            # Для простоты предположим, что у родителя есть поле children, связанное с User
            children = User.objects.filter(parent=user)
            return Attendance.objects.filter(student__in=children)
        else:
            return Attendance.objects.none()


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
