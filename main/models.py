# main/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import uuid

# -----------------------
# User model
# -----------------------
class User(AbstractUser):
    """
    Кастомная модель пользователя, расширяющая AbstractUser.
    """
    STUDENT = 'student'
    TEACHER = 'teacher'
    PARENT = 'parent'

    ROLE_CHOICES = [
        (STUDENT, 'Студент'),
        (TEACHER, 'Учитель'),
        (PARENT, 'Родитель'),
    ]

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=STUDENT,
        help_text="Роль пользователя: студент, учитель или родитель."
    )
    school = models.ForeignKey(
        'School',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Школа пользователя. Только для учителей и студентов."
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# -----------------------
# School model
# -----------------------
class School(models.Model):
    """
    Модель школы.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Название школы.",
        default="Unnamed School"
    )
    address = models.CharField(
        max_length=500,
        help_text="Адрес школы.",
        default="No Address Provided"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Контактный телефон школы."
    )
    email = models.EmailField(
        unique=True,
        help_text="Электронная почта школы.",
        default="admin@school.com"
    )
    website = models.URLField(
        blank=True,
        null=True,
        help_text="Веб-сайт школы."
    )
    established_date = models.DateField(
        blank=True,
        null=True,
        help_text="Дата основания школы."
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Широта школы."
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Долгота школы."
    )

    def __str__(self):
        return self.name


# -----------------------
# Achievement model
# -----------------------
class Achievement(models.Model):
    """
    Модель достижений для системы геймификации.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Название достижения.",
        default="Unnamed Achievement"
    )
    description = models.TextField(
        help_text="Описание достижения.",
        default="No description provided."
    )
    icon = models.ImageField(
        upload_to='achievements/icons/',
        null=True,
        blank=True,
        help_text="Иконка достижения."
    )
    xp_reward = models.PositiveIntegerField(
        default=0,
        help_text="Количество XP, даваемое за достижение."
    )

    def __str__(self):
        return self.name


# -----------------------
# UserProfile model
# -----------------------
class UserProfile(models.Model):
    """
    Модель профиля пользователя, содержащая информацию для геймификации.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    xp = models.PositiveIntegerField(
        default=0,
        help_text="Накопленные очки XP."
    )
    school_class = models.ForeignKey(
        # you could also reference "SchoolClass" as a string here if needed
        'SchoolClass',
        on_delete=models.CASCADE,
        related_name='profile',
        help_text="Класс, для связи с учителем",
        null=True,  # Allow nulls temporarily
        blank=True,
    )
    level = models.PositiveIntegerField(
        default=1,
        help_text="Текущий уровень пользователя."
    )
    achievements = models.ManyToManyField(
        Achievement,
        through='UserAchievement',
        related_name='users',
        help_text="Достижения пользователя."
    )

    def __str__(self):
        return f"{self.user.username} - Профиль"


# -----------------------
# UserAchievement model
# -----------------------
class UserAchievement(models.Model):
    """
    Промежуточная модель для связи пользователей с достижениями.
    """
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='user_achievements',
        help_text="Профиль пользователя."
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='user_achievements',
        help_text="Достижение."
    )
    achieved_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата и время достижения."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user_profile', 'achievement'], name='unique_user_achievement')
        ]

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.achievement.name}"


# -----------------------
# Leaderboard model
# -----------------------
class Leaderboard(models.Model):
    """
    Модель таблицы лидеров для отображения рейтинга пользователей по XP.
    """
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name='leaderboard_entry',
        help_text="Профиль пользователя."
    )
    rank = models.PositiveIntegerField(
        unique=True,
        help_text="Место в таблице лидеров.",
        default=1
    )

    def __str__(self):
        return f"{self.user_profile.user.username} - Rank {self.rank}"


# -----------------------
# SchoolClass model
# -----------------------
class SchoolClass(models.Model):
    """
    Модель класса.
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Название класса, например, 5А."
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='classes',
        help_text="Школа, к которой принадлежит класс."
    )
    # Use a string reference to avoid the 'NameError' if the model is declared later
    user_profile = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='classes',
        help_text="Профиль пользователя (например, классный руководитель)."
    )
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='classes',
        limit_choices_to={'role': User.STUDENT},
        help_text="Студенты, принадлежащие к классу."
    )
    teachers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teaching_classes',
        limit_choices_to={'role': User.TEACHER},
        help_text="Учителя, ведущие класс."
    )
    subjects = models.ManyToManyField(
        'Subject',
        related_name='classes',
        help_text="Предметы, преподаваемые в классе."
    )

    def __str__(self):
        return self.name


# -----------------------
# Subject model
# -----------------------
class Subject(models.Model):
    """
    Модель предмета.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Название предмета.",
        default="Unnamed Subject"
    )

    def __str__(self):
        return self.name


# -----------------------
# StudentTeacher model
# -----------------------
class StudentTeacher(models.Model):
    """
    Модель для связи студентов с учителями (например, наставники).
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_teacher_relations',
        limit_choices_to={'role': User.STUDENT},
        help_text="Студент."
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_student_relations',
        limit_choices_to={'role': User.TEACHER},
        help_text="Учитель."
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='student_teacher_relations',
        help_text="Класс, в котором установлены отношения.",
        null=True,
        blank=True,
    )
    relationship = models.CharField(
        max_length=50,
        help_text="Тип отношений, например, наставник."
    )
    established_date = models.DateField(
        default=timezone.now,
        help_text="Дата установления отношений."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'teacher', 'school_class'], name='unique_student_teacher_class')
        ]

    def __str__(self):
        return f"{self.teacher.username} -> {self.student.username} ({self.relationship})"


