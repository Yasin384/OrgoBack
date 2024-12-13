# admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, Class, Subject, Schedule, Homework, SubmittedHomework, Grade,
    Attendance, Achievement, UserProfile, UserAchievement, Leaderboard, Notification
)

# Регистрация кастомной модели пользователя
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Административная панель для кастомной модели пользователя.
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Additional Info'), {'fields': ('role', 'school', 'name')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'role', 'school', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

# Базовый класс админки для общих настроек
class BaseAdmin(admin.ModelAdmin):
    """
    Базовый класс админки для общих конфигураций.
    """
    search_fields = ('name',)
    ordering = ('id',)
    list_per_page = 25

# Инлайн админка для достижения пользователя
class UserAchievementInline(admin.TabularInline):
    model = UserAchievement
    extra = 1
    readonly_fields = ('achieved_at',)

# Регистрация модели профиля пользователя с инлайном для достижений
@admin.register(UserProfile)
class UserProfileAdmin(BaseAdmin):
    """
    Административная панель для модели профиля пользователя.
    """
    list_display = ('user', 'xp', 'level')
    list_filter = ('level',)
    search_fields = ('user__username',)
    inlines = [UserAchievementInline]
    list_select_related = ('user',)
    prefetch_related = ('achievements',)

# Регистрация остальных моделей с оптимизациями
@admin.register(Class)
class ClassAdmin(BaseAdmin):
    """
    Административная панель для модели Class.
    """
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)

@admin.register(Subject)
class SubjectAdmin(BaseAdmin):
    """
    Административная панель для модели Subject.
    """
    list_display = ('name',)
    search_fields = ('name',)
    list_filter = ('name',)

@admin.register(Schedule)
class ScheduleAdmin(BaseAdmin):
    """
    Административная панель для модели Schedule.
    """
    list_display = ('class_obj', 'subject', 'teacher', 'weekday', 'start_time', 'end_time')
    list_filter = ('weekday', 'class_obj', 'subject', 'teacher')
    search_fields = ('class_obj__name', 'subject__name', 'teacher__username')
    list_select_related = ('class_obj', 'subject', 'teacher')

@admin.register(Homework)
class HomeworkAdmin(BaseAdmin):
    """
    Административная панель для модели Homework.
    """
    list_display = ('subject', 'class_obj', 'due_date', 'created_at')
    list_filter = ('subject', 'class_obj', 'due_date')
    search_fields = ('subject__name', 'class_obj__name', 'description')
    list_select_related = ('subject', 'class_obj')

@admin.register(SubmittedHomework)
class SubmittedHomeworkAdmin(BaseAdmin):
    """
    Административная панель для модели SubmittedHomework.
    """
    list_display = ('homework', 'student', 'submitted_at', 'status', 'grade')
    list_filter = ('status', 'homework__subject', 'homework__class_obj')
    search_fields = ('homework__subject__name', 'student__username')
    list_select_related = ('homework', 'student')

@admin.register(Grade)
class GradeAdmin(BaseAdmin):
    """
    Административная панель для модели Grade.
    """
    list_display = ('student', 'subject', 'grade', 'date', 'teacher')
    list_filter = ('subject', 'date', 'teacher')
    search_fields = ('student__username', 'subject__name', 'teacher__username')
    list_select_related = ('student', 'subject', 'teacher')

@admin.register(Attendance)
class AttendanceAdmin(BaseAdmin):
    """
    Административная панель для модели Attendance.
    """
    list_display = ('student', 'class_obj', 'date', 'status')
    list_filter = ('status', 'class_obj', 'date')
    search_fields = ('student__username', 'class_obj__name')
    list_select_related = ('student', 'class_obj')

@admin.register(Achievement)
class AchievementAdmin(BaseAdmin):
    """
    Административная панель для модели Achievement.
    """
    list_display = ('name', 'xp_reward')
    list_filter = ('xp_reward',)
    search_fields = ('name',)
    ordering = ('-xp_reward',)

@admin.register(UserAchievement)
class UserAchievementAdmin(BaseAdmin):
    """
    Административная панель для модели UserAchievement.
    """
    list_display = ('user_profile', 'achievement', 'achieved_at')
    list_filter = ('achieved_at', 'achievement')
    search_fields = ('user_profile__user__username', 'achievement__name')
    list_select_related = ('user_profile', 'achievement')

@admin.register(Leaderboard)
class LeaderboardAdmin(BaseAdmin):
    """
    Административная панель для модели Leaderboard.
    """
    list_display = ('user_profile', 'rank')
    ordering = ('rank',)
    search_fields = ('user_profile__user__username',)
    list_select_related = ('user_profile',)

@admin.register(Notification)
class NotificationAdmin(BaseAdmin):
    """
    Административная панель для модели Notification.
    """
    list_display = ('user', 'message_snippet', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
    list_select_related = ('user',)

    def message_snippet(self, obj):
        """
        Отображает фрагмент сообщения уведомления.
        """
        return (obj.message[:50] + '...') if len(obj.message) > 50 else obj.message
    message_snippet.short_description = 'Message Snippet'

# Настройка заголовков административного сайта
admin.site.site_header = "School App Admin Panel"
admin.site.site_title = "Admin Panel"
admin.site.index_title = "Welcome to the Admin Panel"