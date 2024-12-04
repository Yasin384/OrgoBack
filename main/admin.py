# admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
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
    Notification
)

# ==========================
# Custom User Administration
# ==========================

class UserAdmin(BaseUserAdmin):
    """
    Custom admin for the User model to include the 'role' field.
    """
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

admin.site.register(User, UserAdmin)

# ==========================
# Class Administration
# ==========================

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    """
    Admin interface for the Class model.
    """
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

# ==========================
# Subject Administration
# ==========================

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """
    Admin interface for the Subject model.
    """
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

# ==========================
# Schedule Administration
# ==========================

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    """
    Admin interface for the Schedule model.
    """
    list_display = ('class_obj', 'subject', 'teacher', 'get_weekday', 'start_time', 'end_time')
    list_filter = ('weekday', 'class_obj', 'subject', 'teacher')
    search_fields = ('class_obj__name', 'subject__name', 'teacher__username')
    ordering = ('class_obj', 'weekday', 'start_time')

    def get_weekday(self, obj):
        return obj.get_weekday_display()
    get_weekday.short_description = 'Weekday'
    get_weekday.admin_order_field = 'weekday'

# ==========================
# Homework Administration
# ==========================

@admin.register(Homework)
class HomeworkAdmin(admin.ModelAdmin):
    """
    Admin interface for the Homework model.
    """
    list_display = ('subject', 'class_obj', 'due_date', 'created_at')
    list_filter = ('subject', 'class_obj', 'due_date')
    search_fields = ('subject__name', 'class_obj__name', 'description')
    ordering = ('due_date',)

# ===============================
# Submitted Homework Administration
# ===============================

@admin.register(SubmittedHomework)
class SubmittedHomeworkAdmin(admin.ModelAdmin):
    """
    Admin interface for the SubmittedHomework model.
    """
    list_display = ('homework', 'student', 'submitted_at', 'status', 'grade')
    list_filter = ('status', 'submitted_at', 'grade')
    search_fields = ('homework__subject__name', 'student__username')
    readonly_fields = ('submitted_at',)
    ordering = ('-submitted_at',)

    actions = ['mark_as_graded']

    def mark_as_graded(self, request, queryset):
        """
        Custom action to mark selected homeworks as graded.
        """
        updated_count = queryset.update(status='graded')
        self.message_user(request, f"{updated_count} homework(s) marked as graded.")
    mark_as_graded.short_description = "Mark selected homeworks as graded"

# ==========================
# Grade Administration
# ==========================

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    """
    Admin interface for the Grade model.
    """
    list_display = ('student', 'subject', 'grade', 'date', 'teacher')
    list_filter = ('subject', 'date', 'teacher')
    search_fields = ('student__username', 'subject__name', 'teacher__username')
    ordering = ('-date',)

# ==============================
# Attendance Administration
# ==============================

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """
    Admin interface for the Attendance model.
    """
    list_display = ('student', 'class_obj', 'date', 'status')
    list_filter = ('status', 'class_obj', 'date')
    search_fields = ('student__username', 'class_obj__name')
    ordering = ('-date',)

# ==============================
# Achievement Administration
# ==============================

@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """
    Admin interface for the Achievement model.
    """
    list_display = ('name', 'xp_reward')
    search_fields = ('name',)
    list_filter = ('xp_reward',)
    ordering = ('-xp_reward',)

# ===============================
# UserProfile Administration
# ===============================

class UserAchievementInline(admin.TabularInline):
    """
    Inline admin interface for UserAchievement within UserProfile.
    """
    model = UserAchievement
    extra = 1
    readonly_fields = ('achieved_at',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserProfile model.
    """
    list_display = ('user', 'xp', 'level')
    search_fields = ('user__username', 'user__email')
    inlines = [UserAchievementInline]
    ordering = ('-xp',)

# ====================================
# UserAchievement Administration
# ====================================

@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """
    Admin interface for the UserAchievement model.
    """
    list_display = ('user_profile', 'achievement', 'achieved_at')
    list_filter = ('achievement', 'achieved_at')
    search_fields = ('user_profile__user__username', 'achievement__name')
    readonly_fields = ('achieved_at',)
    ordering = ('-achieved_at',)

# ===============================
# Leaderboard Administration
# ===============================

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """
    Admin interface for the Leaderboard model.
    """
    list_display = ('user_profile', 'rank')
    search_fields = ('user_profile__user__username',)
    list_filter = ('rank',)
    ordering = ('rank',)

# ==============================
# Notification Administration
# ==============================

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for the Notification model.
    """
    list_display = ('user', 'short_message', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def short_message(self, obj):
        """
        Returns a truncated version of the message for display.
        """
        return (obj.message[:75] + '...') if len(obj.message) > 75 else obj.message
    short_message.short_description = 'Message'

# ====================================
# Optional: Customize the Admin Site
# ====================================

admin.site.site_header = "School Management Admin"
admin.site.site_title = "School Management Admin Portal"
admin.site.index_title = "Welcome to the School Management Admin Portal"