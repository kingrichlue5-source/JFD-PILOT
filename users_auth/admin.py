from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, Department, UserRole, Permission, RolePermission, UserSession, HospitalSetting


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'department', 'status', 'is_active']
    list_filter = ['status', 'is_active', 'department']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone', 'profile_photo_url')}),
        ('Employment', {'fields': ('department', 'employee_id', 'job_title')}),
        ('Security', {'fields': ('status', 'mfa_enabled', 'mfa_secret', 'failed_login_attempts', 'locked_until')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_system_role', 'is_active']
    list_filter = ['is_system_role', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent_department', 'is_clinical', 'is_active']
    list_filter = ['is_clinical', 'is_active']
    search_fields = ['name', 'code']


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'is_active', 'assigned_at']
    list_filter = ['is_active', 'role']
    search_fields = ['user__username', 'role__name']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'code']


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ['role', 'permission', 'granted_at']
    list_filter = ['role']
    search_fields = ['role__name', 'permission__name']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_token', 'ip_address', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['user__username']


@admin.register(HospitalSetting)
class HospitalSettingAdmin(admin.ModelAdmin):
    list_display = ['hospital_name', 'short_name', 'phone', 'email', 'updated_at']
    search_fields = ['hospital_name', 'short_name', 'email', 'phone']
