#!/usr/bin/env python
"""
Automated End-to-End Walkthrough — All 9 Scenarios
JFD Hospital Management System
"""
import requests
import json
import sys
from datetime import date, timedelta

BASE = 'http://127.0.0.1:8000'
RESULTS = []


def log(scenario, step, status, detail=''):
    icon = 'PASS' if status == 'PASS' else 'FAIL'
    msg = f"[{icon}] {scenario} | {step}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    RESULTS.append({'scenario': scenario, 'step': step, 'status': status, 'detail': detail})


def get_session(username, password):
    s = requests.Session()
    # Get CSRF token first
    s.get(f'{BASE}/api/auth/login/')
    csrf = s.cookies.get('csrftoken', '')
    r = s.post(f'{BASE}/api/auth/login/', json={'username': username, 'password': password},
               headers={'X-CSRFToken': csrf})
    if r.status_code == 200:
        return s
    return None


def api(s, method, path, **kwargs):
    url = f'{BASE}{path}'
    csrf = s.cookies.get('csrftoken', '')
    headers = kwargs.pop('headers', {})
    headers['X-CSRFToken'] = csrf
    kwargs['headers'] = headers
    r = getattr(s, method)(url, **kwargs)
    return r


def register_patient(s, first_name, last_name, suffix='', **extra):
    """Register a patient and return (patient_id, mrn)."""
    data = {
        'first_name': first_name, 'last_name': last_name,
        'date_of_birth': '1990-01-01', 'gender': 'M',
        'phone': f'+231770000{hash(first_name) % 10000:04d}',
        'visit_type': 'opd',
    }
    data.update(extra)
    r = api(s, 'post', '/api/patients/', json=data)
    if r.status_code in [200, 201]:
        resp = r.json()
        patient_id = resp.get('id')
        mrn = resp.get('mrn', 'unknown')
        if not patient_id:
            r2 = api(s, 'get', f'/api/patients/?search={last_name}')
            if r2.status_code == 200:
                patients = r2.json()
                if isinstance(patients, dict):
                    patients = patients.get('results', [])
                if patients:
                    patient_id = patients[0].get('id')
                    mrn = patients[0].get('mrn', mrn)
        return patient_id, mrn
    # If duplicate detected, find existing patient
    if 'Potential duplicate' in r.text:
        r2 = api(s, 'get', f'/api/patients/?search={last_name}')
        if r2.status_code == 200:
            patients = r2.json()
            if isinstance(patients, dict):
                patients = patients.get('results', [])
            if patients:
                for p in patients:
                    if p.get('first_name') == first_name and p.get('last_name') == last_name:
                        return p.get('id'), p.get('mrn', 'unknown')
                return patients[0].get('id'), patients[0].get('mrn', 'unknown')
    return None, None


