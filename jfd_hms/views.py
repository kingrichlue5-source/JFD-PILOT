from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count, Sum, Q, F
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
from datetime import date, timedelta
from jfd_hms.permissions import require_permission
import json
import logging
import traceback
from django.http import JsonResponse

logger = logging.getLogger(__name__)


def _get_default_dashboard(user):
    if user.is_superuser:
        return '/'
    try:
        from users_auth.models import UserRole
        role_codes = set(UserRole.objects.filter(
            user=user, is_active=True
        ).values_list('role__code', flat=True))
        if 'CASHIER' in role_codes:
            return '/cashier/'
        if 'PHARMACIST' in role_codes:
            return '/pharmacy/dispensing/'
        if 'TRIAGE_NURSE' in role_codes:
            return '/clinical/triage/'
        if 'INV_MGR' in role_codes:
            return '/inventory/'
        if 'LAB_TECH' in role_codes:
            return '/clinical/diagnostics/'
        if 'DOCTOR' in role_codes:
            return '/opd/'
    except Exception:
        pass
    return '/'


@csrf_exempt
def login_view(request):
    get_token(request)  # Ensure CSRF cookie is set for frontend JS
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            password = data.get('password', '')
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'error': 'Invalid request body'}, status=400)

        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
        if ip:
            ip = ip.split(',')[0].strip()
        ua = request.META.get('HTTP_USER_AGENT', '')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                from audit.models import LoginLog
                LoginLog.objects.create(
                    user_id=user.id, username=username, success=True,
                    ip_address=ip, user_agent=ua
                )
                return JsonResponse({
                    'user': {
                        'id': str(user.id),
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                    },
                    'redirect_url': _get_default_dashboard(user),
                    'message': 'Login successful'
                })
            else:
                from audit.models import LoginLog
                LoginLog.objects.create(
                    user_id=None, username=username, success=False,
                    failure_reason='Account disabled', ip_address=ip, user_agent=ua
                )
                return JsonResponse({'error': 'Account is disabled'}, status=401)
        else:
            from audit.models import LoginLog
            LoginLog.objects.create(
                user_id=None, username=username, success=False,
                failure_reason='Invalid credentials', ip_address=ip, user_agent=ua
            )
            return JsonResponse({'error': 'Invalid username or password'}, status=401)
    if request.user.is_authenticated:
        return redirect('index')
    return render(request, 'registration/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='/login/')
def index(request):
    from patients.models import Patient
    from clinical.models import Visit, Admission, Bed, Encounter, Order
    from billing.models import Invoice, Payment
    from pharmacy.models import Prescription, MedicationDispensing
    from inventory.models import Stock

    today = date.today()
    week_ago = today - timedelta(days=7)

    total_patients = Patient.objects.filter(is_deleted=False).count()
    today_visits = Visit.objects.filter(visit_date=today, is_deleted=False).count()
    active_admissions = Admission.objects.filter(status='active').count()
    total_beds = Bed.objects.filter(is_active=True).count()
    occupied_beds = Bed.objects.filter(is_active=True, is_occupied=True).count()
    pending_invoices = Invoice.objects.filter(status='pending', is_deleted=False).count()
    today_payments = Payment.objects.filter(payment_date__date=today, is_deleted=False).aggregate(total=Sum('amount'))['total'] or 0
    pending_prescriptions = Prescription.objects.filter(status='pending').count()
    pending_orders = Order.objects.filter(status='pending').count()
    low_stock_count = Stock.objects.filter(
        item__reorder_level__gt=0, quantity_on_hand__lte=10, item__is_active=True
    ).count()

    from clinical.models import TriageRecord
    triage_today_count = TriageRecord.objects.filter(triage_time__date=today).count()
    triage_completed_today = TriageRecord.objects.filter(
        triage_time__date=today
    ).exclude(visit__status='checked_in').count()
    triage_critical_count = TriageRecord.objects.filter(
        triage_time__date=today, acuity_level__lte=2
    ).count()

    recent_visits = Visit.objects.filter(
        is_deleted=False, visit_date=today
    ).select_related('patient', 'department', 'provider').order_by('-check_in_time')[:10]

    triage_queue = Visit.objects.filter(
        status__in=['checked_in', 'in_triage'], is_deleted=False
    ).select_related('patient').order_by('triage_priority', 'check_in_time')[:10]

    er_queue = Visit.objects.filter(
        visit_type='er', status__in=['checked_in', 'in_triage'], is_deleted=False
    ).select_related('patient')[:5]

    ward_occupancy = []
    for ward in Bed.objects.filter(is_active=True, room__ward__is_active=True).values(
        ward_name=F('room__ward__name'), ward_code=F('room__ward__code')
    ).annotate(
        total=Count('id'),
        occupied=Count('id', filter=Q(is_occupied=True)),
    ):
        ward['available'] = ward['total'] - ward['occupied']
        ward['occupancy_rate'] = round(ward['occupied'] / ward['total'] * 100) if ward['total'] > 0 else 0
        ward_occupancy.append(ward)

    context = {
        'total_patients': total_patients,
        'today_visits': today_visits,
        'active_admissions': active_admissions,
        'total_beds': total_beds,
        'occupied_beds': occupied_beds,
        'available_beds': total_beds - occupied_beds,
        'bed_occupancy_pct': round(occupied_beds / total_beds * 100) if total_beds > 0 else 0,
        'pending_invoices': pending_invoices,
        'today_payments': today_payments,
        'pending_prescriptions': pending_prescriptions,
        'pending_orders': pending_orders,
        'low_stock_count': low_stock_count,
        'recent_visits': recent_visits,
        'triage_queue': triage_queue,
        'er_queue': er_queue,
        'ward_occupancy': ward_occupancy,
        'triage_today_count': triage_today_count,
        'triage_completed_today': triage_completed_today,
        'triage_critical_count': triage_critical_count,
        'today': today,
    }
    return render(request, 'index.html', context)

@login_required(login_url='/login/')
def patient_search(request):
    return render(request, 'patients/search.html')

@login_required(login_url='/login/')
def patient_register(request):
    from patients.forms import PatientRegistrationForm
    from patients.models import Patient
    from clinical.models import Visit, TriageRecord
    from django.contrib import messages
    from audit.utils import log_audit

    visit_id = request.GET.get('visit_id') or request.POST.get('visit_id')
    existing_visit = None
    triage_record = None
    if visit_id:
        try:
            existing_visit = Visit.objects.get(id=visit_id, is_deleted=False)
            triage_record = TriageRecord.objects.filter(visit=existing_visit).order_by('-created_at').first()
        except Visit.DoesNotExist:
            pass

    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user if request.user.is_authenticated else None
            patient = form.save(commit=False)
            patient.registered_by = user.id if user else None
            patient.save()

            visit_type = form.cleaned_data.get('visit_type', 'opd')
            chief_complaint = form.cleaned_data.get('chief_complaint', '')

            if existing_visit:
                existing_visit.patient = patient
                existing_visit.chief_complaint = chief_complaint or existing_visit.chief_complaint
                existing_visit.visit_type = visit_type
                existing_visit.status = 'in_progress'
                existing_visit.save()
                visit = existing_visit
                for model_class in [TriageRecord]:
                    model_class.objects.filter(visit=visit, patient__isnull=True).update(patient=patient)
            else:
                visit = Visit.objects.create(
                    patient=patient,
                    visit_type=visit_type,
                    chief_complaint=chief_complaint,
                    status='checked_in',
                    check_in_time=timezone.now(),
                    created_by=user.id if user else None
                )

            log_audit('patients', 'patients', patient.id, 'CREATE',
                      new_values={'mrn': patient.mrn, 'first_name': patient.first_name, 'last_name': patient.last_name},
                      request=request)
            log_audit('clinical', 'visits', visit.id, 'CREATE',
                      new_values={'visit_number': visit.visit_number, 'visit_type': visit.visit_type, 'status': visit.status},
                      request=request)

            try:
                from billing.services import post_registration_fee_to_invoice
                post_registration_fee_to_invoice(patient, visit)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f'Registration fee posting failed: {e}')

            doc_files = request.FILES.getlist('documents')
            for f in doc_files:
                from patients.models import PatientDocument
                from django.core.files.storage import default_storage
                path = default_storage.save(f'documents/{patient.id}/{f.name}', f)
                doc_url = default_storage.url(path)
                PatientDocument.objects.create(
                    patient=patient,
                    document_type='registration',
                    document_name=f.name,
                    file_url=doc_url,
                    file_size=f.size,
                    mime_type=f.content_type or '',
                    uploaded_by=user.id if user else None,
                )

            messages.success(request, f'Patient {patient.mrn} registered! Visit {visit.visit_number} created.')
            if existing_visit:
                return redirect('triage-pending-page')
            return redirect('patient-register-page')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        initial = {}
        if existing_visit:
            initial['chief_complaint'] = existing_visit.chief_complaint or ''
            initial['visit_type'] = existing_visit.visit_type or 'opd'
            if existing_visit.patient:
                for field in ['first_name', 'last_name', 'middle_name', 'date_of_birth', 'gender', 'phone']:
                    initial[field] = getattr(existing_visit.patient, field, '')
        form = PatientRegistrationForm(initial=initial)

    return render(request, 'patients/register.html', {
        'form': form,
        'existing_visit': existing_visit,
        'triage_record': triage_record,
    })


