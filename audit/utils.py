from .models import AuditLog


def log_audit(schema_name, table_name, record_id, action,
              old_values=None, new_values=None, request=None):
    """Central audit logging function.

    Args:
        schema_name: App name (e.g. 'patients', 'clinical', 'pharmacy')
        table_name: Model table name (e.g. 'patients', 'visits')
        record_id: UUID of the affected record
        action: 'CREATE', 'UPDATE', or 'DELETE'
        old_values: Dict of previous values (for UPDATE/DELETE)
        new_values: Dict of new values (for CREATE/UPDATE)
        request: Django HttpRequest (optional, for user/IP capture)
    """
    user_id = None
    user_name = None
    user_ip = '127.0.0.1'
    user_agent = ''

    if request:
        if hasattr(request, 'user') and request.user and request.user.is_authenticated:
            user_id = request.user.id
            user_name = f"{request.user.first_name} {request.user.last_name}".strip()
            if not user_name:
                user_name = request.user.username
        xff = request.META.get('HTTP_X_FORWARDED_FOR')
        if xff:
            user_ip = xff.split(',')[0].strip()
        else:
            user_ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

    AuditLog.objects.create(
        schema_name=schema_name,
        table_name=table_name,
        record_id=record_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        user_id=user_id,
        user_name=user_name,
        user_ip=user_ip,
        user_agent=user_agent,
    )