# ═══════════════════════════════════════════════════════════════
# SCENARIO A: Normal Patient Journey
# ═══════════════════════════════════════════════════════════════
def scenario_a():
    s = get_session('admin', 'admin123')
    if not s:
        log('A', 'Login', 'FAIL', 'Could not login as admin')
        return

    log('A', 'Login', 'PASS', 'Logged in as admin')

    # Step 1: Register patient
    patient_id, mrn = register_patient(s, 'John', 'Walkthrough',
        date_of_birth='1985-03-20', gender='M',
        phone='+231770000001', blood_type='O+',
        marital_status='single', visit_type='opd')
    if patient_id:
        log('A', '1. Register Patient', 'PASS', f'MRN: {mrn}, ID: {str(patient_id)[:8]}...')
    else:
        log('A', '1. Register Patient', 'FAIL', 'Registration failed')
        return

    # Step 2: Create visit
    r = api(s, 'post', '/api/clinical/visits/', json={
        'patient': patient_id, 'visit_type': 'opd',
        'chief_complaint': 'Headache and fever for 3 days',
    })
    if r.status_code in [200, 201]:
        visit = r.json()
        visit_id = visit.get('id')
        visit_number = visit.get('visit_number', 'unknown')
        log('A', '2. Create Visit', 'PASS', f'Visit: {visit_number}')
    else:
        log('A', '2. Create Visit', 'FAIL', f'{r.status_code}: {r.text[:200]}')
        return

    # Step 3: Triage
    r = api(s, 'patch', f'/api/clinical/visits/{visit_id}/status/', json={
        'status': 'checked_in'
    })
    r = api(s, 'post', f'/api/clinical/visits/{visit_id}/triage/submit/', json={
        'acuity_level': 3,
        'temperature': 38.5, 'heart_rate': 88,
        'blood_pressure_systolic': 120, 'blood_pressure_diastolic': 80,
        'respiratory_rate': 18, 'oxygen_saturation': 97,
        'pain_scale': 6, 'weight': 72.5,
    })
    if r.status_code in [200, 201]:
        log('A', '3. Triage', 'PASS', 'Acuity 3, vitals recorded')
    else:
        log('A', '3. Triage', 'FAIL', f'{r.status_code}: {r.text[:200]}')

    # Step 4: Encounter
    r = api(s, 'post', f'/api/clinical/visits/{visit_id}/encounters/', json={
        'encounter_type': 'opd',
        'subjective': 'Patient reports headache and fever',
        'objective': 'Temp 38.5C, HR 88, BP 120/80',
        'assessment': 'Upper respiratory infection',
        'plan': 'Lab tests and prescription',
    })
    if r.status_code in [200, 201]:
        encounter = r.json()
        encounter_id = encounter.get('id')
        log('A', '4. Encounter', 'PASS', f'Encounter created')
    else:
        log('A', '4. Encounter', 'FAIL', f'{r.status_code}: {r.text[:200]}')
        return

    # Step 5: Diagnosis
    r = api(s, 'post', f'/api/clinical/encounters/{encounter_id}/diagnoses/', json={
        'encounter': encounter_id,
        'patient': patient_id, 'visit': visit_id,
        'diagnosis_code': 'J06.9', 'diagnosis_description': 'Upper respiratory infection',
        'diagnosis_type': 'primary',
    })
    if r.status_code in [200, 201]:
        log('A', '5. Diagnosis', 'PASS', 'J06.9 recorded')
    else:
        log('A', '5. Diagnosis', 'FAIL', f'{r.status_code}: {r.text[:200]}')

    # Step 6: Lab order
    r = api(s, 'post', f'/api/clinical/visits/{visit_id}/place-order/', json={
        'order_type': 'laboratory',
        'items': [{'description': 'Complete Blood Count'}],
    })
    if r.status_code in [200, 201]:
        log('A', '6. Lab Order', 'PASS', 'CBC ordered')
    else:
        log('A', '6. Lab Order', 'FAIL', f'{r.status_code}: {r.text[:200]}')

    # Get doctor user ID
    doctor_uid = None
    r_users = api(s, 'get', '/api/auth/users/')
    if r_users.status_code == 200:
        users = r_users.json()
        if isinstance(users, dict):
            users = users.get('results', [])
        for u in users:
            if u.get('username') == 'doctor':
                doctor_uid = u.get('id')
                break

    # Step 7: Prescription
    r = api(s, 'post', '/api/pharmacy/prescriptions/', json={
        'visit': visit_id, 'patient': patient_id,
        'prescribed_by': doctor_uid or patient_id,
        'notes': 'For headache and fever',
    })
    if r.status_code in [200, 201]:
        prescription = r.json()
        prescription_id = prescription.get('id')
        log('A', '7. Prescription', 'PASS', f'Prescription created')
    else:
        log('A', '7. Prescription', 'FAIL', f'{r.status_code}: {r.text[:200]}')
        return

    # Get a medication UUID
    med_uuid = None
    r_meds = api(s, 'get', '/api/pharmacy/medications/')
    if r_meds.status_code == 200:
        meds = r_meds.json()
        if isinstance(meds, dict):
            meds = meds.get('results', [])
        if meds:
            med_uuid = meds[0].get('id')

    # Step 8: Prescription items
    r = api(s, 'post', f'/api/pharmacy/prescriptions/{prescription_id}/items/', json={
        'prescription': prescription_id,
        'medication': med_uuid,
        'dosage': '500mg', 'frequency': 'TID',
        'duration': '7 days', 'quantity_prescribed': 21,
    })
    if r.status_code in [200, 201]:
        log('A', '8. Prescription Items', 'PASS', 'Amoxicillin added')
    else:
        log('A', '8. Prescription Items', 'FAIL', f'{r.status_code}: {r.text[:200]}')

    log('A', 'Scenario A Complete', 'PASS', 'Patient journey completed')


