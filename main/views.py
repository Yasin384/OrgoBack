# views.py

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.conf import settings

from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from geopy.distance import geodesic  # Для расчёта расстояний

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


# Кастомные классы разрешений
class IsTeacher(permissions.BasePermission):
    """
    Разрешение только для учителей.
    """
    def has_permission(self, request, view):
        return request.user.role == User.TEACHER


class IsStudent(permissions.BasePermission):
    """
    Разрешение только для студентов.
    """
    def has_permission(self, request, view):
        return request.user.role == User.STUDENT


class IsParent(permissions.BasePermission):
    """
    Разрешение только для родителей.
    """
    def has_permission(self, request, view):
        return request.user.role == User.PARENT


# Настройка времени истечения токена (24 часа)
TOKEN_EXPIRATION_TIME = datetime.timedelta(hours=24)


def token_is_expired(token):
    """
    Проверяет, истёк ли токен.
    """
    return timezone.now() > token.created + TOKEN_EXPIRATION_TIME


# Пагинатор по умолчанию
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserMeView(APIView):
    """
    Представление для получения информации о текущем пользователе.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_serializer = UserSerializer(request.user)
        user_profile_serializer = UserProfileSerializer(request.user.userprofile)
        return Response({
            **user_serializer.data,
            **user_profile_serializer.data
        })


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        """
        Регистрация нового пользователя.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
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
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления предметами.
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления расписанием занятий.
    """
    queryset = Schedule.objects.select_related('class_obj', 'subject', 'teacher').all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['class_obj__name', 'subject__name', 'teacher__username']
    ordering_fields = ['weekday', 'start_time']
    ordering = ['weekday', 'start_time']

    def get_queryset(self):
        """
        Ограничение доступа:
        - Учителя видят только свои расписания.
        - Студенты и родители — расписания их классов.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            return Schedule.objects.filter(teacher=user).select_related('class_obj', 'subject', 'teacher')
        elif user.role == User.STUDENT:
            class_objs = user.classes.all()
            return Schedule.objects.filter(class_obj__in=class_objs).select_related('class_obj', 'subject', 'teacher')
        elif user.role == User.PARENT:
            children = user.parent_relations.values_list('child', flat=True)
            class_objs = Class.objects.filter(students__in=children).distinct()
            return Schedule.objects.filter(class_obj__in=class_objs).select_related('class_obj', 'subject', 'teacher')
        else:
            return Schedule.objects.none()


class HomeworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления домашними заданиями.
    """
    queryset = Homework.objects.select_related('subject', 'class_obj').all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['subject__name', 'class_obj__name', 'description']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['due_date']

    def perform_create(self, serializer):
        """
        При создании домашнего задания автоматически связываем его с учителем.
        """
        serializer.save()


class SubmittedHomeworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления отправленными домашними заданиями.
    """
    queryset = SubmittedHomework.objects.select_related('homework', 'student').all()
    serializer_class = SubmittedHomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['homework__subject__name', 'student__username']
    ordering_fields = ['submitted_at', 'status']
    ordering = ['-submitted_at']

    def get_queryset(self):
        """
        - Учителя видят все отправленные задания по их предметам.
        - Студенты видят только свои отправленные задания.
        - Родители видят отправленные задания своих детей.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            return SubmittedHomework.objects.filter(homework__teacher=user).select_related('homework', 'student')
        elif user.role == User.STUDENT:
            return SubmittedHomework.objects.filter(student=user).select_related('homework', 'student')
        elif user.role == User.PARENT:
            children = user.parent_relations.values_list('child', flat=True)
            return SubmittedHomework.objects.filter(student__in=children).select_related('homework', 'student')
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
    queryset = Grade.objects.select_related('student', 'subject', 'teacher').all()
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['student__username', 'subject__name', 'teacher__username']
    ordering_fields = ['date', 'grade']
    ordering = ['-date']

    def get_queryset(self):
        """
        - Учителя видят оценки, которые они выставили.
        - Студенты видят только свои оценки.
        - Родители видят оценки своих детей.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            return Grade.objects.filter(teacher=user).select_related('student', 'subject', 'teacher')
        elif user.role == User.STUDENT:
            return Grade.objects.filter(student=user).select_related('student', 'subject', 'teacher')
        elif user.role == User.PARENT:
            children = user.parent_relations.values_list('child', flat=True)
            return Grade.objects.filter(student__in=children).select_related('student', 'subject', 'teacher')
        else:
            return Grade.objects.none()

    def perform_create(self, serializer):
        """
        При создании оценки автоматически связываем её с учителем.
        """
        serializer.save(teacher=self.request.user)


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления записями посещаемости.
    Включает пользовательские действия для отметки посещаемости на основе GPS координат.
    """
    queryset = Attendance.objects.select_related('student', 'class_obj', 'school').all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['student__username', 'class_obj__name', 'status']
    ordering_fields = ['date', 'status']
    ordering = ['-date']

    def get_queryset(self):
        """
        - Учителя видят посещаемость для своих классов.
        - Студенты видят только свою посещаемость.
        - Родители видят посещаемость своих детей.
        """
        user = self.request.user

        if user.role == User.TEACHER:
            # Получаем классы, которые ведёт учитель
            teacher_classes = Class.objects.filter(teachers=user)
            return Attendance.objects.filter(class_obj__in=teacher_classes).select_related('student', 'class_obj', 'school')
        elif user.role == User.STUDENT:
            return Attendance.objects.filter(student=user).select_related('student', 'class_obj', 'school')
        elif user.role == User.PARENT:
            # Получаем детей родителя
            children = User.objects.filter(parent_relations__parent=user)
            return Attendance.objects.filter(student__in=children).select_related('student', 'class_obj', 'school')
        else:
            return Attendance.objects.none()

    @action(detail=False, methods=['post'], permission_classes=[IsStudent])
    def mark_attendance(self, request):
        """
        Пользователь (студент) может отметить свою посещаемость на основе GPS координат.
        """
        user = request.user

        # Получаем школу пользователя
        school = user.school
        if not school:
            return Response({"error": "У пользователя не назначена школа."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Получаем координаты из запроса
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        if not latitude or not longitude:
            return Response({"error": "Необходимо указать широту и долготу."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            return Response({"error": "Неверный формат широты или долготы."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Расчёт расстояния до школы
        student_coords = (latitude, longitude)
        school_coords = (float(school.latitude), float(school.longitude))
        distance = geodesic(student_coords, school_coords).kilometers

        # Определяем статус посещаемости
        proximity_radius = 0.1  # Радиус в километрах (100 метров)
        status_value = 'present' if distance <= proximity_radius else 'absent'

        # Получаем класс пользователя
        class_obj = user.classes.first()
        if not class_obj:
            return Response({"error": "У студента не назначен класс."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Создаём или обновляем запись посещаемости на сегодня
        attendance, created = Attendance.objects.update_or_create(
            student=user,
            date=localtime(now()).date(),
            defaults={
                'class_obj': class_obj,
                'latitude': latitude,
                'longitude': longitude,
                'status': status_value,
            }
        )

        return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def today(self, request):
        """
        Получение записей посещаемости на сегодня для текущего пользователя.
        """
        user = request.user
        today_date = localtime(now()).date()

        if user.role == User.TEACHER:
            # Посещаемость для всех студентов учителя
            teacher_classes = Class.objects.filter(teachers=user)
            attendance_records = Attendance.objects.filter(
                class_obj__in=teacher_classes,
                date=today_date
            ).select_related('student', 'class_obj', 'school')
        elif user.role == User.STUDENT:
            # Посещаемость только для студента
            attendance_records = Attendance.objects.filter(student=user, date=today_date).select_related('student', 'class_obj', 'school')
        elif user.role == User.PARENT:
            # Посещаемость для детей родителя
            children = User.objects.filter(parent_relations__parent=user)
            attendance_records = Attendance.objects.filter(student__in=children, date=today_date).select_related('student', 'class_obj', 'school')
        else:
            return Response({"error": "У вас нет доступа к этому эндпоинту."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = AttendanceSerializer(attendance_records, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AchievementViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления достижениями.
    """
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['xp_reward', 'name']
    ordering = ['name']


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления профилями пользователей.
    """
    queryset = UserProfile.objects.select_related('user').prefetch_related('achievements').all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    ordering_fields = ['xp', 'level']
    ordering = ['-xp']

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return UserProfile.objects.all().select_related('user').prefetch_related('achievements')
        else:
            return UserProfile.objects.filter(user=user).select_related('user').prefetch_related('achievements')


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly ViewSet для отображения таблицы лидеров.
    """
    queryset = Leaderboard.objects.select_related('user_profile__user').all().order_by('rank')
    serializer_class = LeaderboardSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user_profile__user__username']
    ordering_fields = ['rank']
    ordering = ['rank']


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления уведомлениями.
    """
    queryset = Notification.objects.select_related('user').all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['message']
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        - Админы видят все уведомления.
        - Остальные пользователи видят только свои уведомления.
        """
        user = self.request.user
        if user.is_staff:
            return Notification.objects.all().select_related('user')
        return Notification.objects.filter(user=user).select_related('user')

    def perform_create(self, serializer):
        """
        При создании уведомления связываем его с текущим пользователем.
        """
        serializer.save(user=self.request.user)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Выход пользователя: удаление токена.
    """
    try:
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({"success": "Токен успешно удалён."}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({"error": "Токен не найден."}, status=status.HTTP_400_BAD_REQUEST)