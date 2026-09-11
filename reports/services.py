"""
Aggregation engine for HMIS/DHIS2 reporting.
Queries the database for monthly statistics and formats DHIS2 dataValueSets payloads.
"""
from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum, Q
from django.utils import timezone


def _month_range(year, month):
    """Return (start_date, end_date) for the given year/month."""
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start, end


def get_total_attendance(year, month):
    """Total unique patient visits for the month."""
    from clinical.models import Visit
    start, end = _month_range(year, month)
    return Visit.objects.filter(
        visit_date__gte=start,
        visit_date__lt=end,
        is_deleted=False,
    ).exclude(status='cancelled').values('patient').distinct().count()


def get_opd_attendance(year, month):
    """Outpatient department visits."""
    from clinical.models import Visit
    start, end = _month_range(year, month)
    return Visit.objects.filter(
        visit_date__gte=start,
        visit_date__lt=end,
        visit_type='opd',
        is_deleted=False,
    ).exclude(status='cancelled').count()


def get_er_attendance(year, month):
    """Emergency room visits."""
    from clinical.models import Visit
    start, end = _month_range(year, month)
    return Visit.objects.filter(
        visit_date__gte=start,
        visit_date__lt=end,
        visit_type='er',
        is_deleted=False,
    ).exclude(status='cancelled').count()


def get_ipd_admissions(year, month):
    """Inpatient admissions."""
    from clinical.models import Admission
    start, end = _month_range(year, month)
    return Admission.objects.filter(
        admission_date__gte=start,
        admission_date__lt=end,
    ).count()


def get_maternal_deliveries(year, month):
    """Maternal delivery visits (OBGYN keyword matching on chief complaint)."""
    from clinical.models import Visit
    start, end = _month_range(year, month)
    obgyn_keywords = [
        'delivery', 'labor', 'contraction', 'c-section', 'cesarean',
        'maternal', 'apgar', 'newborn', 'postnatal', 'antenatal',
    ]
    q = Q()
    for kw in obgyn_keywords:
        q |= Q(chief_complaint__icontains=kw)
    return Visit.objects.filter(
        visit_date__gte=start,
        visit_date__lt=end,
        is_deleted=False,
    ).filter(q).distinct().count()


def get_newborn_deliveries(year, month):
    """Newborn-related visits."""
    from clinical.models import Visit
    start, end = _month_range(year, month)
    return Visit.objects.filter(
        visit_date__gte=start,
        visit_date__lt=end,
        is_deleted=False,
    ).filter(
        Q(chief_complaint__icontains='newborn') |
        Q(chief_complaint__icontains='delivery') |
        Q(chief_complaint__icontains='neonatal')
    ).distinct().count()


def get_top_diagnoses(year, month, limit=10):
    """Top N diagnoses by frequency."""
    from clinical.models import Diagnosis
    start, end = _month_range(year, month)
    return list(
        Diagnosis.objects.filter(
            coded_at__gte=start,
            coded_at__lt=end,
        ).values('diagnosis_code', 'diagnosis_description')
        .annotate(count=Count('id'))
        .order_by('-count')[:limit]
    )


def get_mortality_count(year, month):
    """Count of deceased patients."""
    from patients.models import Patient
    start, end = _month_range(year, month)
    return Patient.objects.filter(
        status='deceased',
        updated_at__gte=start,
        updated_at__lt=end,
    ).count()


def get_lab_orders_count(year, month):
    """Number of laboratory orders."""
    from clinical.models import Order
    start, end = _month_range(year, month)
    return Order.objects.filter(
        order_type='laboratory',
        ordered_at__gte=start,
        ordered_at__lt=end,
    ).count()


def get_radiology_orders_count(year, month):
    """Number of radiology orders."""
    from clinical.models import Order
    start, end = _month_range(year, month)
    return Order.objects.filter(
        order_type='radiology',
        ordered_at__gte=start,
        ordered_at__lt=end,
    ).count()


def get_prescriptions_count(year, month):
    """Number of prescriptions issued."""
    from pharmacy.models import Prescription
    start, end = _month_range(year, month)
    return Prescription.objects.filter(
        prescribed_at__gte=start,
        prescribed_at__lt=end,
    ).count()


