"""
Data providers: one function per data type.
Each returns (headers, rows, title) for the export engine.
"""
from django.utils import timezone


def _dt(val):
    if val is None:
        return ''
    return val.strftime('%d %b %Y %H:%M') if hasattr(val, 'strftime') else str(val)


def _date(val):
    if val is None:
        return ''
    return val.strftime('%d %b %Y') if hasattr(val, 'strftime') else str(val)


def get_patients():
    from patients.models import Patient
    headers = ['MRN', 'First Name', 'Last Name', 'DOB', 'Gender', 'Phone', 'Payer Category', 'Registered']
    rows = []
    for p in Patient.objects.filter(is_deleted=False).order_by('-created_at'):
        rows.append([p.mrn, p.first_name, p.last_name, _date(p.date_of_birth),
                      'Male' if p.gender == 'M' else 'Female', p.phone or '',
                      p.payer_category or '', _dt(p.created_at)])
    return headers, rows, 'Patient Register'


def get_visits():
    from clinical.models import Visit
    headers = ['Visit #', 'Patient', 'MRN', 'Type', 'Status', 'Triage Priority', 'Check-in', 'Provider']
    rows = []
    for v in Visit.objects.filter(is_deleted=False).select_related('patient', 'provider').order_by('-created_at'):
        pname = f'{v.patient.first_name} {v.patient.last_name}' if v.patient else ''
        prov = f'{v.provider.first_name} {v.provider.last_name}' if v.provider else ''
        rows.append([v.visit_number, pname, v.patient.mrn if v.patient else '',
                      v.visit_type.upper(), v.status, v.triage_priority or '',
                      _dt(v.check_in_time), prov])
    return headers, rows, 'Clinical Visits'


def get_triage_queue():
    from clinical.models import Visit
    headers = ['Visit #', 'Patient', 'MRN', 'Chief Complaint', 'Acuity', 'Department', 'Triage Time']
    rows = []
    for v in Visit.objects.filter(is_deleted=False, status__in=['in_triage', 'checked_in']).select_related('patient').order_by('triage_priority'):
        pname = f'{v.patient.first_name} {v.patient.last_name}' if v.patient else ''
        rows.append([v.visit_number, pname, v.patient.mrn if v.patient else '',
                      v.chief_complaint or '', v.triage_priority or '', v.suggested_department or '',
                      _dt(v.triage_time)])
    return headers, rows, 'Triage Queue'


def get_opd_consultations():
    from clinical.models import Visit
    headers = ['Visit #', 'Patient', 'MRN', 'Provider', 'Chief Complaint', 'Status', 'Date']
    rows = []
    for v in Visit.objects.filter(is_deleted=False, visit_type='opd').select_related('patient', 'provider').order_by('-created_at'):
        pname = f'{v.patient.first_name} {v.patient.last_name}' if v.patient else ''
        prov = f'{v.provider.first_name} {v.provider.last_name}' if v.provider else ''
        rows.append([v.visit_number, pname, v.patient.mrn if v.patient else '',
                      prov, v.chief_complaint or '', v.status, _dt(v.created_at)])
    return headers, rows, 'OPD Consultations'


def get_emergency_cases():
    from clinical.models import Visit
    headers = ['Visit #', 'Patient', 'MRN', 'Acuity', 'Chief Complaint', 'Status', 'Check-in', 'Disposition']
    rows = []
    for v in Visit.objects.filter(is_deleted=False, visit_type='er').select_related('patient').order_by('-created_at'):
        pname = f'{v.patient.first_name} {v.patient.last_name}' if v.patient else ''
        rows.append([v.visit_number, pname, v.patient.mrn if v.patient else '',
                      v.triage_priority or '', v.chief_complaint or '', v.status,
                      _dt(v.check_in_time), v.route_override or ''])
    return headers, rows, 'Emergency Cases'


