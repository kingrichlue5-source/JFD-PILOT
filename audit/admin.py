from django.contrib import admin
from .models import AuditLog, LoginLog, DataAccessLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['schema_name', 'table_name', 'record_id', 'action', 'user_name', 'created_at']
    list_filter = ['schema_name', 'table_name', 'action']
    search_fields = ['schema_name', 'table_name', 'user_name']
    readonly_fields = ['id', 'schema_name', 'table_name', 'record_id', 'action',
                       'old_values', 'new_values', 'user_id', 'user_name',
                       'user_ip', 'user_agent', 'session_id', 'created_at']
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ['username', 'success', 'ip_address', 'login_at', 'logout_at']
    list_filter = ['success']
    search_fields = ['username']
    readonly_fields = ['id', 'user_id', 'username', 'login_at', 'logout_at',
                       'ip_address', 'user_agent', 'success', 'failure_reason', 'session_id']
    date_hierarchy = 'login_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DataAccessLog)
class DataAccessLogAdmin(admin.ModelAdmin):
    list_display = ['user_id', 'schema_name', 'table_name', 'access_type', 'accessed_at']
    list_filter = ['schema_name', 'access_type']
    search_fields = ['schema_name', 'table_name']
    readonly_fields = ['id', 'user_id', 'schema_name', 'table_name', 'record_id',
                       'access_type', 'accessed_at', 'ip_address']
    date_hierarchy = 'accessed_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
