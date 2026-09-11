from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Q
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import json

from .models import User, Role, Department, UserRole, RolePermission, Permission, UserSession
from .serializers import (
    UserSerializer, UserCreateSerializer, RoleSerializer,
    DepartmentSerializer, LoginSerializer, UserProfileSerializer
)
from jfd_hms.permissions import require_permission, make_permission_class


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]

    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30

    def post(self, request):
        from django.utils import timezone as tz
        from datetime import timedelta
        from audit.models import LoginLog

        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        if not username or not password:
            return Response({'error': 'Username and password required'}, status=status.HTTP_400_BAD_REQUEST)

        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        try:
            lockout_user = User.objects.get(username=username)
            if (lockout_user.failed_login_attempts >= self.MAX_FAILED_ATTEMPTS and
                    lockout_user.locked_until and tz.now() < lockout_user.locked_until):
                remaining = (lockout_user.locked_until - tz.now()).seconds // 60 + 1
                LoginLog.objects.create(
                    user_id=lockout_user.id, username=username, success=False,
                    failure_reason='Account locked', ip_address=ip_address, user_agent=user_agent
                )
                return Response(
                    {'error': f'Account locked. Try again in {remaining} minutes.'},
                    status=status.HTTP_423_LOCKED
                )
            elif lockout_user.locked_until and tz.now() >= lockout_user.locked_until:
                lockout_user.failed_login_attempts = 0
                lockout_user.locked_until = None
                lockout_user.save(update_fields=['failed_login_attempts', 'locked_until'])
        except User.DoesNotExist:
            pass

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.status != 'active':
                LoginLog.objects.create(
                    user_id=user.id, username=username, success=False,
                    failure_reason='Account inactive', ip_address=ip_address, user_agent=user_agent
                )
                return Response({'error': 'Account is inactive'}, status=status.HTTP_403_FORBIDDEN)

            login(request, user)

            user.failed_login_attempts = 0
            user.locked_until = None
            user.save(update_fields=['failed_login_attempts', 'locked_until'])

            session = UserSession.objects.create(
                user=user,
                session_token=request.session.session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=tz.now() + tz.timedelta(hours=24)
            )

            LoginLog.objects.create(
                user_id=user.id, username=username, success=True,
                ip_address=ip_address, user_agent=user_agent,
                session_id=session.id
            )

            user_roles = UserRole.objects.filter(user=user, is_active=True).select_related('role')
            roles = [ur.role.code for ur in user_roles]

            permission_ids = RolePermission.objects.filter(
                role__in=[ur.role for ur in user_roles]
            ).values_list('permission_id', flat=True)
            permissions = Permission.objects.filter(id__in=permission_ids).values_list('code', flat=True)

            return Response({
                'user': UserSerializer(user).data,
                'roles': roles,
                'permissions': list(permissions),
                'session_id': str(session.id)
            })
        else:
            try:
                fail_user = User.objects.get(username=username)
                fail_user.failed_login_attempts = (fail_user.failed_login_attempts or 0) + 1
                fail_user.locked_until = tz.now()
                fail_user.save(update_fields=['failed_login_attempts', 'locked_until'])
                LoginLog.objects.create(
                    user_id=fail_user.id, username=username, success=False,
                    failure_reason='Invalid credentials', ip_address=ip_address, user_agent=user_agent
                )
            except User.DoesNotExist:
                LoginLog.objects.create(
                    user_id=None, username=username, success=False,
                    failure_reason='User not found', ip_address=ip_address, user_agent=user_agent
                )
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from audit.models import LoginLog

        session = UserSession.objects.filter(
            user=request.user,
            session_token=request.session.session_key
        ).first()
        if session:
            LoginLog.objects.filter(session_id=session.id, logout_at__isnull=True).update(
                logout_at=timezone.now() if hasattr(timezone, 'now') else None
            )
            session.is_active = False
            session.save(update_fields=['is_active'])

        logout(request)
        return Response({'message': 'Logged out successfully'})


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(generics.ListAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        queryset = User.objects.filter(is_active=True)
        search = self.request.query_params.get('search', None)
        department = self.request.query_params.get('department', None)
        role = self.request.query_params.get('role', None)

        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )

        if department:
            queryset = queryset.filter(department_id=department)

        if role:
            role_list = [r.strip() for r in role.split(',')]
            user_ids = UserRole.objects.filter(role__code__in=role_list).values_list('user_id', flat=True)
            queryset = queryset.filter(id__in=user_ids)

        return queryset


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [make_permission_class('USER_MANAGE')]

    def destroy(self, request, *args, **kwargs):
        from audit.utils import log_audit
        user = self.get_object()
        user.is_active = False
        user.save()
        log_audit('users_auth', 'users', user.id, 'UPDATE',
                  new_values={'is_active': False, 'username': user.username},
                  request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleListView(generics.ListCreateAPIView):
    queryset = Role.objects.filter(is_active=True)
    serializer_class = RoleSerializer
    permission_classes = [make_permission_class('ROLE_MANAGE')]


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [make_permission_class('ROLE_MANAGE')]


class DepartmentListView(generics.ListCreateAPIView):
    queryset = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [make_permission_class('USER_MANAGE')]

    def get_queryset(self):
        queryset = Department.objects.filter(is_active=True)
        parent = self.request.query_params.get('parent', None)
        clinical = self.request.query_params.get('clinical', None)

        if parent:
            if parent == 'root':
                queryset = queryset.filter(parent_department__isnull=True)
            else:
                queryset = queryset.filter(parent_department_id=parent)

        if clinical is not None:
            queryset = queryset.filter(is_clinical=clinical.lower() == 'true')

        return queryset


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [make_permission_class('USER_MANAGE')]


class RolePermissionCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        permission_code = request.data.get('permission_code')
        if not permission_code:
            return Response({'error': 'permission_code required'}, status=status.HTTP_400_BAD_REQUEST)

        user_roles = UserRole.objects.filter(user=request.user, is_active=True)
        permission_ids = RolePermission.objects.filter(
            role__in=[ur.role for ur in user_roles]
        ).values_list('permission_id', flat=True)
        has_permission = Permission.objects.filter(id__in=permission_ids, code=permission_code).exists()

        return Response({
            'has_permission': has_permission,
            'permission_code': permission_code,
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_counts(request):
    """Return pending task counts based on the user's role permissions."""
    user = request.user
    counts = {}

    if user.is_superuser:
        from clinical.models import Visit, Order
        from pharmacy.models import Prescription
        from billing.models import Invoice
        from inventory.models import Item, Stock
        counts['triage_queue'] = Visit.objects.filter(status='checked_in', is_deleted=False).count()
        counts['pending_visits'] = Visit.objects.filter(status='in_progress', is_deleted=False).count()
        counts['pending_prescriptions'] = Prescription.objects.filter(status='pending').count()
        counts['pending_invoices'] = Invoice.objects.filter(status__in=['pending', 'partial'], is_deleted=False).count()
        counts['pending_orders'] = Order.objects.filter(status='pending').count()
        counts['low_stock_items'] = Stock.objects.filter(quantity_on_hand__lte=10).count()
        return Response(counts)

    user_role_ids = UserRole.objects.filter(user=user, is_active=True).values_list('role_id', flat=True)
    perm_codes = set(RolePermission.objects.filter(
        role_id__in=user_role_ids, permission__is_active=True
    ).values_list('permission__code', flat=True))

    from clinical.models import Visit, Order
    from pharmacy.models import Prescription
    from billing.models import Invoice
    from inventory.models import Stock

    if 'TRIAGE_PERFORM' in perm_codes:
        counts['triage_queue'] = Visit.objects.filter(status='checked_in', is_deleted=False).count()

    if 'ENCOUNTER_EDIT' in perm_codes:
        counts['pending_visits'] = Visit.objects.filter(status='in_progress', is_deleted=False).count()

    if 'RX_VIEW' in perm_codes:
        counts['pending_prescriptions'] = Prescription.objects.filter(status='pending').count()

    if 'INVOICE_VIEW' in perm_codes:
        counts['pending_invoices'] = Invoice.objects.filter(status__in=['pending', 'partial'], is_deleted=False).count()

    if 'ORDER_VIEW' in perm_codes:
        counts['pending_orders'] = Order.objects.filter(status='pending').count()

    if 'INVENTORY_VIEW' in perm_codes:
        counts['low_stock_items'] = Stock.objects.filter(quantity_on_hand__lte=10).count()

    return Response(counts)