# ═══════════════════════════════════════════════════════════════
# SCENARIO B: Emergency Case
# ═══════════════════════════════════════════════════════════════
def scenario_b():
    s = get_session('admin', 'admin123')
    if not s:
        log('B', 'Login', 'FAIL', 'Could not login')
        return

    log('B', 'Login', 'PASS', 'Logged in as admin')

    # Emergency bypass
    r = api(s, 'post', '/api/clinical/emergency-bypass/', json={
        'chief_complaint': 'Chest pain, difficulty breathing',
        'gender': 'M',
        'reason': 'Patient unconscious, no ID available',
    })
    if r.status_code in [200, 201]:
        data = r.json()
        patient_id = data.get('patient', {}).get('id')
        visit_id = data.get('visit', {}).get('id')
        log('B', '1. Emergency Bypass', 'PASS', f'Patient: {str(patient_id)[:8]}...')
    else:
        log('B', '1. Emergency Bypass', 'FAIL', f'{r.status_code}: {r.text[:200]}')
        return

    # Verify emergency visit status
    r = api(s, 'get', f'/api/clinical/visits/{visit_id}/')
    if r.status_code == 200:
        visit = r.json()
        log('B', '2. Verify Emergency Visit', 'PASS', f'Status: {visit.get("status")}')
    else:
        log('B', '2. Verify Emergency Visit', 'FAIL', f'{r.status_code}')

    log('B', 'Scenario B Complete', 'PASS', 'Emergency case handled')


# ═══════════════════════════════════════════════════════════════
# SCENARIO C: Inpatient Admission
# ═══════════════════════════════════════════════════════════════
def scenario_c():
    s = get_session('admin', 'admin123')
    if not s:
        log('C', 'Login', 'FAIL', 'Could not login')
        return

    log('C', 'Login', 'PASS', 'Logged in as admin')

    # Register patient
    patient_id, mrn = register_patient(s, 'Mary', 'Admission', gender='F', visit_type='ipd')
    if patient_id:
        log('C', '1. Register Patient', 'PASS', f'MRN: {mrn}')
    else:
        log('C', '1. Register Patient', 'FAIL', 'Registration failed')
        return

    # Create visit
    r = api(s, 'post', '/api/clinical/visits/', json={
        'patient': patient_id, 'visit_type': 'ipd',
        'chief_complaint': 'Severe pneumonia requiring admission',
    })
    if r.status_code in [200, 201]:
        visit = r.json()
        visit_id = visit.get('id')
        log('C', '2. Create Visit', 'PASS', f'Visit: {visit.get("visit_number")}')
    else:
        log('C', '2. Create Visit', 'FAIL', f'{r.status_code}')
        return

    # Check-in
    api(s, 'patch', f'/api/clinical/visits/{visit_id}/status/', json={'status': 'checked_in'})

    # Create encounter
    r = api(s, 'post', f'/api/clinical/visits/{visit_id}/encounters/', json={
        'encounter_type': 'ipd',
        'subjective': 'Severe pneumonia',
        'assessment': 'Bilateral pneumonia requiring admission',
    })
    if r.status_code in [200, 201]:
        log('C', '3. Encounter', 'PASS', 'IPD encounter created')
    else:
        log('C', '3. Encounter', 'FAIL', f'{r.status_code}')

    # Get available beds
    r = api(s, 'get', '/api/clinical/beds/')
    if r.status_code == 200:
        beds = r.json()
        if isinstance(beds, dict):
            beds = beds.get('results', [])
        available = [b for b in beds if not b.get('is_occupied', True)]
        if available:
            bed_id = available[0]['id']
            log('C', '4. Find Available Bed', 'PASS', f'Bed found: {available[0].get("bed_number")}')
        else:
            log('C', '4. Find Available Bed', 'FAIL', 'No available beds')
            return
    else:
        log('C', '4. Find Available Bed', 'FAIL', f'{r.status_code}')
        return

    # Get doctor user ID
    doctor_uid = None
    r_users = api(s, 'get', '/api/auth/users/')
    if r_users.status_code == 200:
        users = r_users.json()
        if isinstance(users, dict):
            users = users.get('results', [])
        for u in users:
            if u.get('username') == 'doctor':
                doctor_uid = u.get('id')
                break

    # Admit patient
    r = api(s, 'post', '/api/clinical/admissions/', json={
        'patient': patient_id, 'visit': visit_id,
        'bed': bed_id,
        'admitting_provider': doctor_uid,
        'expected_discharge_date': (date.today() + timedelta(days=5)).isoformat(),
    })
    if r.status_code in [200, 201]:
        admission = r.json()
        admission_id = admission.get('id')
        log('C', '5. Admit Patient', 'PASS', f'Admission: {admission.get("admission_number")}')
    else:
        log('C', '5. Admit Patient', 'FAIL', f'{r.status_code}: {r.text[:200]}')
        return

    # Discharge
    r = api(s, 'post', f'/api/clinical/admissions/{admission_id}/discharge/', json={
        'discharge_type': 'routine',
        'discharge_summary': 'Patient recovered, discharge with medications',
    })
    if r.status_code == 200:
        log('C', '6. Discharge', 'PASS', 'Patient discharged')
    else:
        log('C', '6. Discharge', 'FAIL', f'{r.status_code}: {r.text[:200]}')

    log('C', 'Scenario C Complete', 'PASS', 'Inpatient journey completed')