def get_ipd_patients():
    from clinical.models import Admission
    headers = ['Admission #', 'Patient', 'MRN', 'Ward', 'Bed', 'Admitted', 'Status', 'Diagnosis']
    rows = []
    for a in Admission.objects.filter(status='active').select_related('patient', 'ward', 'bed').order_by('-admission_date'):
        pname = f'{a.patient.first_name} {a.patient.last_name}' if a.patient else ''
        ward = a.ward.name if a.ward else ''
        bed = a.bed.bed_number if a.bed else ''
        rows.append([a.admission_number, pname, a.patient.mrn if a.patient else '',
                      ward, bed, _dt(a.admission_date), a.status, a.admitting_diagnosis or ''])
    return headers, rows, 'IPD Active Patients'


def get_appointments():
    from clinical.models import Appointment
    headers = ['Patient', 'MRN', 'Provider', 'Date', 'Type', 'Reason', 'Status']
    rows = []
    for a in Appointment.objects.filter(is_deleted=False).select_related('patient', 'provider').order_by('-appointment_date'):
        pname = f'{a.patient.first_name} {a.patient.last_name}' if a.patient else ''
        prov = f'{a.provider.first_name} {a.provider.last_name}' if a.provider else ''
        rows.append([pname, a.patient.mrn if a.patient else '', prov,
                      _dt(a.appointment_date), a.appointment_type or '', a.reason or '', a.status])
    return headers, rows, 'Appointments'


def get_surgical_cases():
    from clinical.models import SurgicalCase
    headers = ['Case #', 'Patient', 'MRN', 'Procedure', 'Surgeon', 'Priority', 'Status', 'Scheduled']
    rows = []
    for c in SurgicalCase.objects.all().select_related('patient', 'surgeon').order_by('-created_at'):
        pname = f'{c.patient.first_name} {c.patient.last_name}' if c.patient else ''
        surg = f'{c.surgeon.first_name} {c.surgeon.last_name}' if c.surgeon else ''
        rows.append([c.case_number, pname, c.patient.mrn if c.patient else '',
                      c.procedure_name, surg, c.priority, c.status, _dt(c.scheduled_date)])
    return headers, rows, 'Surgical Cases'


def get_antenatal_visits():
    from clinical.models import AntenatalVisit
    headers = ['ANC #', 'Patient', 'MRN', 'GA (weeks)', 'LMP', 'EDD', 'Gravida', 'Parity', 'BP', 'Status']
    rows = []
    for a in AntenatalVisit.objects.all().select_related('patient').order_by('-created_at'):
        pname = f'{a.patient.first_name} {a.patient.last_name}' if a.patient else ''
        bp = f'{a.blood_pressure_systolic}/{a.blood_pressure_diastolic}' if a.blood_pressure_systolic else ''
        rows.append([a.visit_number, pname, a.patient.mrn if a.patient else '',
                      a.ga_weeks, _date(a.lmp_date), _date(a.edd_date),
                      a.gravida, a.parity, bp, a.status])
    return headers, rows, 'Antenatal Visits'


def get_labor_records():
    from clinical.models import LaborRecord
    headers = ['Patient', 'MRN', 'Status', 'Cervical Dilation', 'FHR', 'Presentation', 'Admitted']
    rows = []
    for l in LaborRecord.objects.all().select_related('patient').order_by('-created_at'):
        pname = f'{l.patient.first_name} {l.patient.last_name}' if l.patient else ''
        rows.append([pname, l.patient.mrn if l.patient else '', l.status,
                      l.cervical_dilation or '', l.fetal_heart_rate or '',
                      l.presentation or '', _dt(l.admission_time)])
    return headers, rows, 'Labor Records'


def get_delivery_records():
    from clinical.models import DeliveryRecord
    headers = ['Patient', 'MRN', 'Mode', 'Complications', 'Blood Loss', 'Duration', 'Date']
    rows = []
    for d in DeliveryRecord.objects.all().select_related('patient').order_by('-created_at'):
        pname = f'{d.patient.first_name} {d.patient.last_name}' if d.patient else ''
        rows.append([pname, d.patient.mrn if d.patient else '', d.mode_of_delivery or '',
                      d.complications or '', d.blood_loss_ml or '', d.duration_minutes or '',
                      _dt(d.created_at)])
    return headers, rows, 'Delivery Records'


