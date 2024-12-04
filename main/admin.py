from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Class, Subject, Schedule, Homework,
    SubmittedHomework, Attendance, Grade, Achievement,
    UserProfile, UserAchievement, Leaderboard, Notification
)

# Customizing the User admin
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

# Admin for the Class model
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'teacher', 'created_at')
    search_fields = ('name', 'teacher__username')
    list_filter = ('created_at',)

# Admin for the Subject model
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'class_assigned', 'teacher')
    search_fields = ('name', 'teacher__username')
    list_filter = ('class_assigned',)

# Admin for the Schedule model
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('class_assigned', 'subject', 'day', 'start_time', 'end_time')
    list_filter = ('day', 'class_assigned')
    search_fields = ('class_assigned__name', 'subject__name')

# Admin for the Homework model
class HomeworkAdmin(admin.ModelAdmin):
    list_display = ('title', 'class_assigned', 'subject', 'due_date')
    list_filter = ('due_date', 'class_assigned', 'subject')
    search_fields = ('title', 'class_assigned__name', 'subject__name')

# Admin for SubmittedHomework
class SubmittedHomeworkAdmin(admin.ModelAdmin):
    list_display = ('homework', 'student', 'submitted_at', 'grade')
    list_filter = ('submitted_at', 'grade')
    search_fields = ('homework__title', 'student__username')

# Admin for Attendance
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_assigned', 'date', 'status')
    list_filter = ('date', 'status', 'class_assigned')
    search_fields = ('student__username', 'class_assigned__name')

# Admin for Grade
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'class_assigned', 'subject', 'grade')
    list_filter = ('class_assigned', 'subject')
    search_fields = ('student__username', 'subject__name')

# Admin for Achievement
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'date_awarded')
    search_fields = ('title', 'student__username')
    list_filter = ('date_awarded',)

# Admin for UserProfile
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'profile_picture')
    search_fields = ('user__username',)

# Admin for UserAchievement
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ('user', 'achievement', 'date_awarded')
    search_fields = ('user__username', 'achievement__title')
    list_filter = ('date_awarded',)

# Admin for Leaderboard
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'rank')
    search_fields = ('user__username',)
    list_filter = ('rank',)

# Admin for Notification
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('title', 'user__username')

# Registering models with their respective customizations
admin.site.register(User, UserAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(Homework, HomeworkAdmin)
admin.site.register(SubmittedHomework, SubmittedHomeworkAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Grade, GradeAdmin)
admin.site.register(Achievement, AchievementAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(UserAchievement, UserAchievementAdmin)
admin.site.register(Leaderboard, LeaderboardAdmin)
admin.site.register(Notification, NotificationAdmin)