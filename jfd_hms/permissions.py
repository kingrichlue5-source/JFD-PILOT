from functools import wraps
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status


def _user_has_permission(user, permission_code):
    """Check if a user has a specific permission through their role assignments."""
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


def require_permission(permission_code):
    """Decorator for function-based API views. Returns 403 if user lacks permission."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            if not _user_has_permission(request.user, permission_code):
                return Response(
                    {'error': f'Permission denied: {permission_code} required'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def make_permission_class(permission_code):
    """Create a DRF permission class for a specific permission code."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return _user_has_permission(request.user, permission_code)

    cls = type(
        f'Has_{permission_code}',
        (BasePermission,),
        {'has_permission': has_permission, 'permission_code': permission_code}
    )
    return cls


def has_permission(user, permission_code):
    """Utility function for checking permissions outside views."""
    return _user_has_permission(user, permission_code)
