from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def user_has_permission(context, permission_code):
    """Check if the current user has a specific permission."""
    try:
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
    except Exception:
        return False


@register.simple_tag(takes_context=True)
def user_has_role(context, role_code):
    """Check if the current user has a specific role."""
    try:
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
    except Exception:
        return False