# -----------------------
# ParentChild model
# -----------------------
class ParentChild(models.Model):
    """
    Модель для связи родителей с их детьми (студентами).
    """
    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='children_relations',
        limit_choices_to={'role': User.PARENT},
        help_text="Родитель."
    )
    child = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parent_relations',
        limit_choices_to={'role': User.STUDENT},
        help_text="Ребёнок."
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='parent_child_relations',
        help_text="Класс ребенка.",
        default=1,  # Make sure a SchoolClass with ID=1 exists!
        null=False,
        blank=False
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['parent', 'child', 'school_class'], name='unique_parent_child_class')
        ]

    def __str__(self):
        return f"{self.parent.username} -> {self.child.username} in {self.school_class.name}"


# -----------------------
# Schedule model
# -----------------------
class Schedule(models.Model):
    """
    Модель расписания занятий.
    """
    WEEKDAYS = [
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
        (7, 'Воскресенье'),
    ]

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="Класс, для которого расписание.",
        null=True,
        blank=True,
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="Предмет."
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': User.TEACHER},
        related_name='schedules',
        help_text="Учитель, проводящий занятие."
    )
    weekday = models.IntegerField(
        choices=WEEKDAYS,
        help_text="День недели проведения занятия.",
        default=1
    )
    start_time = models.TimeField(
        help_text="Время начала занятия."
    )
    end_time = models.TimeField(
        help_text="Время окончания занятия."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['school_class', 'subject', 'weekday', 'start_time'], name='unique_schedule')
        ]
        ordering = ['school_class', 'weekday', 'start_time']

    def __str__(self):
        return f"{self.school_class} - {self.subject} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


# -----------------------
# Homework model
# -----------------------
class Homework(models.Model):
    """
    Модель домашнего задания.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Уникальный идентификатор домашнего задания."
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='homeworks',
        help_text="Предмет, к которому относится задание."
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='homeworks',
        help_text="Класс, для которого задано домашнее задание.",
        default=1,  # Make sure a SchoolClass with ID=1 exists!
        null=False,
        blank=False
    )
    description = models.TextField(
        help_text="Описание домашнего задания.",
        default="No description provided."
    )
    due_date = models.DateTimeField(
        help_text="Срок сдачи задания."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата и время создания задания."
    )

    def __str__(self):
        return f"Домашнее задание по {self.subject} для {self.school_class}"


# -----------------------
# SubmittedHomework model
# -----------------------
class SubmittedHomework(models.Model):
    """
    Модель отправленного домашнего задания студентом.
    """
    STATUS_CHOICES = [
        ('submitted', 'Отправлено'),
        ('graded', 'Оценено'),
    ]

    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name='submitted_homeworks',
        help_text="Домашнее задание."
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': User.STUDENT},
        related_name='submitted_homeworks',
        help_text="Студент, отправивший задание."
    )
    submission_file = models.FileField(
        upload_to='homeworks/submissions/',
        help_text="Файл с выполненным заданием."
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата и время отправки задания."
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='submitted',
        help_text="Статус выполнения задания."
    )
    grade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Оценка за задание."
    )
    feedback = models.TextField(
        null=True,
        blank=True,
        help_text="Обратная связь от учителя."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['homework', 'student'], name='unique_homework_submission')
        ]

    def __str__(self):
        return f"{self.student} - {self.homework}"


# -----------------------
# Grade model
# -----------------------
class Grade(models.Model):
    """
    Модель оценок для студентов.
    """
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': User.STUDENT},
        related_name='grades',
        help_text="Студент."
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='grades',
        help_text="Предмет."
    )
    grade = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        help_text="Оценка студента."
    )
    date = models.DateField(
        default=timezone.now,
        help_text="Дата выставления оценки."
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': User.TEACHER},
        related_name='assigned_grades',
        help_text="Учитель, выставивший оценку."
    )
    comments = models.TextField(
        null=True,
        blank=True,
        help_text="Комментарии учителя к оценке."
    )

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.grade}"


# -----------------------
# Attendance model
# -----------------------
class Attendance(models.Model):
    """
    Модель посещаемости студентов.
    """
    STATUS_CHOICES = [
        ('present', 'Присутствует'),
        ('absent', 'Отсутствует'),
        ('excused', 'По уважительной причине'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': User.STUDENT},
        related_name='attendances',
        help_text="Студент."
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text="Класс студента.",
        default=1,  # Make sure a SchoolClass with ID=1 exists!
        null=False,
        blank=False
    )
    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text="Школа, к которой относится посещаемость.",
        null=True,
        blank=True,
    )
    date = models.DateField(
        default=timezone.now,
        help_text="Дата посещаемости."
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='present',
        help_text="Статус посещаемости."
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Примечания к посещаемости."
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'date'], name='unique_attendance')
        ]

    def __str__(self):
        return f"{self.student} - {self.date} - {self.get_status_display()}"


# -----------------------
# Notification model
# -----------------------
class Notification(models.Model):
    """
    Модель уведомлений для пользователей.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Пользователь, получающий уведомление."
    )
    message = models.TextField(
        help_text="Текст уведомления.",
        default="No message."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата и время создания уведомления."
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Прочитано ли уведомление."
    )

    def __str__(self):
        return f"Уведомление для {self.user.username} - {'Прочитано' if self.is_read else 'Не прочитано'}"