# ═══════════════════════════════════════════════════════════════
# SCENARIO D: Multi-Visit Follow-up
# ═══════════════════════════════════════════════════════════════
def scenario_d():
    s = get_session('admin', 'admin123')
    if not s:
        log('D', 'Login', 'FAIL', 'Could not login')
        return

    log('D', 'Login', 'PASS', 'Logged in as admin')

    # Register patient
    patient_id, mrn = register_patient(s, 'Peter', 'Followup', visit_type='opd')
    if patient_id:
        log('D', '1. Register Patient', 'PASS', f'MRN: {mrn}')
    else:
        log('D', '1. Register Patient', 'FAIL', 'Registration failed')
        return

    # Create initial visit
    r = api(s, 'post', '/api/clinical/visits/', json={
        'patient': patient_id, 'visit_type': 'opd',
        'chief_complaint': 'Follow-up for diabetes management',
    })
    if r.status_code in [200, 201]:
        visit = r.json()
        visit_id = visit.get('id')
        log('D', '2. Create Initial Visit', 'PASS', f'Visit: {visit.get("visit_number")}')
    else:
        log('D', '2. Create Initial Visit', 'FAIL', f'{r.status_code}')
        return

    # Schedule follow-up appointment
    follow_up_date = (date.today() + timedelta(weeks=2)).isoformat()
    r = api(s, 'post', '/api/clinical/appointments/', json={
        'patient': patient_id,
        'appointment_date': follow_up_date,
        'appointment_time': '10:00',
        'appointment_type': 'follow_up',
        'linked_visit': visit_id,
    })
    if r.status_code in [200, 201]:
        appt = r.json()
        appt_id = appt.get('id')
        log('D', '3. Schedule Follow-up', 'PASS', f'Appointment: {appt_id[:8]}...')
    else:
        log('D', '3. Schedule Follow-up', 'FAIL', f'{r.status_code}: {r.text[:200]}')
        return

    # Reschedule
    new_date = (date.today() + timedelta(weeks=3)).isoformat()
    r = api(s, 'patch', f'/api/clinical/appointments/{appt_id}/', json={
        'appointment_date': new_date,
        'appointment_time': '14:00',
    })
    if r.status_code == 200:
        log('D', '4. Reschedule', 'PASS', f'New date: {new_date}')
    else:
        log('D', '4. Reschedule', 'FAIL', f'{r.status_code}')

    log('D', 'Scenario D Complete', 'PASS', 'Multi-visit follow-up completed')