def get_birth_records():
    from clinical.models import BirthRecord
    headers = ['Baby Name', 'Sex', 'Weight (kg)', 'APGAR 1min', 'APGAR 5min', 'Mother', 'MRN', 'Feeding']
    rows = []
    for b in BirthRecord.objects.all().select_related('patient').order_by('-created_at'):
        mname = f'{b.patient.first_name} {b.patient.last_name}' if b.patient else ''
        rows.append([b.baby_name or '', b.sex or '', b.birth_weight_kg or '',
                      b.apgar_score_1min or '', b.apgar_score_5min or '',
                      mname, b.patient.mrn if b.patient else '', b.feeding_method or ''])
    return headers, rows, 'Birth Records'


def get_postnatal_visits():
    from clinical.models import PostnatalVisit
    headers = ['Patient', 'MRN', 'Day Postpartum', 'Temp', 'BP', 'Fundal Height', 'Feeding', 'Date']
    rows = []
    for p in PostnatalVisit.objects.all().select_related('patient').order_by('-created_at'):
        pname = f'{p.patient.first_name} {p.patient.last_name}' if p.patient else ''
        bp = f'{p.blood_pressure_systolic}/{p.blood_pressure_diastolic}' if p.blood_pressure_systolic else ''
        rows.append([pname, p.patient.mrn if p.patient else '', p.day_postpartum or '',
                      p.temperature or '', bp, p.fundal_height or '',
                      p.feeding_method or '', _dt(p.created_at)])
    return headers, rows, 'Postnatal Visits'


def get_prescriptions():
    from pharmacy.models import Prescription, PrescriptionItem
    headers = ['Patient', 'MRN', 'Medication', 'Quantity', 'Duration', 'Prescribed By', 'Date']
    rows = []
    for pr in Prescription.objects.all().select_related('patient', 'prescribed_by').order_by('-created_at'):
        pname = f'{pr.patient.first_name} {pr.patient.last_name}' if pr.patient else ''
        doc = f'{pr.prescribed_by.first_name} {pr.prescribed_by.last_name}' if pr.prescribed_by else ''
        items = PrescriptionItem.objects.filter(prescription=pr)
        for item in items:
            rows.append([pname, pr.patient.mrn if pr.patient else '',
                          item.medication.name if item.medication else '',
                          item.quantity_prescribed, item.duration or '',
                          doc, _dt(pr.created_at)])
    if not rows:
        rows = [['', '', '', '', '', '', '']]
    return headers, rows, 'Prescriptions'


def get_dispensing():
    from pharmacy.models import Dispensing
    headers = ['Patient', 'MRN', 'Medication', 'Quantity', 'Dispensed By', 'Date']
    rows = []
    for d in Dispensing.objects.all().select_related('prescription__patient', 'dispensed_by').order_by('-created_at'):
        pname = ''
        mrn = ''
        med = ''
        qty = ''
        if d.prescription and d.prescription.patient:
            pname = f'{d.prescription.patient.first_name} {d.prescription.patient.last_name}'
            mrn = d.prescription.patient.mrn or ''
        if d.prescription_item:
            med = d.prescription_item.medication.name if d.prescription_item.medication else ''
            qty = d.quantity_dispensed or ''
        doc = f'{d.dispensed_by.first_name} {d.dispensed_by.last_name}' if d.dispensed_by else ''
        rows.append([pname, mrn, med, qty, doc, _dt(d.created_at)])
    return headers, rows, 'Dispensing Records'


def get_invoices():
    from billing.models import Invoice
    headers = ['Invoice #', 'Patient', 'MRN', 'Total', 'Status', 'Created']
    rows = []
    for inv in Invoice.objects.filter(is_deleted=False).select_related('patient').order_by('-created_at'):
        pname = f'{inv.patient.first_name} {inv.patient.last_name}' if inv.patient else ''
        rows.append([inv.invoice_number, pname, inv.patient.mrn if inv.patient else '',
                      f'${inv.total_amount}', inv.status, _dt(inv.created_at)])
    return headers, rows, 'Invoices'


