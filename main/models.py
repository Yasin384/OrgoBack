from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
import uuid
from decimal import Decimal
# Модель школы
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

    def __str__(self):
        return self.name


# Кастомная модель пользователя с различными ролями
class User(AbstractUser):
    """
    Кастомная модель пользователя, расширяющая AbstractUser.
    Добавляет поле role для определения роли пользователя и связь со школой.
    """
    # Определяем возможные роли
    STUDENT = 'student'
    TEACHER = 'teacher'
    PARENT = 'parent'

    ROLE_CHOICES = [
        (STUDENT, 'Студент'),
        (TEACHER, 'Учитель'),
        (PARENT, 'Родитель'),
    ]

    # Поле для хранения роли пользователя
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=STUDENT,
        help_text="Роль пользователя: студент, учитель или родитель."
    )

    # Связь со школой (только для учителей и студентов)
    school = models.ForeignKey(
        School,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        help_text="Школа пользователя. Только для учителей и студентов."
    )

    # Дополнительное поле имени с значением по умолчанию
    name = models.CharField(
        max_length=255,
        default='Guest',
        help_text="Имя пользователя."
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Class(models.Model):
    name = models.CharField(
        max_length=100,  # Увеличиваем максимальную длину до 100 символов
        unique=True,
        help_text="Название класса, например, 5А."
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

    def __str__(self):
        return self.name


# Модель предмета, например, математика, русский язык и т.д.
class Subject(models.Model):
    """
    Модель предмета, например, математика, русский язык и т.д.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Название предмета.",
        default="Unnamed Subject"
    )

    def __str__(self):
        return self.name


# Модель расписания занятий
class Schedule(models.Model):
    """
    Модель расписания занятий.
    Связывает класс, предмет, учителя и время проведения.
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

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="Класс, для которого расписание."
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
        default=1  # Значение по умолчанию: Понедельник
    )
    start_time = models.TimeField(
        help_text="Время начала занятия.",
        default=timezone.now
    )
    end_time = models.TimeField(
        help_text="Время окончания занятия.",
        default=timezone.now
    )

    class Meta:
        unique_together = ('class_obj', 'subject', 'weekday', 'start_time')
        ordering = ['class_obj', 'weekday', 'start_time']

    def __str__(self):
        return f"{self.class_obj} - {self.subject} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


# Модель домашнего задания
class Homework(models.Model):
    """
    Модель домашнего задания.
    Связывает предмет, класс, школу, описание задания и срок сдачи.
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
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='homeworks',
        help_text="Класс, для которого задано домашнее задание."
    )
    
    description = models.TextField(
        help_text="Описание домашнего задания.",
        default="No description provided."
    )
    due_date = models.DateTimeField(
        help_text="Срок сдачи задания.",
        default=timezone.now
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Дата и время создания задания."
    )

    def __str__(self):
        return f"Домашнее задание по {self.subject} для {self.class_obj}"


# Модель отправленного домашнего задания
class SubmittedHomework(models.Model):
    """
    Модель отправленного домашнего задания студентом.
    Связывает домашнее задание, студента, файл и статус.
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
        help_text="Файл с выполненным заданием.",
        default='homeworks/submissions/default_submission.txt'
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
        help_text="Обратная связь от учителя.",
        default=""
    )

    class Meta:
        unique_together = ('homework', 'student')

    def __str__(self):
        return f"{self.student} - {self.homework}"


# Модель оценок (Grades)
class Grade(models.Model):
    """
    Модель оценок для хранения оценок студентов по различным категориям.
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
        help_text="Оценка студента.",
        default=0.0
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
        help_text="Комментарии учителя к оценке.",
        default=""
    )

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.grade}"


# Модель учёта посещаемости
class Attendance(models.Model):
    """
    Модель учёта посещаемости студентов.
    Связывает студента, класс, школу, дату и статус посещаемости.
    """
    STATUS_CHOICES = [
        ('present', 'Присутствует'),
        ('absent', 'Отсутствует'),
        ('excused', 'По уважительной причине'),
    ]
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True, 
        help_text="Широта (latitude) для GPS-отметки посещаемости."
    )
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True,
        help_text="Долгота (longitude) для GPS-отметки посещаемости."
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': User.STUDENT},
        related_name='attendances',
        help_text="Студент."
    )
    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name='attendances',
        help_text="Класс студента."
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
        help_text="Дата посещаемости.",
        default=timezone.now
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
        help_text="Примечания к посещаемости.",
        default=""
    )

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        return f"{self.student} - {self.date} - {self.get_status_display()}"


# Модель связи родитель-ученик
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

    class Meta:
        unique_together = ('parent', 'child')

    def __str__(self):
        return f"{self.parent.username} -> {self.child.username}"


# Модель достижений
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
        help_text="Иконка достижения.",
        default='achievements/icons/default_icon.png'
    )
    xp_reward = models.PositiveIntegerField(
        default=0,
        help_text="Количество XP, даваемое за достижение."
    )

    def __str__(self):
        return self.name


# Модель профиля пользователя для геймификации
class UserProfile(models.Model):
    """
    Модель профиля пользователя, содержащая информацию для геймификации.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text="Пользователь.",
    )
    xp = models.PositiveIntegerField(
        default=0,
        help_text="Накопленные очки XP."
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


# Модель связи пользователь-достижение
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
        unique_together = ('user_profile', 'achievement')

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.achievement.name}"


# Модель таблицы лидеров
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


# Модель уведомлений для пользователей
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

# Create your models here.