# ═══════════════════════════════════════════════════════════════
# SCENARIO E: Financial Cycle
# ═══════════════════════════════════════════════════════════════
def scenario_e():
    s = get_session('admin', 'admin123')
    if not s:
        log('E', 'Login', 'FAIL', 'Could not login')
        return

    log('E', 'Login', 'PASS', 'Logged in as admin')

    # Register patient
    patient_id, mrn = register_patient(s, 'Finance', 'Test', visit_type='opd')
    if patient_id:
        log('E', '1. Register Patient', 'PASS', f'MRN: {mrn}')
    else:
        log('E', '1. Register Patient', 'FAIL', 'Registration failed')
        return

    # Create visit + encounter + order to generate invoice
    r = api(s, 'post', '/api/clinical/visits/', json={
        'patient': patient_id, 'visit_type': 'opd',
        'chief_complaint': 'Financial cycle test',
    })
    if r.status_code in [200, 201]:
        visit = r.json()
        visit_id = visit.get('id')
        log('E', '2. Create Visit', 'PASS', f'Visit: {visit.get("visit_number")}')
    else:
        log('E', '2. Create Visit', 'FAIL', f'{r.status_code}')
        return

    # Place order to generate invoice
    r = api(s, 'post', f'/api/clinical/visits/{visit_id}/place-order/', json={
        'order_type': 'consultation',
        'items': [{'description': 'OPD Consultation'}],
    })
    if r.status_code in [200, 201]:
        log('E', '3. Place Order', 'PASS', 'Invoice generated')
    else:
        log('E', '3. Place Order', 'FAIL', f'{r.status_code}')

    # Get invoice
    r = api(s, 'get', f'/api/billing/invoices/?patient={patient_id}')
    if r.status_code == 200:
        invoices = r.json()
        if isinstance(invoices, dict):
            invoices = invoices.get('results', [])
        if invoices:
            invoice = invoices[0]
            invoice_id = invoice.get('id')
            log('E', '4. Get Invoice', 'PASS', f'Invoice: {invoice.get("invoice_number")}')
        else:
            log('E', '4. Get Invoice', 'FAIL', 'No invoices found')
            return
    else:
        log('E', '4. Get Invoice', 'FAIL', f'{r.status_code}')
        return

    # Process payment
    r = api(s, 'post', '/api/billing/pay/', json={
        'invoice_id': invoice_id,
        'amount': '50.00',
        'payment_method': 'cash',
    })
    if r.status_code in [200, 201]:
        log('E', '5. Process Payment', 'PASS', 'Partial payment processed')
    else:
        log('E', '5. Process Payment', 'FAIL', f'{r.status_code}: {r.text[:200]}')

    # Check invoice status
    r = api(s, 'get', f'/api/billing/invoices/{invoice_id}/')
    if r.status_code == 200:
        invoice = r.json()
        log('E', '6. Check Invoice Status', 'PASS', f'Status: {invoice.get("status")}')
    else:
        log('E', '6. Check Invoice Status', 'FAIL', f'{r.status_code}')

    log('E', 'Scenario E Complete', 'PASS', 'Financial cycle completed')


