# main/views.py

import logging
import datetime
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.timezone import localtime, now
from django.conf import settings
from django.db.models import Prefetch, Sum, Count, Avg, Q
from django.core.cache import cache

from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import UserRateThrottle

from geopy.distance import geodesic  # For distance calculations

from .models import (
    SchoolClass, Subject, Schedule, Homework, SubmittedHomework,
    Grade, Attendance, Achievement, UserProfile,
    UserAchievement, Leaderboard, Notification, StudentTeacher
)
from .serializers import (
    UserSerializer, SchoolClassSerializer, SubjectSerializer, ScheduleSerializer,
    HomeworkSerializer, SubmittedHomeworkSerializer, GradeSerializer,
    AttendanceSerializer, AchievementSerializer, UserProfileSerializer,
    UserAchievementSerializer, LeaderboardSerializer, NotificationSerializer,
    UserRegistrationSerializer, StudentTeacherSerializer
)

User = get_user_model()

# Initialize logger
logger = logging.getLogger(__name__)

# Custom permission classes
class IsTeacher(permissions.BasePermission):
    """
    Permission only for teachers.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.TEACHER


class IsStudent(permissions.BasePermission):
    """
    Permission only for students.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.STUDENT


class IsParent(permissions.BasePermission):
    """
    Permission only for parents.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.PARENT


# Token expiration settings
TOKEN_EXPIRATION_TIME = datetime.timedelta(hours=24)


def token_is_expired(token):
    """
    Checks if the token has expired.
    """
    return timezone.now() > token.created + TOKEN_EXPIRATION_TIME


# Default paginator
class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserMeView(APIView):
    """
    View for retrieving information about the current user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            user_serializer = UserSerializer(user)
            try:
                user_profile = user.profile
                user_profile_serializer = UserProfileSerializer(user_profile)
            except UserProfile.DoesNotExist:
                user_profile_serializer = None
                logger.warning(f"User {user.username} does not have a UserProfile.")
            
            response_data = user_serializer.data
            if user_profile_serializer:
                response_data.update(user_profile_serializer.data)
            else:
                response_data.update({"profile": "Profile not found."})
            
            logger.info(f"User {user.username} retrieved their information.")
            return Response(response_data)
        except Exception as e:
            logger.error(f"Error processing /api/me/ request for user {request.user.username}: {e}")
            return Response({"error": "Failed to retrieve user information."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing users.
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
        Register a new user.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                token, created = Token.objects.get_or_create(user=user)
                logger.info(f"New user registered: {user.username}")
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                logger.error(f"Error registering user: {e}")
                return Response({"error": "Failed to register user."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Invalid registration data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomObtainAuthToken(ObtainAuthToken):
    """
    Custom ObtainAuthToken to add token expiration check. 
    """
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        if not created and token_is_expired(token):
            logger.info(f"Token for user {user.username} expired. Creating a new token.")
            token.delete()
            token = Token.objects.create(user=user)
        else:
            logger.info(f"Token retrieved for user {user.username}.")

        return Response({'token': token.key})


class SchoolClassViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing school classes.
    """
    queryset = SchoolClass.objects.all().prefetch_related('teachers', 'students', 'subjects')
    serializer_class = SchoolClassSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    ordering = ['name']

    def perform_create(self, serializer):
        try:
            school_class = serializer.save()
            logger.info(f"Created new class: {school_class.name}")
        except Exception as e:
            logger.error(f"Error creating class: {e}")
            raise e

    def get_queryset(self):
        """
        Optionally restricts the returned classes based on the user's role.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            queryset = SchoolClass.objects.filter(teachers=user).prefetch_related('teachers', 'students', 'subjects')
            logger.debug(f"Teacher {user.username} accessing their classes.")
            return queryset
        elif user.role == User.STUDENT:
            queryset = SchoolClass.objects.filter(students=user).prefetch_related('teachers', 'students', 'subjects')
            logger.debug(f"Student {user.username} accessing their classes.")
            return queryset
        elif user.role == User.PARENT:
            queryset = SchoolClass.objects.filter(students__parent_relations__parent=user).distinct().prefetch_related('teachers', 'students', 'subjects')
            logger.debug(f"Parent {user.username} accessing their children's classes.")
            return queryset
        else:
            logger.warning(f"User {user.username} with unknown role trying to access classes.")
            return SchoolClass.objects.none()


class SubjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing subjects.
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
            logger.info(f"Created new subject: {subject.name}")
        except Exception as e:
            logger.error(f"Error creating subject: {e}")
            raise e


class ScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing schedules.
    """
    queryset = Schedule.objects.select_related('school_class', 'subject', 'teacher').all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['school_class__name', 'subject__name', 'teacher__username']
    ordering_fields = ['weekday', 'start_time']
    ordering = ['weekday', 'start_time']

    def get_queryset(self):
        user = self.request.user
        logger.debug(f"Fetching schedules for user: {user.username} with role: {user.role}")

        if user.role == User.TEACHER:
            queryset = Schedule.objects.filter(teacher=user).select_related('school_class', 'subject', 'teacher')
            logger.debug(f"Teacher {user.username} schedules: {queryset}")
            return queryset
        elif user.role == User.STUDENT:
            class_objs = user.classes.all()
            queryset = Schedule.objects.filter(school_class__in=class_objs).select_related('school_class', 'subject', 'teacher')
            logger.debug(f"Student {user.username} schedules: {queryset}")
            return queryset
        elif user.role == User.PARENT:
            children = user.parent_relations.values_list('child', flat=True)
            class_objs = SchoolClass.objects.filter(students__in=children).distinct()
            queryset = Schedule.objects.filter(school_class__in=class_objs).select_related('school_class', 'subject', 'teacher')
            logger.debug(f"Parent {user.username} schedules: {queryset}")
            return queryset
        else:
            logger.warning(f"Unknown role for user: {user.username}")
            return Schedule.objects.none()


class HomeworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing homework.
    """
    queryset = Homework.objects.select_related('subject', 'school_class').all()
    serializer_class = HomeworkSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['subject__name', 'school_class__name', 'description']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['due_date']

    def perform_create(self, serializer):
        try:
            homework = serializer.save()
            logger.info(f"Created homework: {homework.description} for class {homework.school_class.name}")
        except Exception as e:
            logger.error(f"Error creating homework: {e}")
            raise e

    def get_queryset(self):
        """
        Optionally restricts the returned homework based on the user's role.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            queryset = Homework.objects.filter(subject__in=user.teaching_subjects.all()).select_related('subject', 'school_class')
            logger.debug(f"Teacher {user.username} accessing homework for their subjects.")
            return queryset
        elif user.role == User.STUDENT:
            queryset = Homework.objects.filter(school_class__in=user.classes.all()).select_related('subject', 'school_class')
            logger.debug(f"Student {user.username} accessing homework for their classes.")
            return queryset
        elif user.role == User.PARENT:
            children = user.parent_relations.values_list('child', flat=True)
            queryset = Homework.objects.filter(school_class__students__in=children).distinct().select_related('subject', 'school_class')
            logger.debug(f"Parent {user.username} accessing homework for their children.")
            return queryset
        else:
            logger.warning(f"User {user.username} with unknown role trying to access homework.")
            return Homework.objects.none()


class SubmittedHomeworkViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing submitted homework.
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
        - Teachers see all submitted homework for their subjects.
        - Students see only their own submissions.
        - Parents see their children's submissions.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            queryset = SubmittedHomework.objects.filter(homework__teacher=user).select_related('homework', 'student')
            logger.debug(f"Teacher {user.username} accessing submitted homework for their subjects.")
            return queryset
        elif user.role == User.STUDENT:
            queryset = SubmittedHomework.objects.filter(student=user).select_related('homework', 'student')
            logger.debug(f"Student {user.username} accessing their submitted homework.")
            return queryset
        elif user.role == User.PARENT:
            children_ids = user.parent_relations.values_list('child__id', flat=True)
            queryset = SubmittedHomework.objects.filter(student__id__in=children_ids).select_related('homework', 'student')
            logger.debug(f"Parent {user.username} accessing submitted homework for their children.")
            return queryset
        else:
            logger.warning(f"User {user.username} with unknown role trying to access submitted homework.")
            return SubmittedHomework.objects.none()

    def perform_create(self, serializer):
        try:
            submitted_homework = serializer.save(student=self.request.user)
            logger.info(f"Student {self.request.user.username} submitted homework: {submitted_homework.homework.description}")
        except Exception as e:
            logger.error(f"Error submitting homework by student {self.request.user.username}: {e}")
            raise e

    def perform_update(self, serializer):
        try:
            submitted_homework = serializer.save()
            logger.info(f"Student {self.request.user.username} updated submitted homework: {submitted_homework.homework.description}")
        except Exception as e:
            logger.error(f"Error updating submitted homework by student {self.request.user.username}: {e}")
            raise e


class GradeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing grades.
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
        - Teachers see grades they've assigned.
        - Students see their own grades.
        - Parents see their children's grades.
        """
        user = self.request.user
        if user.role == User.TEACHER:
            queryset = Grade.objects.filter(teacher=user).select_related('student', 'subject', 'teacher')
            logger.debug(f"Teacher {user.username} accessing their assigned grades.")
            return queryset
        elif user.role == User.STUDENT:
            queryset = Grade.objects.filter(student=user).select_related('student', 'subject', 'teacher')
            logger.debug(f"Student {user.username} accessing their grades.")
            return queryset
        elif user.role == User.PARENT:
            children_ids = user.parent_relations.values_list('child__id', flat=True)
            queryset = Grade.objects.filter(student__id__in=children_ids).select_related('student', 'subject', 'teacher')
            logger.debug(f"Parent {user.username} accessing grades for their children.")
            return queryset
        else:
            logger.warning(f"User {user.username} with unknown role trying to access grades.")
            return Grade.objects.none()

    def perform_create(self, serializer):
        try:
            grade = serializer.save(teacher=self.request.user)
            logger.info(f"Teacher {self.request.user.username} assigned grade {grade.grade} to student {grade.student.username} for subject {grade.subject.name}")
        except Exception as e:
            logger.error(f"Error assigning grade by teacher {self.request.user.username}: {e}")
            raise e


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing attendance records.
    Includes custom actions for marking attendance based on GPS coordinates.
    """
    queryset = Attendance.objects.select_related('student', 'school_class', 'school').all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['student__username', 'school_class__name', 'status']
    ordering_fields = ['date', 'status']
    ordering = ['-date']

    def get_queryset(self):
        """
        - Teachers see attendance for their classes.
        - Students see their own attendance.
        - Parents see their children's attendance.
        """
        user = self.request.user

        if user.role == User.TEACHER:
            teacher_classes = SchoolClass.objects.filter(teachers=user)
            queryset = Attendance.objects.filter(school_class__in=teacher_classes).select_related('student', 'school_class', 'school')
            logger.debug(f"Teacher {user.username} accessing attendance for their classes.")
            return queryset
        elif user.role == User.STUDENT:
            queryset = Attendance.objects.filter(student=user).select_related('student', 'school_class', 'school')
            logger.debug(f"Student {user.username} accessing their attendance.")
            return queryset
        elif user.role == User.PARENT:
            children_ids = user.parent_relations.values_list('child__id', flat=True)
            queryset = Attendance.objects.filter(student__id__in=children_ids).select_related('student', 'school_class', 'school')
            logger.debug(f"Parent {user.username} accessing attendance for their children.")
            return queryset
        else:
            logger.warning(f"User {user.username} with unknown role trying to access attendance.")
            return Attendance.objects.none()

    @action(detail=False, methods=['post'], permission_classes=[IsStudent], throttle_classes=[UserRateThrottle])
    def mark_attendance(self, request):
        """
        Allows a student to mark their attendance based on GPS coordinates.
        Implements throttling to prevent abuse.
        """
        user = request.user

        try:
            # Get the user's school
            school = user.school
            if not school:
                logger.warning(f"Student {user.username} does not have an assigned school.")
                return Response({"error": "User does not have an assigned school."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Get coordinates from the request
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            if not latitude or not longitude:
                logger.warning(f"Student {user.username} submitted incomplete coordinates for attendance.")
                return Response({"error": "Latitude and longitude are required."},
                                status=status.HTTP_400_BAD_REQUEST)

            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            logger.warning(f"Student {user.username} submitted invalid coordinates: latitude={latitude}, longitude={longitude}")
            return Response({"error": "Invalid latitude or longitude format."},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error processing coordinates for student {user.username}: {e}")
            return Response({"error": "Failed to process coordinates."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Calculate distance to the school
            student_coords = (latitude, longitude)
            school_coords = (float(school.latitude), float(school.longitude))
            distance = geodesic(student_coords, school_coords).kilometers

            # Determine attendance status
            proximity_radius = 0.1  # 100 meters
            status_value = 'present' if distance <= proximity_radius else 'absent'

            # Get the student's class
            class_obj = user.classes.first()
            if not class_obj:
                logger.warning(f"Student {user.username} is not assigned to any class.")
                return Response({"error": "Student is not assigned to any class."},
                                status=status.HTTP_400_BAD_REQUEST)

            # Create or update attendance record for today
            attendance, created = Attendance.objects.update_or_create(
                student=user,
                date=localtime(now()).date(),
                defaults={
                    'school_class': class_obj,
                    'latitude': latitude,
                    'longitude': longitude,
                    'status': status_value,
                }
            )

            if created:
                logger.info(f"Student {user.username} marked attendance as {'present' if status_value == 'present' else 'absent'}.")
            else:
                logger.info(f"Student {user.username} updated attendance to {'present' if status_value == 'present' else 'absent'}.")
            
            # Invalidate the leaderboard cache since attendance has changed
            cache.delete('leaderboard_xp_cache')
            cache.delete('leaderboard_attendance_cache')
            cache.delete('leaderboard_grades_cache')
            logger.info("Leaderboard caches invalidated due to attendance update.")

            return Response(AttendanceSerializer(attendance).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error marking attendance for student {user.username}: {e}")
            return Response({"error": "Failed to mark attendance."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def today(self, request):
        """
        Retrieve today's attendance records for the current user.
        """
        user = request.user
        today_date = localtime(now()).date()

        try:
            if user.role == User.TEACHER:
                teacher_classes = SchoolClass.objects.filter(teachers=user)
                attendance_records = Attendance.objects.filter(
                    school_class__in=teacher_classes,
                    date=today_date
                ).select_related('student', 'school_class', 'school')
                logger.info(f"Teacher {user.username} requested today's attendance for their classes.")
            elif user.role == User.STUDENT:
                attendance_records = Attendance.objects.filter(student=user, date=today_date).select_related('student', 'school_class', 'school')
                logger.info(f"Student {user.username} requested their attendance for today.")
            elif user.role == User.PARENT:
                children_ids = user.parent_relations.values_list('child__id', flat=True)
                attendance_records = Attendance.objects.filter(student__id__in=children_ids, date=today_date).select_related('student', 'school_class', 'school')
                logger.info(f"Parent {user.username} requested today's attendance for their children.")
            else:
                logger.warning(f"User {user.username} with unknown role attempted to access today's attendance.")
                return Response({"error": "You do not have access to this endpoint."},
                                status=status.HTTP_403_FORBIDDEN)

            serializer = AttendanceSerializer(attendance_records, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving today's attendance for user {user.username}: {e}")
            return Response({"error": "Failed to retrieve attendance."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AchievementViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing achievements.
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
            logger.info(f"Created new achievement: {achievement.name}")
        except Exception as e:
            logger.error(f"Error creating achievement: {e}")
            raise e


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user profiles.
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
            logger.debug(f"Admin {user.username} accessing all user profiles.")
            return queryset
        else:
            queryset = UserProfile.objects.filter(user=user).select_related('user').prefetch_related('achievements')
            logger.debug(f"User {user.username} accessing their own profile.")
            return queryset

    def perform_create(self, serializer):
        try:
            user_profile = serializer.save()
            logger.info(f"Created profile for user: {user_profile.user.username}")
        except Exception as e:
            logger.error(f"Error creating profile for user: {e}")
            raise e


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnly ViewSet for displaying leaderboards based on different metrics.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user_profile__user__username']
    ordering_fields = ['rank']
    ordering = ['rank']
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        """
        Returns different querysets based on the 'metric' parameter:
        - 'xp': Leaderboard based on XP.
        - 'attendance': Leaderboard based on attendance.
        - 'grades': Leaderboard based on grades.
        """
        metric = self.request.query_params.get('metric', 'xp')
        logger.debug(f"Fetching leaderboard for metric: {metric}")

        if metric == 'xp':
            queryset = UserProfile.objects.annotate(
                total_xp=Sum('userachievement__xp')
            ).order_by('-total_xp')[:100]  # Top 100
            return queryset
        elif metric == 'attendance':
            queryset = UserProfile.objects.annotate(
                total_attendance=Count('attendance', filter=Q(attendance__status='present'))
            ).order_by('-total_attendance')[:100]
            return queryset
        elif metric == 'grades':
            queryset = UserProfile.objects.annotate(
                average_grade=Avg('grade__grade')
            ).order_by('-average_grade')[:100]
            return queryset
        else:
            logger.warning(f"Invalid metric requested: {metric}. Defaulting to XP.")
            queryset = UserProfile.objects.annotate(
                total_xp=Sum('userachievement__xp')
            ).order_by('-total_xp')[:100]
            return queryset

    def list(self, request, *args, **kwargs):
        """
        Override list method to implement caching based on metric.
        """
        metric = request.query_params.get('metric', 'xp')
        cache_key = f'leaderboard_{metric}_cache'
        leaderboard_data = cache.get(cache_key)

        if leaderboard_data is None:
            try:
                queryset = self.get_queryset()
                serializer = UserProfileSerializer(queryset, many=True)
                leaderboard_data = serializer.data
                cache.set(cache_key, leaderboard_data, 300)  # Cache for 5 minutes
                logger.info(f"Leaderboard data cached for metric: {metric}")
            except Exception as e:
                logger.error(f"Error retrieving leaderboard for metric {metric}: {e}")
                return Response({"error": "Failed to retrieve leaderboard."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.info(f"Leaderboard data retrieved from cache for metric: {metric}")

        # Enhance data with rank
        for index, user_data in enumerate(leaderboard_data, start=1):
            user_data['rank'] = index

        return Response(leaderboard_data, status=status.HTTP_200_OK)


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications.
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
        - Admins see all notifications.
        - Other users see only their own notifications.
        """
        user = self.request.user
        if user.is_staff:
            queryset = Notification.objects.all().select_related('user')
            logger.debug(f"Admin {user.username} accessing all notifications.")
            return queryset
        queryset = Notification.objects.filter(user=user).select_related('user')
        logger.debug(f"User {user.username} accessing their notifications.")
        return queryset

    def perform_create(self, serializer):
        try:
            notification = serializer.save(user=self.request.user)
            logger.info(f"User {self.request.user.username} created a notification: {notification.message}")
        except Exception as e:
            logger.error(f"Error creating notification for user {self.request.user.username}: {e}")
            raise e


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    User logout: delete the token.
    """
    user = request.user
    try:
        token = Token.objects.get(user=user)
        token.delete()
        logger.info(f"User {user.username} logged out. Token deleted.")
        return Response({"success": "Token successfully deleted."}, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        logger.warning(f"User {user.username} attempted to logout but no token was found.")
        return Response({"error": "Token not found."}, status=status.HTTP_400_BAD_REQUEST)
