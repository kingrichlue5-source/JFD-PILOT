import json
from datetime import date

from django.db.models import F
from django.http import JsonResponse, HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services import (
    get_hmis_summary, build_dhis2_payload,
    get_top_diagnoses, get_revenue_collected, get_total_attendance,
    _month_range,
)
from .exporters import export_csv, export_xlsx


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hmis_summary(request):
    """Monthly HMIS summary with all indicators."""
    year = int(request.query_params.get('year', date.today().year))
    month = int(request.query_params.get('month', date.today().month))

    if month < 1 or month > 12:
        return Response({'error': 'Month must be 1-12'}, status=400)

    data = get_hmis_summary(year, month)
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dhis2_export(request):
    """DHIS2 dataValueSets JSON payload for import into DHIS2."""
    year = int(request.query_params.get('year', date.today().year))
    month = int(request.query_params.get('month', date.today().month))

    if month < 1 or month > 12:
        return Response({'error': 'Month must be 1-12'}, status=400)

    payload = build_dhis2_payload(year, month)
    return Response(payload)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def csv_export(request):
    """CSV export of monthly HMIS report."""
    year = int(request.query_params.get('year', date.today().year))
    month = int(request.query_params.get('month', date.today().month))

    data = get_hmis_summary(year, month)
    filename = f'JFD_HMIS_{year}_{month:02d}'
    return export_csv(data['indicators'], filename=filename)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def xlsx_export(request):
    """Formatted XLSX export of monthly HMIS report."""
    year = int(request.query_params.get('year', date.today().year))
    month = int(request.query_params.get('month', date.today().month))

    if month < 1 or month > 12:
        return Response({'error': 'Month must be 1-12'}, status=400)

    data = get_hmis_summary(year, month)
    filename = f'JFD_HMIS_{year}_{month:02d}'
    return export_xlsx(data, filename=filename)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def top_diagnoses(request):
    """Top N diagnoses for a given month."""
    year = int(request.query_params.get('year', date.today().year))
    month = int(request.query_params.get('month', date.today().month))
    limit = int(request.query_params.get('limit', 10))

    data = get_top_diagnoses(year, month, limit=limit)
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def monthly_revenue(request):
    """Monthly revenue breakdown for a given year."""
    year = int(request.query_params.get('year', date.today().year))

    from billing.models import Payment
    from django.db.models import Sum

    monthly_data = []
    for m in range(1, 13):
        start, end = _month_range(year, m)
        total = Payment.objects.filter(
            payment_date__gte=start,
            payment_date__lt=end,
            is_deleted=False,
        ).aggregate(total=Sum('amount'))['total'] or 0
        monthly_data.append({
            'month': m,
            'month_name': date(year, m, 1).strftime('%B'),
            'revenue': str(total),
        })

    return Response({
        'year': year,
        'monthly_revenue': monthly_data,
        'total_annual': str(sum(float(m['revenue']) for m in monthly_data)),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attendance_trend(request):
    """Monthly attendance trend for a given year."""
    year = int(request.query_params.get('year', date.today().year))

    from clinical.models import Visit

    monthly_data = []
    for m in range(1, 13):
        start, end = _month_range(year, m)
        count = Visit.objects.filter(
            visit_date__gte=start,
            visit_date__lt=end,
            is_deleted=False,
        ).exclude(status='cancelled').values('patient').distinct().count()
        monthly_data.append({
            'month': m,
            'month_name': date(year, m, 1).strftime('%B'),
            'attendance': count,
        })

    return Response({
        'year': year,
        'monthly_attendance': monthly_data,
        'total_annual': sum(m['attendance'] for m in monthly_data),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def patient_demographics(request):
    from patients.models import Patient
    from django.db.models import Count

    total = Patient.objects.filter(is_deleted=False).count()
    by_gender = list(
        Patient.objects.filter(is_deleted=False)
        .values('gender').annotate(count=Count('id'))
    )
    by_payer = list(
        Patient.objects.filter(is_deleted=False)
        .values('payer_category').annotate(count=Count('id'))
    )
    return Response({
        'total_patients': total,
        'by_gender': by_gender,
        'by_payer_category': by_payer,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def department_utilization(request):
    from clinical.models import Visit
    from django.db.models import Count
    from datetime import date

    year = int(request.query_params.get('year', date.today().year))
    month = int(request.query_params.get('month', date.today().month))
    start, end = _month_range(year, month)

    data = list(
        Visit.objects.filter(
            visit_date__gte=start, visit_date__lt=end, is_deleted=False
        ).exclude(status='cancelled')
        .values(dept_name=F('department__name'))
        .annotate(visit_count=Count('id'))
        .order_by('-visit_count')
    )
    return Response({'year': year, 'month': month, 'departments': data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bed_occupancy_report(request):
    from clinical.models import Bed
    from django.db.models import Count, Q

    data = list(
        Bed.objects.filter(is_active=True, room__ward__is_active=True)
        .values(ward_name=F('room__ward__name'), ward_code=F('room__ward__code'))
        .annotate(
            total=Count('id'),
            occupied=Count('id', filter=Q(is_occupied=True)),
            reserved=Count('id', filter=Q(is_reserved=True)),
        )
    )
    for d in data:
        d['available'] = d['total'] - d['occupied'] - d['reserved']
        d['occupancy_rate'] = round(d['occupied'] / d['total'] * 100, 1) if d['total'] > 0 else 0
    return Response(data)