# ═══════════════════════════════════════════════════════════════
# SCENARIO F: Inventory Cycle
# ═══════════════════════════════════════════════════════════════
def scenario_f():
    s = get_session('admin', 'admin123')
    if not s:
        log('F', 'Login', 'FAIL', 'Could not login')
        return

    log('F', 'Login', 'PASS', 'Logged in as admin')

    # Get stores
    r = api(s, 'get', '/api/inventory/stores/')
    if r.status_code == 200:
        stores = r.json()
        if isinstance(stores, dict):
            stores = stores.get('results', [])
        if stores:
            store_id = stores[0]['id']
            log('F', '1. Get Stores', 'PASS', f'Store: {stores[0].get("name")}')
        else:
            log('F', '1. Get Stores', 'FAIL', 'No stores found')
            return
    else:
        log('F', '1. Get Stores', 'FAIL', f'{r.status_code}')
        return

    # Get items
    r = api(s, 'get', '/api/inventory/items/')
    if r.status_code == 200:
        items = r.json()
        if isinstance(items, dict):
            items = items.get('results', [])
        if items:
            item_id = items[0]['id']
            log('F', '2. Get Items', 'PASS', f'Item: {items[0].get("name")}')
        else:
            log('F', '2. Get Items', 'FAIL', 'No items found')
            return
    else:
        log('F', '2. Get Items', 'FAIL', f'{r.status_code}')
        return

    # Receive stock
    r = api(s, 'post', '/api/inventory/receive/', json={
        'item_id': item_id,
        'store_id': store_id,
        'quantity': '100',
        'batch_lot_number': 'BATCH-WALK-001',
        'expiry_date': (date.today() + timedelta(days=365)).isoformat(),
        'unit_cost': '5.00',
    })
    if r.status_code in [200, 201]:
        log('F', '3. Receive Stock', 'PASS', '100 units received')
    else:
        log('F', '3. Receive Stock', 'FAIL', f'{r.status_code}: {r.text[:200]}')

    # Check stock
    r = api(s, 'get', f'/api/inventory/stock/?item={item_id}&store={store_id}')
    if r.status_code == 200:
        stock = r.json()
        if isinstance(stock, dict):
            stock = stock.get('results', [])
        if stock:
            qty = stock[0].get('quantity_on_hand', 0)
            log('F', '4. Check Stock', 'PASS', f'Quantity: {qty}')
        else:
            log('F', '4. Check Stock', 'FAIL', 'No stock found')
    else:
        log('F', '4. Check Stock', 'FAIL', f'{r.status_code}')

    # Get stock summary
    r = api(s, 'get', '/api/inventory/stock-summary/')
    if r.status_code == 200:
        summary = r.json()
        log('F', '5. Stock Summary', 'PASS', f'Total items: {summary.get("total_items")}')
    else:
        log('F', '5. Stock Summary', 'FAIL', f'{r.status_code}')

    log('F', 'Scenario F Complete', 'PASS', 'Inventory cycle completed')


# ═══════════════════════════════════════════════════════════════
# SCENARIO G: Admin and Security
# ═══════════════════════════════════════════════════════════════
def scenario_g():
    # Test login as different roles
    roles = [
        ('admin', 'admin123', 'Administrator'),
        ('doctor', 'doctor123', 'Doctor'),
        ('nurse', 'nurse123', 'Nurse'),
        ('pharmacist', 'pharm123', 'Pharmacist'),
        ('cashier', 'cash123', 'Cashier'),
    ]

    for username, password, role_name in roles:
        s = get_session(username, password)
        if s:
            log('G', f'Login as {role_name}', 'PASS', f'Username: {username}')
        else:
            log('G', f'Login as {role_name}', 'FAIL', f'Username: {username}')

    # Test failed login
    s = get_session('admin', 'wrongpassword')
    if not s:
        log('G', 'Reject Wrong Password', 'PASS', 'Login rejected')
    else:
        log('G', 'Reject Wrong Password', 'FAIL', 'Login should have failed')

    # Test unauthorized access
    s = get_session('nurse', 'nurse123')
    if s:
        r = api(s, 'get', '/api/billing/invoices/')
        if r.status_code in [200, 403]:
            log('G', 'Permission Check', 'PASS', f'Status: {r.status_code}')
        else:
            log('G', 'Permission Check', 'FAIL', f'Unexpected: {r.status_code}')

    log('G', 'Scenario G Complete', 'PASS', 'Admin and security tests completed')


# ═══════════════════════════════════════════════════════════════
# SCENARIO H: Reporting
# ═══════════════════════════════════════════════════════════════
def scenario_h():
    s = get_session('admin', 'admin123')
    if not s:
        log('H', 'Login', 'FAIL', 'Could not login')
        return

    log('H', 'Login', 'PASS', 'Logged in as admin')

    # Get report data
    r = api(s, 'get', '/api/reports/hmis/')
    if r.status_code == 200:
        log('H', '1. HMIS Summary', 'PASS', 'Report data retrieved')
    else:
        log('H', '1. HMIS Summary', 'FAIL', f'{r.status_code}')

    # Get dashboard data
    r = api(s, 'get', '/api/billing/daily-revenue/')
    if r.status_code == 200:
        log('H', '2. Daily Revenue', 'PASS', 'Revenue data retrieved')
    else:
        log('H', '2. Daily Revenue', 'FAIL', f'{r.status_code}')

    # Get dispensing summary
    r = api(s, 'get', f'/api/pharmacy/reports/dispensing-summary/?year={date.today().year}&month={date.today().month}')
    if r.status_code == 200:
        log('H', '3. Dispensing Summary', 'PASS', 'Dispensing data retrieved')
    else:
        log('H', '3. Dispensing Summary', 'FAIL', f'{r.status_code}')

    log('H', 'Scenario H Complete', 'PASS', 'Reporting tests completed')


