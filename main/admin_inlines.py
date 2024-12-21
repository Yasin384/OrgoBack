# main/admin_inlines.py

from django.contrib import admin
from .models import ParentChild, StudentTeacher, UserAchievement

class ParentChildInline(admin.TabularInline):
    """
    Inline admin interface for ParentChild model within SchoolClassAdmin.
    """
    model = ParentChild
    extra = 1
    autocomplete_fields = ('parent', 'child', 'school_class')
    # Optional: Define fields to display in the inline
    fields = ('parent', 'child', 'school_class')
    readonly_fields = ('school_class',)  # Assuming school_class is set via SchoolClassAdmin

class StudentTeacherInline(admin.TabularInline):
    """
    Inline admin interface for StudentTeacher model within SchoolClassAdmin.
    """
    model = StudentTeacher
    extra = 1
    autocomplete_fields = ('student', 'teacher', 'school_class')
    fields = ('student', 'teacher', 'school_class', 'relationship', 'established_date')
    readonly_fields = ('school_class',)  # Assuming school_class is set via SchoolClassAdmin

class UserAchievementInline(admin.TabularInline):
    """
    Inline admin interface for UserAchievement model within UserProfileAdmin.
    """
    model = UserAchievement
    extra = 1
    autocomplete_fields = ('achievement',)
    fields = ('achievement', 'achieved_at')
    readonly_fields = ('achieved_at',)
