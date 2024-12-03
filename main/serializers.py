# serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Class, Subject, Schedule, Homework, SubmittedHomework,
    Grade, Attendance, Achievement, UserProfile,
    UserAchievement, Leaderboard, Notification
)

# Получаем кастомную модель пользователя
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели User.
    Используется для отображения информации о пользователе.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def create(self, validated_data):
        """
        Метод для создания нового пользователя с хэшированным паролем.
        """
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # Хэшируем пароль
        user.save()
        return user


class ClassSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Class.
    """
    class Meta:
        model = Class
        fields = ['id', 'name']


class SubjectSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Subject.
    """
    class Meta:
        model = Subject
        fields = ['id', 'name']


class ScheduleSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Schedule.
    Включает вложенные сериализаторы для класса, предмета и учителя.
    """
    class_obj = ClassSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    teacher = UserSerializer(read_only=True)

    class Meta:
        model = Schedule
        fields = ['id', 'class_obj', 'subject', 'teacher', 'weekday', 'start_time', 'end_time']


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Homework.
    Включает вложенные сериализаторы для предмета и класса.
    """
    subject = SubjectSerializer(read_only=True)
    class_obj = ClassSerializer(read_only=True)

    class Meta:
        model = Homework
        fields = ['id', 'subject', 'class_obj', 'description', 'due_date', 'created_at']


class SubmittedHomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели SubmittedHomework.
    Включает вложенные сериализаторы для домашнего задания и студента.
    """
    homework = HomeworkSerializer(read_only=True)
    student = UserSerializer(read_only=True)

    class Meta:
        model = SubmittedHomework
        fields = [
            'id', 'homework', 'student', 'submission_file',
            'submitted_at', 'status', 'grade', 'feedback'
        ]


class GradeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Grade.
    Включает вложенные сериализаторы для студента, предмета и учителя.
    """
    student = UserSerializer(read_only=True)
    subject = SubjectSerializer(read_only=True)
    teacher = UserSerializer(read_only=True)

    class Meta:
        model = Grade
        fields = ['id', 'student', 'subject', 'grade', 'date', 'teacher', 'comments']


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Attendance.
    Включает вложенные сериализаторы для студента и класса.
    """
    student = UserSerializer(read_only=True)
    class_obj = ClassSerializer(read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'class_obj', 'date', 'status', 'notes']


class AchievementSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Achievement.
    """
    class Meta:
        model = Achievement
        fields = ['id', 'name', 'description', 'icon', 'xp_reward']


class UserAchievementSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели UserAchievement.
    Включает вложенные сериализаторы для профиля пользователя и достижения.
    """
    user_profile = serializers.StringRelatedField()
    achievement = AchievementSerializer(read_only=True)

    class Meta:
        model = UserAchievement
        fields = ['id', 'user_profile', 'achievement', 'achieved_at']


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели UserProfile.
    Включает вложенные сериализаторы для пользователя и достижений.
    """
    user = UserSerializer(read_only=True)
    achievements = AchievementSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'xp', 'level', 'achievements']


class LeaderboardSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Leaderboard.
    Включает вложенные сериализаторы для профиля пользователя.
    """
    user_profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = Leaderboard
        fields = ['id', 'user_profile', 'rank']


class NotificationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Notification.
    Включает вложенный сериализатор для пользователя.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'created_at', 'is_read']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации новых пользователей.
    Автоматически создаёт профиль пользователя.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default=User.STUDENT)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'password']

    def create(self, validated_data):
        """
        Создаёт нового пользователя с хэшированным паролем и автоматически создаёт профиль.
        """
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # Хэшируем пароль
        user.save()
        # Профиль создаётся автоматически через сигнал
        return user