# main/views.py

import logging
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

# Получаем логгер для текущего модуля
logger = logging.getLogger(__name__)


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
        try:
            user_serializer = UserSerializer(request.user)
            try:
                user_profile_serializer = UserProfileSerializer(request.user.profile)
            except UserProfile.DoesNotExist:
                user_profile_serializer = None
                logger.warning(f"Пользователь {request.user.username} не имеет UserProfile.")
            response_data = user_serializer.data
            if user_profile_serializer:
                response_data.update(user_profile_serializer.data)
            else:
                response_data.update({"profile": "Профиль не найден."})
            logger.info(f"Пользователь {request.user.username} получил информацию о себе.")
            return Response(response_data)
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса /api/me/ для пользователя {request.user.username}: {e}")
            return Response({"error": "Не удалось получить информацию о пользователе."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            try:
                user = serializer.save()
                token, created = Token.objects.get_or_create(user=user)
                logger.info(f"Зарегистрирован новый пользователь: {user.username}")
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Ошибка при регистрации пользователя: {e}")
                return Response({"error": "Не удалось зарегистрировать пользователя."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Некорректные данные при регистрации пользователя: {serializer.errors}")
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
            logger.info(f"Токен пользователя {user.username} истёк и создаётся новый.")
            token.delete()
            token = Token.objects.create(user=user)
        else:
            logger.info(f"Токен пользователя {user.username} получен.")

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

    def perform_create(self, serializer):
        try:
            class_obj = serializer.save()
            logger.info(f"Создан новый класс: {class_obj.name}")
        except Exception as e:
            logger.error(f"Ошибка при создании класса: {e}")
            raise e


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

    def perform_create(self, serializer):
        try:
            subject = serializer.save()
            logger.info(f"Создан новый предмет: {subject.name}")
        except Exception as e:
            logger.error(f"Ошибка при создании предмета: {e}")
            raise e


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
    user = self.request.user
    logger.debug(f"Fetching schedules for user: {user.username} with role: {user.role}")

    if user.role == User.TEACHER:
        queryset = Schedule.objects.filter(teacher=user).select_related('class_obj', 'subject', 'teacher')
        logger.debug(f"Teacher schedules: {queryset}")
        return queryset
    elif user.role == User.STUDENT:
        class_objs = user.classes.all()
        queryset = Schedule.objects.filter(class_obj__in=class_objs).select_related('class_obj', 'subject', 'teacher')
        logger.debug(f"Student schedules: {queryset}")
        return queryset
    elif user.role == User.PARENT:
        children = user.parent_relations.values_list('child', flat=True)
        class_objs = Class.objects.filter(students__in=children).distinct()
        queryset = Schedule.objects.filter(class_obj__in=class_objs).select_related('class_obj', 'subject', 'teacher')
        logger.debug(f"Parent schedules: {queryset}")
        return queryset
    else:
        logger.warning(f"Unknown role for user: {user.username}")
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
        try:
            homework = serializer.save()
            logger.info(f"Создано домашнее задание: {homework.description} для класса {homework.class_obj.name}")
        except Exception as e:
            logger.error(f"Ошибка при создании домашнего задания: {e}")
            raise e


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
            queryset = SubmittedHomework.objects.filter(homework__teacher=user).select_related('homework', 'student')
            logger.debug(f"Учитель {user.username} просматривает отправленные домашние задания по своим предметам.")
            return queryset
        elif user.role == User.STUDENT:
            queryset = SubmittedHomework.objects.filter(student=user).select_related('homework', 'student')
            logger.debug(f"Студент {user.username} просматривает свои отправленные домашние задания.")
            return queryset
        elif user.role == User.PARENT:
            children = user.parent_relations.values_list('child', flat=True)
            queryset = SubmittedHomework.objects.filter(student__in=children).select_related('homework', 'student')
            logger.debug(f"Родитель {user.username} просматривает отправленные задания своих детей.")
            return queryset
        else:
            logger.warning(f"Пользователь {user.username} с неизвестной ролью пытается получить доступ к отправленным заданиям.")
            return SubmittedHomework.objects.none()

    def perform_create(self, serializer):
        try:
            submitted_homework = serializer.save(student=self.request.user)
            logger.info(f"Студент {self.request.user.username} отправил домашнее задание: {submitted_homework.homework.description}")
        except Exception as e:
            logger.error(f"Ошибка при отправке домашнего задания студентом {self.request.user.username}: {e}")
            raise e


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
            queryset = Grade.objects.filter(teacher=user).select_related('student', 'subject', 'teacher')
            logger.debug(f"Учитель {user.username} просматривает свои оценки.")
            return queryset
        elif user.role == User.STUDENT:
            queryset = Grade.objects.filter(student=user).select_related('student', 'subject', 'teacher')
            logger.debug(f"Студент {user.username} просматривает свои оценки.")
            return queryset
        elif user.role == User.PARENT:
            children = user.parent_relations.values_list('child', flat=True)
            queryset = Grade.objects.filter(student__in=children).select_related('student', 'subject', 'teacher')
            logger.debug(f"Родитель {user.username} просматривает оценки своих детей.")
            return queryset
        else:
            logger.warning(f"Пользователь {user.username} с неизвестной ролью пытается получить доступ к оценкам.")
            return Grade.objects.none()

    def perform_create(self, serializer):
        try:
            grade = serializer.save(teacher=self.request.user)
            logger.info(f"Учитель {self.request.user.username} выставил оценку {grade.grade} студенту {grade.student.username} по предмету {grade.subject.name}")
        except Exception as e:
            logger.error(f"Ошибка при выставлении оценки: {e}")
            raise e


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
            teacher_classes = Class.objects.filter(teachers=user)
            queryset = Attendance.objects.filter(class_obj__in=teacher_classes).select_related('student', 'class_obj', 'school')
            logger.debug(f"Учитель {user.username} просматривает посещаемость своих классов.")
            return queryset
        elif user.role == User.STUDENT:
            queryset = Attendance.objects.filter(student=user).select_related('student', 'class_obj', 'school')
            logger.debug(f"Студент {user.username} просматривает свою посещаемость.")
            return queryset
        elif user.role == User.PARENT:
            children = User.objects.filter(parent_relations__parent=user)
            queryset = Attendance.objects.filter(student__in=children).select_related('student', 'class_obj', 'school')
            logger.debug(f"Родитель {user.username} просматривает посещаемость своих детей.")
            return queryset
        else:
            logger.warning(f"Пользователь {user.username} с неизвестной ролью пытается получить доступ к посещаемости.")
            return Attendance.objects.none()

    @action(detail=False, methods=['post'], permission_classes=[IsStudent])
    def mark_attendance(self, request):
        """
        Пользователь (студент) может отметить свою посещаемость на основе GPS координат.
        """
        user = request.user

        try:
            # Получаем школу пользователя
            school = user.school
            if not school:
                logger.warning(f"Студент {user.username} не имеет назначенной школы.")
                return Response({"error": "У пользователя не назначена школа."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Получаем координаты из запроса
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            if not latitude or not longitude:
                logger.warning(f"Студент {user.username} отправил неполные координаты для посещаемости.")
                return Response({"error": "Необходимо указать широту и долготу."},
                                status=status.HTTP_400_BAD_REQUEST)

            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            logger.warning(f"Студент {user.username} отправил некорректные координаты: latitude={latitude}, longitude={longitude}")
            return Response({"error": "Неверный формат широты или долготы."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Неизвестная ошибка при обработке координат студента {user.username}: {e}")
            return Response({"error": "Не удалось обработать координаты."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
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
                logger.warning(f"Студент {user.username} не назначен в класс.")
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

            if created:
                logger.info(f"Студент {user.username} отметил посещаемость как {'присутствует' if status_value == 'present' else 'отсутствует'}")
            else:
                logger.info(f"Студент {user.username} обновил посещаемость на {'присутствует' if status_value == 'present' else 'отсутствует'}")

            return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Ошибка при отметке посещаемости студентом {user.username}: {e}")
            return Response({"error": "Не удалось отметить посещаемость."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def today(self, request):
        """
        Получение записей посещаемости на сегодня для текущего пользователя.
        """
        user = request.user
        today_date = localtime(now()).date()

        try:
            if user.role == User.TEACHER:
                teacher_classes = Class.objects.filter(teachers=user)
                attendance_records = Attendance.objects.filter(
                    class_obj__in=teacher_classes,
                    date=today_date
                ).select_related('student', 'class_obj', 'school')
                logger.info(f"Учитель {user.username} запрашивает посещаемость своих классов на сегодня.")
            elif user.role == User.STUDENT:
                attendance_records = Attendance.objects.filter(student=user, date=today_date).select_related('student', 'class_obj', 'school')
                logger.info(f"Студент {user.username} запрашивает свою посещаемость на сегодня.")
            elif user.role == User.PARENT:
                children = User.objects.filter(parent_relations__parent=user)
                attendance_records = Attendance.objects.filter(student__in=children, date=today_date).select_related('student', 'class_obj', 'school')
                logger.info(f"Родитель {user.username} запрашивает посещаемость своих детей на сегодня.")
            else:
                logger.warning(f"Пользователь {user.username} с неизвестной ролью пытается получить доступ к посещаемости.")
                return Response({"error": "У вас нет доступа к этому эндпоинту."},
                                status=status.HTTP_403_FORBIDDEN)

            serializer = AttendanceSerializer(attendance_records, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Ошибка при получении посещаемости для пользователя {user.username}: {e}")
            return Response({"error": "Не удалось получить посещаемость."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

    def perform_create(self, serializer):
        try:
            achievement = serializer.save()
            logger.info(f"Создано новое достижение: {achievement.name}")
        except Exception as e:
            logger.error(f"Ошибка при создании достижения: {e}")
            raise e


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
            queryset = UserProfile.objects.all().select_related('user').prefetch_related('achievements')
            logger.debug(f"Администратор {user.username} просматривает все профили пользователей.")
            return queryset
        else:
            queryset = UserProfile.objects.filter(user=user).select_related('user').prefetch_related('achievements')
            logger.debug(f"Пользователь {user.username} просматривает свой профиль.")
            return queryset

    def perform_create(self, serializer):
        try:
            user_profile = serializer.save()
            logger.info(f"Создан профиль для пользователя: {user_profile.user.username}")
        except Exception as e:
            logger.error(f"Ошибка при создании профиля для пользователя: {e}")
            raise e


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

    def list(self, request, *args, **kwargs):
        try:
            logger.info(f"Пользователь {request.user.username} запрашивает таблицу лидеров.")
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Ошибка при запросе таблицы лидеров: {e}")
            return Response({"error": "Не удалось получить таблицу лидеров."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
            queryset = Notification.objects.all().select_related('user')
            logger.debug(f"Администратор {user.username} просматривает все уведомления.")
            return queryset
        queryset = Notification.objects.filter(user=user).select_related('user')
        logger.debug(f"Пользователь {user.username} просматривает свои уведомления.")
        return queryset

    def perform_create(self, serializer):
        try:
            notification = serializer.save(user=self.request.user)
            logger.info(f"Пользователь {self.request.user.username} создал уведомление: {notification.message}")
        except Exception as e:
            logger.error(f"Ошибка при создании уведомления пользователем {self.request.user.username}: {e}")
            raise e


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Выход пользователя: удаление токена.
    """
    user = request.user
    try:
        token = Token.objects.get(user=user)
        token.delete()
        logger.info(f"Пользователь {user.username} вышел из системы. Токен удалён.")
        return Response({"success": "Токен успешно удалён."}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        logger.warning(f"Пользователь {user.username} попытался выйти, но токен не найден.")
        return Response({"error": "Токен не найден."}, status=status.HTTP_400_BAD_REQUEST)