def get_medications_dispensed_count(year, month):
    """Number of medication dispensing records."""
    from pharmacy.models import MedicationDispensing
    start, end = _month_range(year, month)
    return MedicationDispensing.objects.filter(
        dispensed_at__gte=start,
        dispensed_at__lt=end,
    ).count()


def get_revenue_collected(year, month):
    """Total revenue collected via payments."""
    from billing.models import Payment
    start, end = _month_range(year, month)
    result = Payment.objects.filter(
        payment_date__gte=start,
        payment_date__lt=end,
        is_deleted=False,
    ).aggregate(total=Sum('amount'))
    return result['total'] or Decimal('0.00')


def get_hmis_summary(year, month):
    """Build a complete HMIS summary dictionary."""
    return {
        'period': f'{year}-{month:02d}',
        'org_unit': 'Jackson F. Doe Memorial Regional Referral Hospital',
        'org_unit_code': 'JFDMRRH_LBR',
        'indicators': {
            'total_attendance': get_total_attendance(year, month),
            'opd_attendance': get_opd_attendance(year, month),
            'er_attendance': get_er_attendance(year, month),
            'ipd_admissions': get_ipd_admissions(year, month),
            'maternal_deliveries': get_maternal_deliveries(year, month),
            'newborn_deliveries': get_newborn_deliveries(year, month),
            'lab_orders': get_lab_orders_count(year, month),
            'radiology_orders': get_radiology_orders_count(year, month),
            'prescriptions_issued': get_prescriptions_count(year, month),
            'medications_dispensed': get_medications_dispensed_count(year, month),
            'mortality_count': get_mortality_count(year, month),
            'revenue_collected': str(get_revenue_collected(year, month)),
        },
        'top_diagnoses': get_top_diagnoses(year, month, limit=10),
    }


def build_dhis2_payload(year, month):
    """
    Build a DHIS2-compatible dataValueSets JSON payload.
    Format: https://docs.dhis2.org/2.36/en/dhis2_developer_manual/html/
    """
    org_unit = 'JFDMRRH_LBR'
    period = f'{year}{month:02d}'
    data_set = 'JFD_HMS_HMIS_REPORT'

    data_values = [
        {'dataElement': 'TOTAL_ATTENDANCE', 'value': get_total_attendance(year, month)},
        {'dataElement': 'OPD_ATTENDANCE', 'value': get_opd_attendance(year, month)},
        {'dataElement': 'ER_ATTENDANCE', 'value': get_er_attendance(year, month)},
        {'dataElement': 'IPD_ADMISSIONS', 'value': get_ipd_admissions(year, month)},
        {'dataElement': 'MATERNAL_DELIVERIES', 'value': get_maternal_deliveries(year, month)},
        {'dataElement': 'NEWBORN_DELIVERIES', 'value': get_newborn_deliveries(year, month)},
        {'dataElement': 'LAB_ORDERS', 'value': get_lab_orders_count(year, month)},
        {'dataElement': 'RAD_ORDERS', 'value': get_radiology_orders_count(year, month)},
        {'dataElement': 'PRESCRIPTIONS', 'value': get_prescriptions_count(year, month)},
        {'dataElement': 'MEDICATIONS_DISPENSED', 'value': get_medications_dispensed_count(year, month)},
        {'dataElement': 'MORTALITY_COUNT', 'value': get_mortality_count(year, month)},
        {'dataElement': 'REVENUE_COLLECTED', 'value': str(get_revenue_collected(year, month))},
    ]

    top_diag = get_top_diagnoses(year, month, limit=10)
    for i, diag in enumerate(top_diag[:10], 1):
        data_values.append({
            'dataElement': f'TOP_DIAGNOSIS_{i}',
            'value': diag['count'],
            'comment': f"{diag.get('diagnosis_code', 'N/A')}: {diag.get('diagnosis_description', 'N/A')}",
        })

    return {
        'dataSet': data_set,
        'completeDataDivs': False,
        'period': period,
        'orgUnit': org_unit,
        'dataValues': data_values,
    }