@login_required(login_url='/login/')
@require_permission('PATIENT_CREATE')
def triage_awaiting_registration(request):
    from clinical.models import Visit
    pending_visits = Visit.objects.filter(
        status='pending_registration', is_deleted=False
    ).select_related('patient').order_by('check_in_time')
    return render(request, 'clinical/triage_awaiting.html', {
        'pending_visits': pending_visits,
    })


@login_required(login_url='/login/')
@require_permission('ENCOUNTER_VIEW')
def follow_up_queue(request):
    from clinical.models import Visit
    from users_auth.models import HospitalSetting
    from datetime import date, timedelta
    setting = HospitalSetting.get_settings()
    window = setting.followup_window_days
    today = date.today()
    window_start = today - timedelta(days=window)
    window_end = today + timedelta(days=window)
    follow_up_visits = Visit.objects.filter(
        is_follow_up=True,
        follow_up_date__isnull=False,
        follow_up_date__gte=window_start,
        status__in=['scheduled', 'checked_in', 'in_progress'],
        is_deleted=False,
    ).select_related('patient').order_by('follow_up_date')
    overdue_visits = Visit.objects.filter(
        is_follow_up=True,
        follow_up_date__lt=window_start,
        status__in=['scheduled', 'checked_in', 'in_progress'],
        is_deleted=False,
    ).select_related('patient').order_by('follow_up_date')
    upcoming_visits = Visit.objects.filter(
        is_follow_up=True,
        follow_up_date__gt=window_end,
        follow_up_date__gte=today,
        status__in=['scheduled'],
        is_deleted=False,
    ).select_related('patient').order_by('follow_up_date')[:20]
    return render(request, 'clinical/follow_up_queue.html', {
        'follow_up_visits': follow_up_visits,
        'overdue_visits': overdue_visits,
        'upcoming_visits': upcoming_visits,
        'window_days': window,
        'today': today,
    })