def get_payments():
    from billing.models import Payment
    headers = ['Payment #', 'Invoice #', 'Patient', 'Amount', 'Method', 'Reference', 'Date']
    rows = []
    for p in Payment.objects.filter(is_deleted=False).select_related('invoice__patient').order_by('-created_at'):
        inv = p.invoice
        pname = ''
        mrn = ''
        inv_num = ''
        if inv and inv.patient:
            pname = f'{inv.patient.first_name} {inv.patient.last_name}'
            mrn = inv.patient.mrn or ''
            inv_num = inv.invoice_number or ''
        rows.append([p.payment_number or '', inv_num, pname, f'${p.amount}',
                      p.payment_method or '', p.reference_number or '', _dt(p.created_at)])
    return headers, rows, 'Payments'


def get_stock():
    from inventory.models import Stock
    headers = ['Item', 'Store', 'Quantity', 'Batch #', 'Expiry', 'Status']
    rows = []
    for s in Stock.objects.filter(is_active=True).select_related('item', 'store').order_by('item__name'):
        item = s.item.name if s.item else ''
        store = s.store.name if s.store else ''
        status = 'Expired' if s.expiry_date and s.expiry_date < timezone.now().date() else ('Low' if s.quantity <= 0 else 'OK')
        rows.append([item, store, s.quantity, s.batch_lot_number or '',
                      _date(s.expiry_date), status])
    return headers, rows, 'Stock Items'


def get_inventory_items():
    from inventory.models import InventoryItem
    headers = ['Item', 'Category', 'Unit', 'Min Stock', 'Reorder Level', 'Description']
    rows = []
    for i in InventoryItem.objects.filter(is_active=True).select_related('category').order_by('name'):
        rows.append([i.name, i.category.name if i.category else '', i.unit_of_measure or '',
                      i.minimum_stock or '', i.reorder_level or '', i.description or ''])
    return headers, rows, 'Inventory Items'


def get_audit_trail():
    from audit.models import AuditLog
    headers = ['Timestamp', 'User', 'Action', 'Table', 'Record ID', 'IP Address']
    rows = []
    for a in AuditLog.objects.all().order_by('-timestamp')[:500]:
        rows.append([_dt(a.timestamp), str(a.user_id or ''), a.action or '',
                      f'{a.app_label}.{a.model_name}' if a.app_label else '',
                      str(a.record_id or ''), a.ip_address or ''])
    return headers, rows, 'Audit Trail'


def get_users():
    from users_auth.models import User, UserRole
    headers = ['Name', 'Username', 'Email', 'Phone', 'Roles', 'Status', 'Last Login']
    rows = []
    for u in User.objects.filter(is_active=True).order_by('first_name'):
        roles = ', '.join([ur.role.name for ur in UserRole.objects.filter(user=u, is_active=True).select_related('role')])
        rows.append([f'{u.first_name} {u.last_name}', u.username, u.email or '',
                      u.phone or '', roles, 'Active' if u.is_active else 'Inactive',
                      _dt(u.last_login)])
    return headers, rows, 'Users'


PROVIDERS = {
    'patients': get_patients,
    'visits': get_visits,
    'triage': get_triage_queue,
    'opd': get_opd_consultations,
    'emergency': get_emergency_cases,
    'ipd': get_ipd_patients,
    'appointments': get_appointments,
    'surgery': get_surgical_cases,
    'obgyn': get_antenatal_visits,
    'labor': get_labor_records,
    'delivery': get_delivery_records,
    'births': get_birth_records,
    'postnatal': get_postnatal_visits,
    'prescriptions': get_prescriptions,
    'dispensing': get_dispensing,
    'invoices': get_invoices,
    'payments': get_payments,
    'stock': get_stock,
    'inventory': get_inventory_items,
    'audit': get_audit_trail,
    'users': get_users,
}
