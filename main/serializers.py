# serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    SchoolClass, Subject, Schedule, Homework, SubmittedHomework,
    Grade, Attendance, Achievement, UserProfile,
    UserAchievement, Leaderboard, Notification, StudentTeacher
)
from geopy.distance import geodesic

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


class SchoolClassSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели SchoolClass.
    """
    teachers = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(role=User.TEACHER),
        required=False
    )
    students = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.filter(role=User.STUDENT),
        required=False
    )
    subjects = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Subject.objects.all(),
        required=False
    )

    class Meta:
        model = SchoolClass
        fields = ['id', 'name', 'teachers', 'students', 'subjects']


class SubjectSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Subject.
    """
    class Meta:
        model = Subject
        fields = ['id', 'name']


class StudentTeacherSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели StudentTeacher.
    """
    student = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.STUDENT)
    )
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.TEACHER)
    )

    class Meta:
        model = StudentTeacher
        fields = ['id', 'student', 'teacher', 'relationship', 'established_date']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=StudentTeacher.objects.all(),
                fields=['student', 'teacher'],
                message="This student-teacher relationship already exists."
            )
        ]


class ScheduleSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Schedule.
    Включает вложенные сериализаторы для класса, предмета и учителя.
    """
    school_class = serializers.PrimaryKeyRelatedField(
        queryset=SchoolClass.objects.all()
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all()
    )
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.TEACHER)
    )

    class Meta:
        model = Schedule
        fields = ['id', 'school_class', 'subject', 'teacher', 'weekday', 'start_time', 'end_time']

    def to_representation(self, instance):
        """
        Customize representation to include nested data.
        """
        representation = super().to_representation(instance)
        representation['school_class'] = SchoolClassSerializer(instance.school_class).data
        representation['subject'] = SubjectSerializer(instance.subject).data
        representation['teacher'] = UserSerializer(instance.teacher).data
        return representation


class HomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Homework.
    Включает вложенные сериализаторы для предмета и класса.
    """
    school_class = serializers.PrimaryKeyRelatedField(
        queryset=SchoolClass.objects.all()
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all()
    )

    class Meta:
        model = Homework
        fields = ['id', 'subject', 'school_class', 'description', 'due_date', 'created_at']

    def to_representation(self, instance):
        """
        Customize representation to include nested data.
        """
        representation = super().to_representation(instance)
        representation['subject'] = SubjectSerializer(instance.subject).data
        representation['school_class'] = SchoolClassSerializer(instance.school_class).data
        return representation


class SubmittedHomeworkSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели SubmittedHomework.
    Включает вложенные сериализаторы для домашнего задания и студента.
    """
    homework = serializers.PrimaryKeyRelatedField(
        queryset=Homework.objects.all()
    )
    student = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.STUDENT)
    )

    class Meta:
        model = SubmittedHomework
        fields = [
            'id', 'homework', 'student', 'submission_file',
            'submitted_at', 'status', 'grade', 'feedback'
        ]

    def to_representation(self, instance):
        """
        Customize representation to include nested data.
        """
        representation = super().to_representation(instance)
        representation['homework'] = HomeworkSerializer(instance.homework).data
        representation['student'] = UserSerializer(instance.student).data
        return representation


class GradeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Grade.
    Включает вложенные сериализаторы для студента, предмета и учителя.
    """
    student = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.STUDENT)
    )
    subject = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all()
    )
    teacher = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.TEACHER)
    )

    class Meta:
        model = Grade
        fields = ['id', 'student', 'subject', 'grade', 'date', 'teacher', 'comments']

    def to_representation(self, instance):
        """
        Customize representation to include nested data.
        """
        representation = super().to_representation(instance)
        representation['student'] = UserSerializer(instance.student).data
        representation['subject'] = SubjectSerializer(instance.subject).data
        representation['teacher'] = UserSerializer(instance.teacher).data
        return representation


class AttendanceSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Attendance.
    Включает вложенные сериализаторы для студента и класса.
    """
    student = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.STUDENT)
    )
    school_class = serializers.PrimaryKeyRelatedField(
        queryset=SchoolClass.objects.all()
    )

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'school_class', 'date', 'status', 'latitude', 'longitude', 'notes']

    def validate(self, data):
        """
        Validate that latitude and longitude are provided if attendance is being marked.
        """
        request = self.context.get('request')
        if 'latitude' in data and 'longitude' in data:
            school = request.user.school
            if not school or not school.latitude or not school.longitude:
                raise serializers.ValidationError("School coordinates are not set for this user.")
            # Validate proximity to the school (e.g., within 100 meters)
            valid = self.is_within_school_proximity(
                data['latitude'], data['longitude'], school.latitude, school.longitude
            )
            data['status'] = 'present' if valid else 'absent'
        return data

    def is_within_school_proximity(self, lat1, lon1, lat2, lon2, radius=0.1):
        """
        Check if the distance between two coordinates is within a given radius (default: ~100 meters).
        """
        student_coords = (lat1, lon1)
        school_coords = (lat2, lon2)
        distance = geodesic(student_coords, school_coords).kilometers
        return distance <= radius

    def to_representation(self, instance):
        """
        Customize representation to include nested data.
        """
        representation = super().to_representation(instance)
        representation['student'] = UserSerializer(instance.student).data
        representation['school_class'] = SchoolClassSerializer(instance.school_class).data
        return representation


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
    user_profile = serializers.PrimaryKeyRelatedField(
        queryset=UserProfile.objects.all()
    )
    achievement = serializers.PrimaryKeyRelatedField(
        queryset=Achievement.objects.all()
    )

    class Meta:
        model = UserAchievement
        fields = ['id', 'user_profile', 'achievement', 'achieved_at']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=UserAchievement.objects.all(),
                fields=['user_profile', 'achievement'],
                message="This achievement is already assigned to the user."
            )
        ]

    def to_representation(self, instance):
        """
        Customize representation to include nested data.
        """
        representation = super().to_representation(instance)
        representation['user_profile'] = UserProfileSerializer(instance.user_profile).data
        representation['achievement'] = AchievementSerializer(instance.achievement).data
        return representation


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
