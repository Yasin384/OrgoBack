# main/admin.py

from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import (
    School, SchoolClass, ParentChild, StudentTeacher,
    Subject, Schedule, Homework, SubmittedHomework,
    Grade, Attendance, Achievement, UserProfile,
    UserAchievement, Leaderboard, Notification
)
from .admin_inlines import ParentChildInline, StudentTeacherInline, UserAchievementInline

User = get_user_model()

# Register User Model
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_display_links = ('id', 'username')

# Achievement Admin
@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'xp_reward')
    list_display_links = ('id', 'name')
    search_fields = ('name',)

# School Admin
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'address')

# SchoolClass Admin with Inlines
@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'school')
    list_display_links = ('id', 'name')
    autocomplete_fields = ('school', 'subjects',)
    inlines = [ParentChildInline, StudentTeacherInline]
    search_fields = ('name', 'school__name',)

# Subject Admin
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)

# Schedule Admin
@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'school_class', 'subject', 'teacher', 'weekday', 'start_time', 'end_time')
    list_display_links = ('id', 'school_class')
    autocomplete_fields = ('school_class', 'subject', 'teacher')
    search_fields = ('school_class__name', 'subject__name', 'teacher__username')

# Homework Admin
@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'school_class', 'due_date')
    list_display_links = ('id', 'subject')
    autocomplete_fields = ('subject', 'school_class')
    search_fields = ('subject__name', 'school_class__name', 'description')

# SubmittedHomework Admin
@admin.register(SubmittedHomework)
class SubmittedHomeworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'homework', 'student', 'submitted_at', 'status')
    list_display_links = ('id', 'homework')
    autocomplete_fields = ('homework', 'student')
    search_fields = ('homework__subject__name', 'student__username')

# Grade Admin
@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'subject', 'grade', 'date')
    list_display_links = ('id', 'student')
    autocomplete_fields = ('student', 'subject', 'teacher')
    search_fields = ('student__username', 'subject__name', 'teacher__username')

# Attendance Admin
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'school_class', 'date', 'status')
    list_display_links = ('id', 'student')
    autocomplete_fields = ('student', 'school_class', 'school')
    search_fields = ('student__username', 'school_class__name', 'status')

# UserProfile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'xp', 'level')
    list_display_links = ('id', 'user')
    autocomplete_fields = ('user',)
    inlines = [UserAchievementInline]
    search_fields = ('user__username', 'user__email')

# UserAchievement Admin
@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_username', 'achievement', 'achieved_at')
    list_display_links = ('id', 'get_username')
    autocomplete_fields = ('user_profile', 'achievement')
    search_fields = ('user_profile__user__username', 'achievement__name')

    def get_username(self, obj):
        return obj.user_profile.user.username
    get_username.short_description = 'Username'

# Leaderboard Admin
@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_username', 'rank')
    list_display_links = ('id', 'get_username')
    list_filter = ('rank',)
    search_fields = ('user_profile__user__username',)

    def get_username(self, obj):
        return obj.user_profile.user.username
    get_username.short_description = 'Username'

# Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'message', 'created_at', 'is_read')
    list_display_links = ('id', 'user')
    search_fields = ('message',)
