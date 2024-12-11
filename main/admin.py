from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User,
    Class,
    Subject,
    Schedule,
    Homework,
    SubmittedHomework,
    Grade,
    Attendance,
    Achievement,
    UserProfile,
    UserAchievement,
    Leaderboard,
    Notification,
)

# Регистрация кастомной модели пользователя с расширенными полями
class UserAdmin(BaseUserAdmin):
    """
    Админ-панель для кастомной модели пользователя.
    """
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Additional Info'), {'fields': ('role',)}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'role', 'password1', 'password2'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели Class.
    """
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели Subject.
    """
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели Schedule.
    """
    list_display = ('class_obj', 'subject', 'teacher', 'weekday', 'start_time', 'end_time')
    list_filter = ('weekday', 'class_obj', 'subject', 'teacher')
    search_fields = ('class_obj__name', 'subject__name', 'teacher__username')


@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели Homework.
    """
    list_display = ('subject', 'class_obj', 'due_date', 'created_at')
    list_filter = ('subject', 'class_obj', 'due_date')
    search_fields = ('subject__name', 'class_obj__name', 'description')


@admin.register(SubmittedHomework)
class SubmittedHomeworkAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели SubmittedHomework.
    """
    list_display = ('homework', 'student', 'submitted_at', 'status', 'grade')
    list_filter = ('status', 'homework__subject', 'homework__class_obj')
    search_fields = ('homework__subject__name', 'student__username')

    # Опционально, вы можете добавить дополнительные методы или настройки здесь


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели Grade.
    """
    list_display = ('student', 'subject', 'grade', 'date', 'teacher')
    list_filter = ('subject', 'date', 'teacher')
    search_fields = ('student__username', 'subject__name', 'teacher__username')


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели Attendance.
    """
    list_display = ('student', 'class_obj', 'date', 'status')
    list_filter = ('status', 'class_obj', 'date')
    search_fields = ('student__username', 'class_obj__name')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели Achievement.
    """
    list_display = ('name', 'xp_reward')
    search_fields = ('name',)
    list_filter = ('xp_reward',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели UserProfile.
    """
    list_display = ('user', 'xp', 'level')
    search_fields = ('user__username',)
    list_filter = ('level',)


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели UserAchievement.
    """
    list_display = ('user_profile', 'achievement', 'achieved_at')
    list_filter = ('achieved_at', 'achievement')
    search_fields = ('user_profile__user__username', 'achievement__name')


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели Leaderboard.
    """
    list_display = ('user_profile', 'rank')
    search_fields = ('user_profile__user__username',)
    ordering = ('rank',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели Notification.
    """
    list_display = ('user', 'message_snippet', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')

    def message_snippet(self, obj):
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    message_snippet.short_description = 'Сообщение'


# Регистрация кастомной модели пользователя
admin.site.register(User, UserAdmin)

# Опционально, можно переименовать заголовок админки
admin.site.site_header = "Админ-панель Школьного Приложения"
admin.site.site_title = "Админ-панель"
admin.site.index_title = "Добро пожаловать в админ-панель"