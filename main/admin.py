from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import (
    User, Class, Subject, Schedule, Homework, SubmittedHomework, Grade,
    Attendance, Achievement, UserProfile, UserAchievement, Leaderboard, Notification
)


# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin panel for the custom User model.
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


# Base admin class for common list configurations
class BaseAdmin(admin.ModelAdmin):
    """
    Base Admin class for common configurations.
    """
    search_fields = ('name',)
    ordering = ('id',)


@admin.register(Class)
class ClassAdmin(BaseAdmin):
    """
    Admin panel for the Class model.
    """
    list_display = ('name',)


@admin.register(Subject)
class SubjectAdmin(BaseAdmin):
    """
    Admin panel for the Subject model.
    """
    list_display = ('name',)


@admin.register(Schedule)
class ScheduleAdmin(BaseAdmin):
    """
    Admin panel for the Schedule model.
    """
    list_display = ('class_obj', 'subject', 'teacher', 'weekday', 'start_time', 'end_time')
    list_filter = ('weekday', 'class_obj', 'subject', 'teacher')
    search_fields = ('class_obj__name', 'subject__name', 'teacher__username')


@admin.register(Homework)
class HomeworkAdmin(BaseAdmin):
    """
    Admin panel for the Homework model.
    """
    list_display = ('subject', 'class_obj', 'due_date', 'created_at')
    list_filter = ('subject', 'class_obj', 'due_date')
    search_fields = ('subject__name', 'class_obj__name', 'description')


@admin.register(SubmittedHomework)
class SubmittedHomeworkAdmin(BaseAdmin):
    """
    Admin panel for the SubmittedHomework model.
    """
    list_display = ('homework', 'student', 'submitted_at', 'status', 'grade')
    list_filter = ('status', 'homework__subject', 'homework__class_obj')
    search_fields = ('homework__subject__name', 'student__username')


@admin.register(Grade)
class GradeAdmin(BaseAdmin):
    """
    Admin panel for the Grade model.
    """
    list_display = ('student', 'subject', 'grade', 'date', 'teacher')
    list_filter = ('subject', 'date', 'teacher')
    search_fields = ('student__username', 'subject__name', 'teacher__username')


@admin.register(Attendance)
class AttendanceAdmin(BaseAdmin):
    """
    Admin panel for the Attendance model.
    """
    list_display = ('student', 'class_obj', 'date', 'status')
    list_filter = ('status', 'class_obj', 'date')
    search_fields = ('student__username', 'class_obj__name')


@admin.register(Achievement)
class AchievementAdmin(BaseAdmin):
    """
    Admin panel for the Achievement model.
    """
    list_display = ('name', 'xp_reward')
    list_filter = ('xp_reward',)


@admin.register(UserProfile)
class UserProfileAdmin(BaseAdmin):
    """
    Admin panel for the UserProfile model.
    """
    list_display = ('user', 'xp', 'level')
    list_filter = ('level',)
    search_fields = ('user__username',)


@admin.register(UserAchievement)
class UserAchievementAdmin(BaseAdmin):
    """
    Admin panel for the UserAchievement model.
    """
    list_display = ('user_profile', 'achievement', 'achieved_at')
    list_filter = ('achieved_at', 'achievement')
    search_fields = ('user_profile__user__username', 'achievement__name')


@admin.register(Leaderboard)
class LeaderboardAdmin(BaseAdmin):
    """
    Admin panel for the Leaderboard model.
    """
    list_display = ('user_profile', 'rank')
    ordering = ('rank',)
    search_fields = ('user_profile__user__username',)


@admin.register(Notification)
class NotificationAdmin(BaseAdmin):
    """
    Admin panel for the Notification model.
    """
    list_display = ('user', 'message_snippet', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')

    def message_snippet(self, obj):
        """
        Display a snippet of the notification message.
        """
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    message_snippet.short_description = 'Message Snippet'


# Admin panel customization
admin.site.site_header = "School App Admin Panel"
admin.site.site_title = "Admin Panel"
admin.site.index_title = "Welcome to the Admin Panel"