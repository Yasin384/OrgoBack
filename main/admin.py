from django.contrib import admin
# admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Class, Subject, Schedule, Homework,
    SubmittedHomework, Attendance, Grade, Achievement,
    UserProfile, UserAchievement, Leaderboard, Notification
)

# Кастомизация админки для модели User
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')

admin.site.register(User, UserAdmin)
admin.site.register(Class)
admin.site.register(Subject)
admin.site.register(Schedule)
admin.site.register(Homework)
admin.site.register(SubmittedHomework)
admin.site.register(Attendance)
admin.site.register(Grade)
admin.site.register(Achievement)
admin.site.register(UserProfile)
admin.site.register(UserAchievement)
admin.site.register(Leaderboard)
admin.site.register(Notification)
# Register your models here.
