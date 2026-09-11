"""
Middleware to set the current request user and IP for audit logging in signals.
"""
from billing.signals import set_request_user, set_request_ip


class AuditUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        set_request_user(user)
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            ip = x_forwarded.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        set_request_ip(ip)
        response = self.get_response(request)
        return response
