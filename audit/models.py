import uuid
from django.db import models


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    schema_name = models.CharField(max_length=50)
    table_name = models.CharField(max_length=100)
    record_id = models.UUIDField()
    action = models.CharField(max_length=10)
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    user_id = models.UUIDField(blank=True, null=True)
    user_name = models.CharField(max_length=200, blank=True, null=True)
    user_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    session_id = models.UUIDField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        managed = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.schema_name}.{self.table_name} - {self.action} - {self.created_at}"


class LoginLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True)
    username = models.CharField(max_length=100)
    login_at = models.DateTimeField(auto_now_add=True)
    logout_at = models.DateTimeField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    success = models.BooleanField()
    failure_reason = models.TextField(blank=True, null=True)
    session_id = models.UUIDField(blank=True, null=True)

    class Meta:
        db_table = 'login_logs'
        managed = True
        ordering = ['-login_at']

    def __str__(self):
        return f"{self.username} - {self.login_at} - {'Success' if self.success else 'Failed'}"


class DataAccessLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField()
    schema_name = models.CharField(max_length=50)
    table_name = models.CharField(max_length=100)
    record_id = models.UUIDField(blank=True, null=True)
    access_type = models.CharField(max_length=20)
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        db_table = 'data_access_logs'
        managed = True
        ordering = ['-accessed_at']

    def __str__(self):
        return f"User {self.user_id} - {self.schema_name}.{self.table_name} - {self.access_type}"