@login_required(login_url='/login/')
@require_permission('TRIAGE_PERFORM')
def triage_dashboard(request):
    from clinical.forms import TriageForm
    from audit.utils import log_audit
    if request.method == 'POST':
        form = TriageForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                triage_record, routing, visit = form.process(user=request.user, files=request.FILES)
                log_audit('clinical', 'triage_records', triage_record.id, 'CREATE',
                          new_values={
                              'visit_id': str(visit.id),
                              'patient_id': str(visit.patient_id),
                              'acuity_level': triage_record.acuity_level,
                              'chief_complaint': triage_record.chief_complaint,
                          },
                          request=request)
                log_audit('clinical', 'visits', visit.id, 'UPDATE',
                          old_values={'status': 'checked_in'},
                          new_values={'status': visit.status, 'triage_priority': visit.triage_priority},
                          request=request)
                messages.success(request, 'Triage completed! Patient awaiting registration.')
                return redirect('triage-dashboard-page')
            except Exception as e:
                messages.error(request, f'Triage submission error: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    return render(request, 'clinical/triage.html')

@login_required(login_url='/login/')
def triage_ticket(request):
    return render(request, 'clinical/triage_ticket.html')

@login_required(login_url='/login/')
def opd_consultation(request):
    visit_id = request.GET.get('visit_id', '')
    encounter_id = request.GET.get('encounter_id', '')
    if request.method == 'POST':
        from clinical.forms import EncounterForm
        from audit.utils import log_audit
        form = EncounterForm(request.POST)
        if form.is_valid():
            try:
                encounter = form.process(user=request.user)
                log_audit('clinical', 'encounters', encounter.id, 'UPDATE',
                          new_values={
                              'status': encounter.status,
                              'is_finalized': encounter.is_finalized,
                              'subjective': encounter.subjective[:200] if encounter.subjective else '',
                              'assessment': encounter.assessment[:200] if encounter.assessment else '',
                          },
                          request=request)
                messages.success(request, 'Encounter finalized! Orders and prescriptions sent to billing.')
                vid = request.POST.get("visit_id", "")
                return redirect(f'/opd/?visit_id={vid}&encounter_id={encounter.id}')
            except Exception as e:
                messages.error(request, f'Error saving encounter: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    visit_status = ''
    if visit_id:
        try:
            from clinical.models import Visit
            visit = Visit.objects.get(id=visit_id)
            visit_status = visit.status
        except Exception:
            pass
    return render(request, 'clinical/opd_consultation.html', {
        'visit_id': visit_id,
        'encounter_id': encounter_id,
        'visit_status': visit_status,
    })

@login_required(login_url='/login/')
def ipd_dashboard(request):
    from clinical.models import Bed, Ward, Admission
    beds = Bed.objects.select_related('room__ward').filter(is_active=True)
    wards = Ward.objects.filter(is_active=True)
    admissions = Admission.objects.filter(status='active').select_related('patient')
    total_beds = beds.count()
    occupied_count = admissions.filter(bed__isnull=False).count()
    pending_count = admissions.filter(bed__isnull=True).count()
    available_beds = total_beds - occupied_count - pending_count
    occupancy_rate = round(occupied_count / total_beds * 100) if total_beds > 0 else 0

    beds_by_ward = {}
    for bed in beds:
        ward_name = bed.room.ward.name if bed.room and bed.room.ward else 'Unknown'
        if ward_name not in beds_by_ward:
            beds_by_ward[ward_name] = {'ward_id': str(bed.room.ward.id) if bed.room and bed.room.ward else '', 'beds': []}
        admission = None
        for a in admissions:
            if hasattr(a, 'bed_id') and a.bed_id == bed.id:
                admission = a
                break
        beds_by_ward[ward_name]['beds'].append({
            'id': str(bed.id),
            'bed_number': bed.bed_number,
            'room_number': bed.room.room_number if bed.room else '',
            'bed_type': bed.bed_type,
            'is_occupied': bed.is_occupied,
                'admission': {
                'id': str(admission.id),
                'patient_name': f"{admission.patient.first_name} {admission.patient.last_name}" if admission.patient else 'Unknown',
                'diagnosis': getattr(admission, 'admitting_diagnosis', ''),
                'admission_date': admission.admission_date if hasattr(admission, 'admission_date') else admission.created_at,
            } if admission else None,
        })

    context = {
        'total_beds': total_beds,
        'occupied_beds': occupied_count,
        'pending_admissions': pending_count,
        'available_beds': max(available_beds, 0),
        'occupancy_rate': occupancy_rate,
        'active_inpatients': admissions.count(),
        'wards_count': wards.count(),
        'beds_by_ward': beds_by_ward,
        'wards': wards,
        'admissions': admissions,
        'unassigned_admissions': admissions.filter(bed__isnull=True),
    }
    return render(request, 'clinical/ipd.html', context)

@login_required(login_url='/login/')
def emergency_dashboard(request):
    from clinical.models import Visit
    from clinical.models import Admission, ERNurseEvaluation, ProgressNote
    from datetime import date

    today = date.today()

    active_cases = Visit.objects.filter(
        visit_type='er', status__in=['checked_in', 'in_progress'], is_deleted=False
    ).select_related('patient').order_by('triage_priority', 'check_in_time')

    evaluated_visit_ids = set(
        ERNurseEvaluation.objects.filter(
            visit__in=active_cases
        ).values_list('visit_id', flat=True)
    )

    intervened_visit_ids = set(
        ProgressNote.objects.filter(
            encounter__visit__in=active_cases,
            note_type='progress'
        ).values_list('encounter__visit_id', flat=True)
    )

    completed_today = Visit.objects.filter(
        visit_type='er', status='completed', visit_date=today, is_deleted=False
    ).select_related('patient')

    awaiting_disposition = Visit.objects.filter(
        visit_type='er', status__in=['checked_in', 'in_triage'], is_deleted=False
    ).count()

    admitted_from_er = Admission.objects.filter(
        visit__visit_type='er', visit__visit_date=today, status='active'
    ).count()

    context = {
        'active_cases': active_cases,
        'completed_today': completed_today,
        'active_count': active_cases.count(),
        'awaiting_disposition': awaiting_disposition,
        'discharged_today': completed_today.count(),
        'admitted_from_er': admitted_from_er,
        'evaluated_visit_ids': evaluated_visit_ids,
        'intervened_visit_ids': intervened_visit_ids,
        'er_visits': [
            {'id': str(v.id), 'patient_name': str(v.patient), 'chief_complaint': v.chief_complaint or ''}
            for v in active_cases
        ],
    }
    return render(request, 'clinical/emergency.html', context)

@login_required(login_url='/login/')
def obgyn_dashboard(request):
    return render(request, 'clinical/obgyn.html')

@login_required(login_url='/login/')
def surgery_dashboard(request):
    return render(request, 'clinical/surgery.html')

@login_required(login_url='/login/')
@require_permission('ORDER_VIEW')
def diagnostics_dashboard(request):
    return render(request, 'clinical/diagnostics.html')

@login_required(login_url='/login/')
@require_permission('RX_VIEW')
def pharmacy_dispensing(request):
    if request.method == 'POST':
        from pharmacy.forms import DispensingForm
        from audit.utils import log_audit
        form = DispensingForm(request.POST)
        if form.is_valid():
            confirm = request.POST.get('confirm_warnings', '')
            if confirm != 'yes':
                warnings = form.check_allergies()
                if warnings:
                    context = {'pending_warnings': warnings, 'pending_form': request.POST}
                    return render(request, 'pharmacy/dispensing.html', context)
            try:
                dispensing = form.process(user=request.user)
                log_audit('pharmacy', 'medication_dispensings', dispensing.id, 'CREATE',
                          new_values={
                              'medication_id': str(dispensing.medication_id),
                              'patient_id': str(dispensing.patient_id),
                              'prescription_item_id': str(dispensing.prescription_item_id),
                              'quantity_dispensed': dispensing.quantity_dispensed,
                              'batch_lot_number': dispensing.batch_lot_number,
                          },
                          request=request)
                messages.success(request, 'Medication dispensed successfully! Stock deducted and billing posted.')
                return redirect('pharmacy-dispensing-page')
            except Exception as e:
                messages.error(request, f'Dispensing error: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    return render(request, 'pharmacy/dispensing.html')

@login_required(login_url='/login/')
@require_permission('INVOICE_VIEW')
def cashier(request):
    from billing.forms import PaymentForm, CashierShiftForm
    from billing.models import Invoice, CashierShift, Payment
    from django.db.models import Sum
    from audit.utils import log_audit

    if request.method == 'POST':
        action = request.POST.get('action', 'payment')
        if action == 'shift':
            form = CashierShiftForm(request.POST)
            if form.is_valid():
                try:
                    shift = form.process(user=request.user)
                    log_audit('billing', 'cashier_shifts', shift.id, 'CREATE',
                              new_values={
                                  'opening_balance': str(shift.opening_balance),
                                  'status': shift.status,
                              },
                              request=request)
                    messages.success(request, 'Cashier shift started!')
                    return redirect('cashier')
                except Exception as e:
                    messages.error(request, f'Shift error: {str(e)}')
        elif action == 'waive':
            from billing.forms import WaiveForm
            form = WaiveForm(request.POST)
            if form.is_valid():
                try:
                    payment = form.process(user=request.user)
                    log_audit('billing', 'payments', payment.id, 'CREATE',
                              new_values={
                                  'invoice_id': str(payment.invoice_id),
                                  'patient_id': str(payment.patient_id),
                                  'amount': str(payment.amount),
                                  'payment_method': payment.payment_method,
                                  'reference_number': payment.reference_number,
                              },
                              request=request)
                    messages.success(request, 'Invoice waived!')
                    return redirect('cashier')
                except Exception as e:
                    messages.error(request, f'Waiver error: {str(e)}')
        else:
            form = PaymentForm(request.POST)
            if form.is_valid():
                try:
                    payment = form.process(user=request.user)
                    log_audit('billing', 'payments', payment.id, 'CREATE',
                              new_values={
                                  'invoice_id': str(payment.invoice_id),
                                  'patient_id': str(payment.patient_id),
                                  'amount': str(payment.amount),
                                  'payment_method': payment.payment_method,
                                  'reference_number': payment.reference_number,
                                  'receipt_number': payment.receipt_number,
                              },
                              request=request)
                    return redirect('receipt-page', payment_id=payment.id)
                except Exception as e:
                    messages.error(request, f'Payment error: {str(e)}')

    today = date.today()

    invoices = Invoice.objects.filter(
        status__in=['pending', 'partial'], is_deleted=False, balance_due__gt=0
    ).select_related('patient').order_by('-invoice_date')

    search = request.GET.get('search', '')
    if search:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search) |
            Q(patient__mrn__icontains=search) |
            Q(patient__first_name__icontains=search) |
            Q(patient__last_name__icontains=search)
        )

    shift = CashierShift.objects.filter(
        cashier=request.user, status='open'
    ).first()

    today_payments = Payment.objects.filter(
        payment_date__date=today, is_deleted=False
    )
    revenue = today_payments.aggregate(
        cash_total=Sum('amount', filter=Q(payment_method='cash')),
        mobile_total=Sum('amount', filter=Q(payment_method='mobile_money')),
        insurance_total=Sum('amount', filter=Q(payment_method='insurance')),
    )
    today_revenue = {
        'cash_total': revenue['cash_total'] or 0,
        'mobile_total': revenue['mobile_total'] or 0,
        'insurance_total': revenue['insurance_total'] or 0,
    }
    today_revenue['total'] = today_revenue['cash_total'] + today_revenue['mobile_total'] + today_revenue['insurance_total']

    outstanding = Invoice.objects.filter(
        status__in=['pending', 'partial'], is_deleted=False, balance_due__gt=0
    ).aggregate(total=Sum('balance_due'))['total'] or 0

    context = {
        'invoices': invoices,
        'shift': shift,
        'today_revenue': today_revenue,
        'outstanding_total': outstanding,
        'search': search,
    }
    return render(request, 'billing/cashier.html', context)

@login_required(login_url='/login/')
@require_permission('PAYMENT_PROCESS')
def payment_history(request):
    from billing.models import Invoice, Payment
    from clinical.models import Visit, Encounter
    from django.db.models import Q, Sum

    payments = Payment.objects.filter(
        is_deleted=False
    ).select_related('invoice', 'patient', 'received_by', 'cashier_shift').order_by('-payment_date')

    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    method_filter = request.GET.get('method', '')

    if search:
        payments = payments.filter(
            Q(invoice__invoice_number__icontains=search) |
            Q(patient__mrn__icontains=search) |
            Q(patient__first_name__icontains=search) |
            Q(patient__last_name__icontains=search) |
            Q(receipt_number__icontains=search) |
            Q(reference_number__icontains=search)
        )
    if date_from:
        payments = payments.filter(payment_date__date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__date__lte=date_to)
    if method_filter:
        payments = payments.filter(payment_method=method_filter)

    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0

    payment_data = []
    for p in payments:
        visit_type = ''
        encounter_type = ''
        if p.invoice and p.invoice.visit:
            visit_type = p.invoice.visit.get_visit_type_display() if hasattr(p.invoice.visit, 'get_visit_type_display') else p.invoice.visit.visit_type
            enc = Encounter.objects.filter(visit=p.invoice.visit).order_by('-encounter_date').first()
            if enc:
                encounter_type = enc.get_encounter_type_display() if hasattr(enc, 'get_encounter_type_display') else enc.encounter_type
        payment_data.append({
            'payment': p,
            'visit_type': visit_type,
            'encounter_type': encounter_type,
        })

    context = {
        'payment_data': payment_data,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'method_filter': method_filter,
        'total_amount': total_amount,
        'count': payments.count(),
    }
    return render(request, 'billing/payment_history.html', context)

@login_required(login_url='/login/')
def invoice_detail(request, invoice_id=None):
    from billing.models import Invoice, InvoiceLineItem, Payment
    context = {'invoice_id': invoice_id}
    if invoice_id:
        try:
            invoice = Invoice.objects.select_related('patient', 'visit').get(id=invoice_id)
            line_items = InvoiceLineItem.objects.filter(invoice=invoice).select_related('service_item')
            payments = Payment.objects.filter(invoice=invoice).order_by('payment_date')
            patient_name = f"{invoice.patient.first_name} {invoice.patient.middle_name or ''} {invoice.patient.last_name}".replace('  ', ' ').strip()
            context.update({
                'invoice': invoice,
                'line_items': line_items,
                'payments': payments,
                'patient_name': patient_name,
            })
        except Invoice.DoesNotExist:
            pass
    return render(request, 'billing/invoice_detail.html', context)

@login_required(login_url='/login/')
def receipt_detail(request, payment_id):
    from billing.models import Payment, Invoice, InvoiceLineItem
    payment = Payment.objects.select_related('patient', 'invoice', 'received_by').get(id=payment_id)
    invoice = payment.invoice
    line_items = InvoiceLineItem.objects.filter(invoice=invoice)
    patient_name = f"{payment.patient.first_name} {payment.patient.middle_name or ''} {payment.patient.last_name}".replace('  ', ' ').strip()
    cashier_name = ''
    if payment.received_by:
        cashier_name = f"{payment.received_by.first_name} {payment.received_by.last_name}".strip()
    previous_paid = invoice.amount_paid - payment.amount if invoice.amount_paid else 0
    change_due = None
    if payment.payment_method == 'cash':
        tendered = float(payment.amount)
        inv_total = float(invoice.total_amount)
        if tendered > inv_total:
            change_due = f"{tendered - inv_total:.2f}"
    return render(request, 'billing/receipt.html', {
        'payment': payment,
        'invoice': invoice,
        'line_items': line_items,
        'patient_name': patient_name,
        'cashier_name': cashier_name or 'System',
        'previous_paid': f"{previous_paid:.2f}" if previous_paid else '0.00',
        'change_due': change_due,
    })

@login_required(login_url='/login/')
@login_required(login_url='/login/')
@require_permission('INVENTORY_VIEW')
def inventory_dashboard(request):
    return render(request, 'inventory/stock.html')


@login_required(login_url='/login/')
@require_permission('INVENTORY_MANAGE')
def inventory_management(request):
    return render(request, 'inventory/management.html')

@login_required(login_url='/login/')
def appointments_dashboard(request):
    return render(request, 'clinical/appointments.html')

@login_required(login_url='/login/')
def vital_events_dashboard(request):
    return render(request, 'vital_events/certificates.html')

@login_required(login_url='/login/')
def hmis_dashboard(request):
    return render(request, 'reports/hmis_dashboard.html')


@login_required(login_url='/login/')
def er_nurse_evaluation(request):
    from clinical.models import ERNurseEvaluation, Visit
    visit_id = request.GET.get('visit_id') or request.POST.get('visit_id')
    visit = None
    if visit_id:
        try:
            visit = Visit.objects.get(id=visit_id, is_deleted=False)
        except Visit.DoesNotExist:
            pass
    if request.method == 'POST':
        from django.contrib import messages
        from audit.utils import log_audit
        try:
            eval_data = {
                'visit': visit,
                'patient': visit.patient,
                'mode_of_arrival': request.POST.get('mode_of_arrival', ''),
                'accompanied_by': request.POST.get('accompanied_by', ''),
                'chief_complaint': request.POST.get('chief_complaint', ''),
                'hpi_onset': request.POST.get('hpi_onset', ''),
                'hpi_location': request.POST.get('hpi_location', ''),
                'hpi_character': request.POST.get('hpi_character', ''),
                'hpi_severity': request.POST.get('hpi_severity', ''),
                'hpi_aggravating': request.POST.get('hpi_aggravating', ''),
                'hpi_alleviating': request.POST.get('hpi_alleviating', ''),
                'pmh_chronic_illness': request.POST.get('pmh_chronic_illness', ''),
                'pmh_previous_surgery': request.POST.get('pmh_previous_surgery', ''),
                'pmh_allergies': request.POST.get('pmh_allergies', ''),
                'pmh_medications': request.POST.get('pmh_medications', ''),
                'ros_fever': request.POST.get('ros_fever') == 'on',
                'ros_chest_pain': request.POST.get('ros_chest_pain') == 'on',
                'ros_cough': request.POST.get('ros_cough') == 'on',
                'ros_wheeze': request.POST.get('ros_wheeze') == 'on',
                'ros_bleeding': request.POST.get('ros_bleeding') == 'on',
                'ros_shortness_of_breath': request.POST.get('ros_shortness_of_breath') == 'on',
                'ros_vomiting': request.POST.get('ros_vomiting') == 'on',
                'ros_rash': request.POST.get('ros_rash') == 'on',
                'ros_diarrhea': request.POST.get('ros_diarrhea') == 'on',
                'ros_abdominal_pain': request.POST.get('ros_abdominal_pain') == 'on',
                'ros_trauma': request.POST.get('ros_trauma') == 'on',
                'bp_systolic': request.POST.get('bp_systolic') or None,
                'bp_diastolic': request.POST.get('bp_diastolic') or None,
                'heart_rate': request.POST.get('heart_rate') or None,
                'sp_o2': request.POST.get('sp_o2') or None,
                'temperature': request.POST.get('temperature') or None,
                'respiratory_rate': request.POST.get('respiratory_rate') or None,
                'exam_heent': request.POST.get('exam_heent', ''),
                'exam_cvs': request.POST.get('exam_cvs', ''),
                'exam_respiratory': request.POST.get('exam_respiratory', ''),
                'exam_abdomen': request.POST.get('exam_abdomen', ''),
                'exam_gus': request.POST.get('exam_gus', ''),
                'exam_musculoskeletal': request.POST.get('exam_musculoskeletal', ''),
                'exam_cns': request.POST.get('exam_cns', ''),
                'triage_category': request.POST.get('triage_category', ''),
                'intervention_oxygen': request.POST.get('intervention_oxygen') == 'on',
                'intervention_iv_fluids': request.POST.get('intervention_iv_fluids') == 'on',
                'intervention_blood_transfusion': request.POST.get('intervention_blood_transfusion') == 'on',
                'intervention_analgesics': request.POST.get('intervention_analgesics') == 'on',
                'intervention_suturing': request.POST.get('intervention_suturing') == 'on',
                'intervention_antibiotics': request.POST.get('intervention_antibiotics') == 'on',
                'intervention_antipyretics': request.POST.get('intervention_antipyretics') == 'on',
                'intervention_specimen_collection': request.POST.get('intervention_specimen_collection') == 'on',
                'intervention_collect_results': request.POST.get('intervention_collect_results') == 'on',
                'physician_notified': request.POST.get('physician_notified') == 'on',
                'physician_notified_time': request.POST.get('physician_notified_time') or None,
                'physician_arrival_time': request.POST.get('physician_arrival_time') or None,
                'physicians_order': request.POST.get('physicians_order', ''),
                'pending_orders': request.POST.get('pending_orders', ''),
                'disposition': request.POST.get('disposition', ''),
                'remarks': request.POST.get('remarks', ''),
                'completed_by': request.user,
            }
            evaluation = ERNurseEvaluation.objects.create(**eval_data)
            log_audit('clinical', 'er_nurse_evaluations', str(evaluation.id), 'CREATE', new_values={'patient': str(visit.patient.mrn)}, request=request)
            messages.success(request, 'ER Nurse Evaluation saved successfully!')
            return redirect(f'/clinical/er-evaluation/?visit_id={visit_id}')
        except Exception as e:
            messages.error(request, f'Error saving evaluation: {str(e)}')
    return render(request, 'clinical/er_nurse_evaluation.html', {'visit': visit})


@login_required(login_url='/login/')
def pediatric_assessment(request):
    from clinical.models import PediatricAssessment, Visit
    from patients.models import Patient
    from datetime import date

    visit_id = request.GET.get('visit_id') or request.POST.get('visit_id')
    visit = None
    if visit_id:
        try:
            visit = Visit.objects.get(id=visit_id, is_deleted=False)
        except Visit.DoesNotExist:
            pass

    if request.method == 'POST':
        from django.contrib import messages
        from audit.utils import log_audit
        try:
            bool_fields = [
                'lethargy_unconscious', 'convulsing_now', 'not_able_to_drink',
                'vomits_everything', 'history_of_convulsion', 'has_diarrhea',
                'blood_in_stool', 'dehydration_signs', 'dehydration_lethargy',
                'sunken_eyes', 'delayed_capillary_refill', 'poor_skin_turgor',
                'decreased_urine', 'cough_breath_difficulty', 'severe_respiratory_distress',
                'audible_stridor', 'central_cyanosis', 'severe_pallor', 'fever_present',
                'shock_present', 'cold_hands', 'shock_delayed_capillary_refill',
                'rapid_weak_pulse', 'altered_mental_status', 'edema_both_feet',
                'sleeping_under_net',
                'vaccination_bcg', 'vaccination_opv_0', 'vaccination_opv_1',
                'vaccination_opv_2', 'vaccination_opv_3', 'vaccination_penta_1',
                'vaccination_penta_2', 'vaccination_penta_3', 'vaccination_pcv_1',
                'vaccination_pcv_2', 'vaccination_pcv_3', 'vaccination_rota_1',
                'vaccination_rota_2', 'vaccination_rota_3', 'vaccination_measles',
                'vaccination_yellow_fever', 'counselling_danger_signs',
                'counselling_nutrition', 'counselling_medication', 'counselling_follow_up',
            ]
            patient = visit.patient if visit else None
            data = {'visit': visit, 'patient': patient, 'completed_by': request.user}
            data['visit_type'] = request.POST.get('visit_type', '')
            data['card_number'] = request.POST.get('card_number', '')
            data['child_problem'] = request.POST.get('chief_complaint', '') or request.POST.get('child_problem', '')
            data['pulse'] = request.POST.get('shock_heart_rate') or request.POST.get('pulse') or None
            data['respiratory_rate'] = request.POST.get('respiratory_rr') or request.POST.get('respiratory_rate') or None
            data['temperature'] = request.POST.get('temperature') or None
            data['bp'] = request.POST.get('bp', '')
            data['sao2'] = request.POST.get('respiratory_spo2') or request.POST.get('sao2') or None
            data['weight'] = request.POST.get('dehydration_weight') or request.POST.get('respiratory_weight') or request.POST.get('shock_weight') or request.POST.get('weight') or None
            data['height'] = request.POST.get('height') or None
            data['head_circumference'] = request.POST.get('head_circumference') or None
            data['muac'] = request.POST.get('muac_value') or request.POST.get('muac') or None
            data['wt_ht'] = request.POST.get('wt_ht') or None
            danger_map = {
                'danger_dyspnea': 'cough_breath_difficulty',
                'danger_severe_dehydration': 'dehydration_signs',
                'danger_altered_consciousness': 'altered_mental_status',
                'danger_seizures': 'convulsing_now',
                'danger_severe_pallor': 'severe_pallor',
                'danger_severe_malnutrition': 'edema_both_feet',
                'danger_suspected_meningitis': 'lethargy_unconscious',
            }
            for template_field, model_field in danger_map.items():
                if request.POST.get(template_field):
                    data[model_field] = True
            for field in bool_fields:
                if field not in data:
                    data[field] = request.POST.get(field) == 'on'
            data['sleeping_under_net'] = None
            if request.POST.get('sleeping_under_net') == 'on':
                data['sleeping_under_net'] = True
            for f in ['heent_notes', 'chest_notes', 'cvs_notes', 'abdomen_notes',
                       'gu_notes', 'musculoskeletal_notes', 'integumentary_notes', 'cns_notes']:
                data[f] = request.POST.get(f, '')
            inv_parts = []
            for inv_field in ['investigation_cbc', 'investigation_urinalysis', 'investigation_malaria', 'investigation_other']:
                val = request.POST.get(inv_field, '').strip()
                if val:
                    inv_parts.append(f"{inv_field.replace('investigation_', '').upper()}: {val}")
            data['laboratory_investigation'] = ' | '.join(inv_parts) if inv_parts else request.POST.get('laboratory_investigation', '')
            data['provisional_diagnosis'] = request.POST.get('provisional_diagnosis', '')
            data['treatment'] = request.POST.get('treatment', '')
            data['follow_up_notes'] = request.POST.get('follow_up_notes', '')
            data['discharge_diagnosis'] = request.POST.get('discharge_diagnosis', '')
            data['discharge_treatment_course'] = request.POST.get('discharge_treatment_course', '')
            data['counselling_other'] = request.POST.get('counselling_other', '')
            vaccine_map = {
                'vaccine_bcg': 'vaccination_bcg',
                'vaccine_measles': 'vaccination_measles',
            }
            for template_field, model_field in vaccine_map.items():
                val = request.POST.get(template_field, '').strip()
                if val and val.lower() not in ('', 'no', 'none'):
                    data[model_field] = True
            assessment = PediatricAssessment.objects.create(**data)
            log_audit('clinical', 'pediatric_assessments', str(assessment.id), 'CREATE', new_values={'patient': str(patient.mrn) if patient else 'N/A'}, request=request)
            messages.success(request, 'Pediatric assessment saved successfully!')
            return redirect(f'/clinical/pediatric/?visit_id={visit_id}')
        except Exception as e:
            messages.error(request, f'Error saving assessment: {str(e)}')

    # Dashboard mode: list pediatric patients with assessments
    today = date.today()
    pediatric_patients = Patient.objects.filter(
        date_of_birth__isnull=False,
        is_deleted=False,
    ).order_by('-created_at')[:50]

    patient_data = []
    for p in pediatric_patients:
        try:
            age_days = (today - p.date_of_birth).days
            age_years = age_days / 365.25
        except Exception:
            age_years = None
        if age_years is not None and age_years <= 18:
            assessments = PediatricAssessment.objects.filter(patient=p).order_by('-last_modified')[:5]
            patient_data.append({
                'patient': p,
                'age_years': round(age_years, 1) if age_years else None,
                'assessments': assessments,
                'assessment_count': PediatricAssessment.objects.filter(patient=p).count(),
            })

    return render(request, 'clinical/pediatric.html', {
        'visit': visit,
        'patient_data': patient_data,
    })


@login_required(login_url='/login/')
def nurse_notes(request):
    from clinical.models import ProgressNote, Visit
    from clinical.forms import NurseNoteForm
    visit_id = request.GET.get('visit_id') or request.POST.get('visit_id')
    visit = None
    notes = []
    if visit_id:
        try:
            visit = Visit.objects.get(id=visit_id, is_deleted=False)
            notes = ProgressNote.objects.filter(visit=visit, note_type='nursing').order_by('-authored_at')
        except Visit.DoesNotExist:
            pass
    if request.method == 'POST':
        from django.contrib import messages
        form = NurseNoteForm(request.POST)
        if form.is_valid():
            try:
                note = form.process(user=request.user)
                log_audit('clinical', 'progress_notes', str(note.id), 'CREATE', new_values={'patient': str(visit.patient.mrn)}, request=request)
                messages.success(request, 'Nurse note saved!')
                return redirect(f'/clinical/nurse-notes/?visit_id={visit_id}')
            except Exception as e:
                messages.error(request, f'Error saving note: {str(e)}')
        else:
            messages.error(request, 'Invalid form data.')
    form = NurseNoteForm(initial={
        'visit_id': visit_id,
    })
    return render(request, 'clinical/nurse_notes.html', {
        'visit': visit,
        'form': form,
        'notes': notes,
    })


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_users(request):
    from users_auth.models import User, Role, UserRole, Department
    from users_auth.forms import UserForm, UserRoleAssignForm
    from audit.utils import log_audit

    users = User.objects.filter(is_active=True).select_related('department').order_by('-created_at')
    roles = Role.objects.filter(is_active=True)
    departments = Department.objects.filter(is_active=True)

    search = request.GET.get('search', '')
    dept_filter = request.GET.get('department', '')
    role_filter = request.GET.get('role', '')

    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    if dept_filter:
        users = users.filter(department_id=dept_filter)
    if role_filter:
        user_ids = UserRole.objects.filter(role_id=role_filter, is_active=True).values_list('user_id', flat=True)
        users = users.filter(id__in=user_ids)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'create' or action == 'edit':
            form = UserForm(request.POST)
            if form.is_valid():
                target = form.save(user=request.user)
                log_audit('users_auth', 'users', target.id,
                          'CREATE' if action == 'create' else 'UPDATE',
                          new_values={
                              'username': target.username,
                              'email': target.email,
                              'first_name': target.first_name,
                              'last_name': target.last_name,
                              'status': target.status,
                          },
                          request=request)
                messages.success(request, f'User {target.username} {"updated" if action == "edit" else "created"} successfully.')
                return redirect('admin-users')
            else:
                messages.error(request, 'Please correct the errors below.')
        elif action == 'activate':
            uid = request.POST.get('user_id')
            User.objects.filter(id=uid).update(status='active', is_active=True)
            log_audit('users_auth', 'users', uid, 'UPDATE',
                      old_values={'status': 'inactive', 'is_active': False},
                      new_values={'status': 'active', 'is_active': True},
                      request=request)
            messages.success(request, 'User activated.')
            return redirect('admin-users')
        elif action == 'deactivate':
            uid = request.POST.get('user_id')
            User.objects.filter(id=uid).update(status='inactive', is_active=False)
            log_audit('users_auth', 'users', uid, 'UPDATE',
                      old_values={'status': 'active', 'is_active': True},
                      new_values={'status': 'inactive', 'is_active': False},
                      request=request)
            messages.success(request, 'User deactivated.')
            return redirect('admin-users')
        elif action == 'unlock':
            uid = request.POST.get('user_id')
            User.objects.filter(id=uid).update(failed_login_attempts=0, locked_until=None, status='active')
            log_audit('users_auth', 'users', uid, 'UPDATE',
                      old_values={'status': 'locked'},
                      new_values={'status': 'active', 'failed_login_attempts': 0, 'locked_until': None},
                      request=request)
            messages.success(request, 'User unlocked.')
            return redirect('admin-users')
        elif action == 'assign_role':
            form = UserRoleAssignForm(request.POST)
            if form.is_valid():
                form.assign(assigned_by=request.user)
                log_audit('users_auth', 'user_roles', form.cleaned_data['user_id'], 'CREATE',
                          new_values={'user_id': str(form.cleaned_data['user_id']), 'role_id': str(form.cleaned_data['role_id'])},
                          request=request)
                messages.success(request, 'Role assigned.')
                return redirect('admin-users')
        elif action == 'remove_role':
            form = UserRoleAssignForm(request.POST)
            if form.is_valid():
                form.remove()
                log_audit('users_auth', 'user_roles', form.cleaned_data['user_id'], 'DELETE',
                          old_values={'user_id': str(form.cleaned_data['user_id']), 'role_id': str(form.cleaned_data['role_id'])},
                          request=request)
                messages.success(request, 'Role removed.')
                return redirect('admin-users')

    user_roles_map = {}
    for ur in UserRole.objects.filter(user__in=users, is_active=True).select_related('role'):
        user_roles_map.setdefault(str(ur.user_id), []).append(ur.role)

    context = {
        'users': users,
        'roles': roles,
        'departments': departments,
        'user_roles_map': user_roles_map,
        'search': search,
        'dept_filter': dept_filter,
        'role_filter': role_filter,
        'total_users': users.count(),
    }
    return render(request, 'admin/users.html', context)


@login_required(login_url='/login/')
def admin_user_profile(request):
    from users_auth.models import UserRole
    from users_auth.forms import ProfileForm, PasswordChangeForm
    from audit.utils import log_audit

    user = request.user
    user_roles = UserRole.objects.filter(user=user, is_active=True).select_related('role')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'edit_profile':
            form = ProfileForm(request.POST)
            if form.is_valid():
                old_values = {
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'email': user.email,
                    'phone': user.phone or '',
                }
                form.save(user)
                log_audit('users_auth', 'users', user.id, 'UPDATE',
                          old_values=old_values,
                          new_values={
                              'first_name': user.first_name,
                              'last_name': user.last_name,
                              'email': user.email,
                              'phone': user.phone or '',
                          },
                          request=request)
                messages.success(request, 'Profile updated successfully.')
                return redirect('admin-profile')
            else:
                messages.error(request, 'Please correct the errors below.')
        elif action == 'change_password':
            form = PasswordChangeForm(target_user=user, data=request.POST)
            if form.is_valid():
                form.save()
                log_audit('users_auth', 'users', user.id, 'UPDATE',
                          new_values={'password': '***changed***'},
                          request=request)
                messages.success(request, 'Password changed successfully.')
                return redirect('admin-profile')
            else:
                messages.error(request, 'Please correct the errors below.')

    profile_form = ProfileForm(initial={
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'phone': user.phone or '',
    })
    password_form = PasswordChangeForm(target_user=user)

    context = {
        'profile_user': user,
        'user_roles': user_roles,
        'profile_form': profile_form,
        'password_form': password_form,
    }
    return render(request, 'admin/user_profile.html', context)


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_roles(request):
    from users_auth.models import Role, Permission, RolePermission
    from users_auth.forms import RoleForm, RolePermissionAssignForm
    from audit.utils import log_audit

    roles = Role.objects.filter(is_active=True).order_by('name')
    permissions = Permission.objects.filter(is_active=True).order_by('category', 'name')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'create' or action == 'edit':
            form = RoleForm(request.POST)
            if form.is_valid():
                role = form.save(user=request.user)
                log_audit('users_auth', 'roles', role.id,
                          'CREATE' if action == 'create' else 'UPDATE',
                          new_values={
                              'name': role.name,
                              'code': role.code,
                              'description': role.description or '',
                          },
                          request=request)
                messages.success(request, f'Role {role.name} {"updated" if action == "edit" else "created"} successfully.')
                return redirect('admin-roles')
            else:
                messages.error(request, 'Please correct the errors below.')
        elif action == 'assign_permission':
            form = RolePermissionAssignForm(request.POST)
            if form.is_valid():
                form.assign(granted_by=request.user)
                log_audit('users_auth', 'role_permissions', form.cleaned_data['role_id'], 'CREATE',
                          new_values={'role_id': str(form.cleaned_data['role_id']), 'permission_id': str(form.cleaned_data['permission_id'])},
                          request=request)
                messages.success(request, 'Permission assigned to role.')
                return redirect('admin-roles')
        elif action == 'remove_permission':
            form = RolePermissionAssignForm(request.POST)
            if form.is_valid():
                form.remove()
                log_audit('users_auth', 'role_permissions', form.cleaned_data['role_id'], 'DELETE',
                          old_values={'role_id': str(form.cleaned_data['role_id']), 'permission_id': str(form.cleaned_data['permission_id'])},
                          request=request)
                messages.success(request, 'Permission removed from role.')
                return redirect('admin-roles')

    role_permissions_map = {}
    for rp in RolePermission.objects.filter(role__in=roles).select_related('permission'):
        role_permissions_map.setdefault(str(rp.role_id), []).append(rp.permission)

    import json
    permissions_json = json.dumps([
        {'id': str(p.id), 'name': p.name, 'code': p.code, 'category': getattr(p, 'category', '')}
        for p in permissions
    ])
    role_permissions_map_json = json.dumps({
        k: [{'id': str(p.id), 'name': p.name, 'code': p.code} for p in v]
        for k, v in role_permissions_map.items()
    })

    context = {
        'roles': roles,
        'permissions': permissions,
        'role_permissions_map': role_permissions_map,
        'permissions_json': permissions_json,
        'role_permissions_map_json': role_permissions_map_json,
        'total_roles': roles.count(),
        'total_permissions': permissions.count(),
    }
    return render(request, 'admin/roles.html', context)


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_departments(request):
    from users_auth.models import Department
    from users_auth.forms import DepartmentForm
    from audit.utils import log_audit

    departments = Department.objects.filter(is_active=True).select_related('parent_department').order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'create' or action == 'edit':
            form = DepartmentForm(request.POST)
            if form.is_valid():
                dept = form.save()
                log_audit('users_auth', 'departments', dept.id,
                          'CREATE' if action == 'create' else 'UPDATE',
                          new_values={
                              'name': dept.name,
                              'code': dept.code,
                              'description': dept.description or '',
                              'is_clinical': dept.is_clinical,
                              'parent_department_id': str(dept.parent_department_id) if dept.parent_department_id else None,
                          },
                          request=request)
                messages.success(request, f'Department {dept.name} {"updated" if action == "edit" else "created"} successfully.')
                return redirect('admin-departments')
            else:
                messages.error(request, 'Please correct the errors below.')

    context = {
        'departments': departments,
        'total_departments': departments.count(),
        'clinical_count': departments.filter(is_clinical=True).count(),
    }
    return render(request, 'admin/departments.html', context)


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_settings(request):
    from users_auth.models import HospitalSetting
    from users_auth.forms import HospitalSettingForm
    from audit.utils import log_audit

    setting = HospitalSetting.get_settings()

    if request.method == 'POST':
        form = HospitalSettingForm(request.POST, request.FILES)
        if form.is_valid():
            old_logo = setting.logo
            new_setting = form.save(updated_by=request.user.username)
            log_audit('users_auth', 'hospital_settings', new_setting.id, 'UPDATE',
                      new_values={
                          'hospital_name': new_setting.hospital_name,
                          'short_name': new_setting.short_name,
                          'logo_changed': bool(request.FILES.get('logo')),
                      },
                      request=request)
            messages.success(request, 'Hospital settings updated successfully.')
            return redirect('admin-settings')
        else:
            messages.error(request, 'Please correct the errors below.')

    initial = {
        'hospital_name': setting.hospital_name,
        'short_name': setting.short_name,
        'tagline': setting.tagline,
        'phone': setting.phone,
        'email': setting.email,
        'address': setting.address,
        'website': setting.website,
        'registration_fee': setting.registration_fee,
        'followup_window_days': setting.followup_window_days,
    }
    form = HospitalSettingForm(initial=initial)

    context = {
        'form': form,
        'setting': setting,
        'has_logo': bool(setting.logo),
        'page_title': 'Hospital Settings',
    }
    return render(request, 'admin/settings.html', context)


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_audit_trail(request):
    from audit.models import AuditLog

    logs = AuditLog.objects.all().order_by('-created_at')

    table = request.GET.get('table', '')
    action = request.GET.get('action', '')
    user = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')

    if table:
        logs = logs.filter(table_name=table)
    if action:
        logs = logs.filter(action=action)
    if user:
        logs = logs.filter(user_name__icontains=user)
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    if search:
        logs = logs.filter(
            Q(table_name__icontains=search) |
            Q(user_name__icontains=search) |
            Q(new_values__icontains=search)
        )

    total = logs.count()
    page_size = 50
    page = int(request.GET.get('page', 1))
    offset = (page - 1) * page_size
    logs = logs[offset:offset + page_size]
    total_pages = (total + page_size - 1) // page_size

    tables = AuditLog.objects.values_list('table_name', flat=True).distinct().order_by('table_name')
    actions_list = AuditLog.objects.values_list('action', flat=True).distinct()

    today_count = AuditLog.objects.filter(created_at__date=date.today()).count()
    create_count = AuditLog.objects.filter(action='CREATE').count()
    update_count = AuditLog.objects.filter(action='UPDATE').count()

    context = {
        'logs': logs,
        'tables': tables,
        'actions_list': actions_list,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'table_filter': table,
        'action_filter': action,
        'user_filter': user,
        'date_from': date_from,
        'date_to': date_to,
        'search': search,
        'today_count': today_count,
        'create_count': create_count,
        'update_count': update_count,
    }
    return render(request, 'admin/audit_trail.html', context)


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_login_history(request):
    from audit.models import LoginLog

    logs = LoginLog.objects.all().order_by('-login_at')

    username = request.GET.get('username', '')
    success = request.GET.get('success', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if username:
        logs = logs.filter(username__icontains=username)
    if success:
        logs = logs.filter(success=success == 'true')
    if date_from:
        logs = logs.filter(login_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(login_at__date__lte=date_to)

    total = logs.count()
    page_size = 50
    page = int(request.GET.get('page', 1))
    offset = (page - 1) * page_size
    logs = logs[offset:offset + page_size]
    total_pages = (total + page_size - 1) // page_size

    today_logins = LoginLog.objects.filter(login_at__date=date.today(), success=True).count()
    today_failed = LoginLog.objects.filter(login_at__date=date.today(), success=False).count()
    unique_users_today = LoginLog.objects.filter(login_at__date=date.today(), success=True).values('username').distinct().count()

    context = {
        'logs': logs,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'username_filter': username,
        'success_filter': success,
        'date_from': date_from,
        'date_to': date_to,
        'today_logins': today_logins,
        'today_failed': today_failed,
        'unique_users_today': unique_users_today,
    }
    return render(request, 'admin/login_history.html', context)


@login_required(login_url='/login/')
@user_passes_test(lambda u: u.is_superuser, login_url='/')
def admin_triage_criteria(request):
    from clinical.models import TriageCriteria
    from audit.utils import log_audit

    criteria = TriageCriteria.objects.all().order_by('priority', 'vital_sign')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            name = request.POST.get('name', '').strip()
            vital_sign = request.POST.get('vital_sign', '')
            operator = request.POST.get('operator', '')
            threshold_low = request.POST.get('threshold_low', '')
            threshold_high = request.POST.get('threshold_high', '')
            suggested_acuity = request.POST.get('suggested_acuity', '')
            suggested_department = request.POST.get('suggested_department', 'OPD')
            priority = request.POST.get('priority', '100')

            if not all([name, vital_sign, operator, threshold_low, suggested_acuity]):
                messages.error(request, 'All required fields must be filled.')
                return redirect('admin-triage-criteria')

            try:
                criterion = TriageCriteria.objects.create(
                    name=name,
                    vital_sign=vital_sign,
                    operator=operator,
                    threshold_low=Decimal(threshold_low),
                    threshold_high=Decimal(threshold_high) if threshold_high else None,
                    suggested_acuity=int(suggested_acuity),
                    suggested_department=suggested_department,
                    priority=int(priority),
                    is_active=True,
                )
                log_audit('clinical', 'triage_criteria', criterion.id, 'CREATE',
                          new_values={'name': name, 'vital_sign': vital_sign, 'operator': operator},
                          request=request)
                messages.success(request, f'Triage criteria "{name}" created.')
            except Exception as e:
                messages.error(request, f'Error creating criteria: {str(e)}')

        elif action == 'toggle':
            criterion_id = request.POST.get('criterion_id')
            try:
                criterion = TriageCriteria.objects.get(id=criterion_id)
                criterion.is_active = not criterion.is_active
                criterion.save()
                status_text = 'activated' if criterion.is_active else 'deactivated'
                log_audit('clinical', 'triage_criteria', criterion.id, 'UPDATE',
                          new_values={'is_active': criterion.is_active},
                          request=request)
                messages.success(request, f'Criteria "{criterion.name}" {status_text}.')
            except TriageCriteria.DoesNotExist:
                messages.error(request, 'Criteria not found.')

        elif action == 'delete':
            criterion_id = request.POST.get('criterion_id')
            try:
                criterion = TriageCriteria.objects.get(id=criterion_id)
                name = criterion.name
                log_audit('clinical', 'triage_criteria', criterion.id, 'DELETE',
                          new_values={'name': name},
                          request=request)
                criterion.delete()
                messages.success(request, f'Criteria "{name}" deleted.')
            except TriageCriteria.DoesNotExist:
                messages.error(request, 'Criteria not found.')

        elif action == 'update':
            criterion_id = request.POST.get('criterion_id')
            try:
                criterion = TriageCriteria.objects.get(id=criterion_id)
                criterion.name = request.POST.get('name', criterion.name)
                criterion.vital_sign = request.POST.get('vital_sign', criterion.vital_sign)
                criterion.operator = request.POST.get('operator', criterion.operator)
                criterion.threshold_low = Decimal(request.POST.get('threshold_low', str(criterion.threshold_low)))
                threshold_high = request.POST.get('threshold_high', '')
                criterion.threshold_high = Decimal(threshold_high) if threshold_high else None
                criterion.suggested_acuity = int(request.POST.get('suggested_acuity', criterion.suggested_acuity))
                criterion.suggested_department = request.POST.get('department', criterion.suggested_department)
                criterion.priority = int(request.POST.get('priority', criterion.priority))
                criterion.save()
                log_audit('clinical', 'triage_criteria', criterion.id, 'UPDATE',
                          new_values={'name': criterion.name},
                          request=request)
                messages.success(request, f'Criteria "{criterion.name}" updated.')
            except (TriageCriteria.DoesNotExist, Exception) as e:
                messages.error(request, f'Error updating criteria: {str(e)}')

        return redirect('admin-triage-criteria')

    context = {
        'criteria': criteria,
        'active_count': criteria.filter(is_active=True).count(),
        'inactive_count': criteria.filter(is_active=False).count(),
    }
    return render(request, 'admin/triage_criteria.html', context)


@login_required(login_url='/login/')
@require_permission('PATIENT_VIEW')
def patient_profile(request, patient_id):
    from patients.models import Patient, PatientDocument
    from clinical.models import Visit, TriageRecord, Encounter
    from billing.models import Invoice
    try:
        patient = Patient.objects.get(id=patient_id, is_deleted=False)
    except Patient.DoesNotExist:
        from django.contrib import messages
        messages.error(request, 'Patient not found.')
        return redirect('patient-search-page')

    visits = Visit.objects.filter(patient=patient, is_deleted=False).order_by('-created_at')[:10]
    documents = PatientDocument.objects.filter(patient=patient, is_active=True).order_by('-uploaded_at')
    triage_records = TriageRecord.objects.filter(patient=patient).order_by('-triage_time')[:5]
    invoices = Invoice.objects.filter(patient=patient, is_deleted=False).order_by('-created_at')[:5]

    return render(request, 'patients/profile.html', {
        'patient': patient,
        'visits': visits,
        'documents': documents,
        'triage_records': triage_records,
        'invoices': invoices,
    })