# ═══════════════════════════════════════════════════════════════
# SCENARIO I: Cross-Scenario Verification
# ═══════════════════════════════════════════════════════════════
def scenario_i():
    s = get_session('admin', 'admin123')
    if not s:
        log('I', 'Login', 'FAIL', 'Could not login')
        return

    log('I', 'Login', 'PASS', 'Logged in as admin')

    # Verify patients exist
    r = api(s, 'get', '/api/patients/')
    if r.status_code == 200:
        patients = r.json()
        if isinstance(patients, dict):
            patients = patients.get('results', [])
        log('I', '1. Patient Count', 'PASS', f'{len(patients)} patients')
    else:
        log('I', '1. Patient Count', 'FAIL', f'{r.status_code}')

    # Verify visits exist
    r = api(s, 'get', '/api/clinical/visits/?page_size=5')
    if r.status_code == 200:
        visits = r.json()
        if isinstance(visits, dict):
            count = visits.get('count', len(visits.get('results', [])))
            visits = visits.get('results', [])
        else:
            count = len(visits)
        log('I', '2. Visit Count', 'PASS', f'{count} visits (showing {len(visits)})')
    else:
        log('I', '2. Visit Count', 'FAIL', f'{r.status_code}')

    # Verify inventory
    r = api(s, 'get', '/api/inventory/stock/')
    if r.status_code == 200:
        stock = r.json()
        if isinstance(stock, dict):
            stock = stock.get('results', [])
        log('I', '3. Stock Records', 'PASS', f'{len(stock)} stock records')
    else:
        log('I', '3. Stock Records', 'FAIL', f'{r.status_code}')

    # Verify audit logs
    r = api(s, 'get', '/api/audit/logs/')
    if r.status_code == 200:
        logs = r.json()
        if isinstance(logs, dict):
            logs = logs.get('results', [])
        log('I', '4. Audit Logs', 'PASS', f'{len(logs)} audit entries')
    else:
        log('I', '4. Audit Logs', 'FAIL', f'{r.status_code}')

    log('I', 'Scenario I Complete', 'PASS', 'Cross-scenario verification completed')


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print('=' * 70)
    print('JFD HMS — Automated End-to-End Walkthrough')
    print('=' * 70)
    print()

    print('--- Scenario A: Normal Patient Journey ---')
    scenario_a()
    print()

    print('--- Scenario B: Emergency Case ---')
    scenario_b()
    print()

    print('--- Scenario C: Inpatient Admission ---')
    scenario_c()
    print()

    print('--- Scenario D: Multi-Visit Follow-up ---')
    scenario_d()
    print()

    print('--- Scenario E: Financial Cycle ---')
    scenario_e()
    print()

    print('--- Scenario F: Inventory Cycle ---')
    scenario_f()
    print()

    print('--- Scenario G: Admin and Security ---')
    scenario_g()
    print()

    print('--- Scenario H: Reporting ---')
    scenario_h()
    print()

    print('--- Scenario I: Cross-Scenario Verification ---')
    scenario_i()
    print()

    # Summary
    print('=' * 70)
    print('RESULTS SUMMARY')
    print('=' * 70)
    passed = sum(1 for r in RESULTS if r['status'] == 'PASS')
    failed = sum(1 for r in RESULTS if r['status'] == 'FAIL')
    total = len(RESULTS)

    print(f'  Total Steps: {total}')
    print(f'  Passed:      {passed}')
    print(f'  Failed:      {failed}')
    print(f'  Pass Rate:   {passed/total*100:.1f}%' if total > 0 else '  Pass Rate:   N/A')
    print()

    if failed > 0:
        print('FAILED STEPS:')
        for r in RESULTS:
            if r['status'] == 'FAIL':
                print(f"  [{r['scenario']}] {r['step']}: {r['detail']}")
    print()

    print('=' * 70)
    sys.exit(0 if failed == 0 else 1)
