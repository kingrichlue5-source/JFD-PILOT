from django import template
from django.contrib.auth import get_user_model

register = template.Library()
User = get_user_model()


@register.simple_tag(takes_context=True)
def user_has_permission(context, permission_code):
    """Check if the current user has a specific permission.
    Usage: {% user_has_permission "INVENTORY_VIEW" as has_inv %}
            {% if has_inv %}...{% endif %}
    """
    user = context.get('user')
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    from users_auth.models import UserRole, RolePermission
    user_role_ids = UserRole.objects.filter(
        user=user, is_active=True
    ).values_list('role_id', flat=True)
    return RolePermission.objects.filter(
        role_id__in=user_role_ids,
        permission__code=permission_code,
        permission__is_active=True
    ).exists()


@register.simple_tag(takes_context=True)
def user_has_role(context, role_code):
    """Check if the current user has a specific role.
    Usage: {% user_has_role "ADMIN" as is_admin %}
            {% if is_admin %}...{% endif %}
    """
    user = context.get('user')
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    from users_auth.models import UserRole
    return UserRole.objects.filter(
        user=user,
        role__code=role_code,
        is_active=True
    ).exists()
