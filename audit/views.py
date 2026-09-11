from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import AuditLog, LoginLog, DataAccessLog


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def audit_log_list(request):
    queryset = AuditLog.objects.all()
    table = request.query_params.get('table')
    action = request.query_params.get('action')
    user_id = request.query_params.get('user_id')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')
    search = request.query_params.get('search')

    if table:
        queryset = queryset.filter(table_name=table)
    if action:
        queryset = queryset.filter(action=action)
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)
    if search:
        queryset = queryset.filter(
            Q(table_name__icontains=search) |
            Q(user_name__icontains=search) |
            Q(new_values__icontains=search)
        )

    page_size = min(int(request.query_params.get('page_size', 50)), 200)
    offset = int(request.query_params.get('offset', 0))
    total = queryset.count()
    logs = queryset[offset:offset + page_size]

    return Response({
        'total': total,
        'page_size': page_size,
        'offset': offset,
        'results': list(logs.values(
            'id', 'schema_name', 'table_name', 'record_id', 'action',
            'old_values', 'new_values', 'user_id', 'user_name',
            'user_ip', 'created_at'
        )),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def login_log_list(request):
    queryset = LoginLog.objects.all()
    username = request.query_params.get('username')
    success = request.query_params.get('success')
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')

    if username:
        queryset = queryset.filter(username__icontains=username)
    if success is not None:
        queryset = queryset.filter(success=success.lower() == 'true')
    if date_from:
        queryset = queryset.filter(login_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(login_at__date__lte=date_to)

    page_size = min(int(request.query_params.get('page_size', 50)), 200)
    offset = int(request.query_params.get('offset', 0))
    total = queryset.count()
    logs = queryset[offset:offset + page_size]

    return Response({
        'total': total,
        'page_size': page_size,
        'offset': offset,
        'results': list(logs.values(
            'id', 'user_id', 'username', 'login_at', 'logout_at',
            'ip_address', 'success', 'failure_reason'
        )),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def data_access_log_list(request):
    queryset = DataAccessLog.objects.all()
    user_id = request.query_params.get('user_id')
    table = request.query_params.get('table')

    if user_id:
        queryset = queryset.filter(user_id=user_id)
    if table:
        queryset = queryset.filter(table_name=table)

    page_size = min(int(request.query_params.get('page_size', 50)), 200)
    offset = int(request.query_params.get('offset', 0))
    total = queryset.count()
    logs = queryset[offset:offset + page_size]

    return Response({
        'total': total,
        'page_size': page_size,
        'offset': offset,
        'results': list(logs.values(
            'id', 'user_id', 'schema_name', 'table_name',
            'record_id', 'access_type', 'accessed_at', 'ip_address'
        )),
    })
