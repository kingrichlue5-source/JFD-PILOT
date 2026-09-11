import os
import django
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jfd_hms.settings')
django.setup()

from users_auth.models import Department, User, Role
from patients.models import Patient, PatientAllergy, PatientAlert
from clinical.models import (
    Ward, Room, Bed, Visit, TriageRecord, Encounter, VitalSigns, Diagnosis, Order,
    LabTestCatalogue, RadiologyTestCatalogue, DiagnosticResult, Admission, ProgressNote, NursingNote
)
from billing.models import PriceList, ServiceItem, ServicePrice, Invoice, InvoiceLineItem, Payment, CashierShift
from pharmacy.models import Medication, Prescription, PrescriptionItem, MedicationDispensing
from inventory.models import Category, Item, Store, Stock, StockMovement

def seed():
    print("Beginning database seeding for JFD Memorial Regional Referral Hospital...")

    # 1. Departments
    dept_med, _ = Department.objects.get_or_create(code='MED', defaults={'name': 'Internal Medicine', 'is_clinical': True})
    dept_surg, _ = Department.objects.get_or_create(code='SURG', defaults={'name': 'General Surgery', 'is_clinical': True})
    dept_ped, _ = Department.objects.get_or_create(code='PED', defaults={'name': 'Pediatrics', 'is_clinical': True})
    dept_obgyn, _ = Department.objects.get_or_create(code='OBGYN', defaults={'name': 'Obstetrics & Gynecology', 'is_clinical': True})
    dept_er, _ = Department.objects.get_or_create(code='ER', defaults={'name': 'Emergency Room', 'is_clinical': True})
    dept_lab, _ = Department.objects.get_or_create(code='LAB', defaults={'name': 'Laboratory & Pathology', 'is_clinical': True})
    dept_rad, _ = Department.objects.get_or_create(code='RAD', defaults={'name': 'Radiology & Imaging', 'is_clinical': True})
    dept_pharm, _ = Department.objects.get_or_create(code='PHARM', defaults={'name': 'Pharmacy', 'is_clinical': False})
    dept_opd, _ = Department.objects.get_or_create(code='OPD', defaults={'name': 'Outpatient Department', 'is_clinical': True})
    dept_fin, _ = Department.objects.get_or_create(code='FIN', defaults={'name': 'Finance & Cashier', 'is_clinical': False})

    # 2. Staff Users
    admin_user, _ = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@jfdhospital.gov.lr',
            'first_name': 'System',
            'last_name': 'Administrator',
            'job_title': 'ICT Director',
            'department': dept_opd,
            'is_staff': True,
            'is_superuser': True
        }
    )
    admin_user.set_password('admin123')
    admin_user.save()

    dr_nishant, _ = User.objects.get_or_create(
        username='dr_nishant',
        defaults={'email': 'nishant@jfdhospital.gov.lr', 'first_name': 'Dr. Nishant', 'last_name': 'Clinician', 'job_title': 'Chief Medical Officer', 'department': dept_opd}
    )
    dr_nishant.set_password('doctor123')
    dr_nishant.save()

    dr_sarah, _ = User.objects.get_or_create(
        username='dr_sarah',
        defaults={'email': 'sarah@jfdhospital.gov.lr', 'first_name': 'Dr. Sarah', 'last_name': 'Hosten', 'job_title': 'Senior OBGYN Specialist', 'department': dept_obgyn}
    )
    dr_sarah.set_password('doctor123')
    dr_sarah.save()

    nurse_sufiya, _ = User.objects.get_or_create(
        username='nurse_sufiya',
        defaults={'email': 'sufiya@jfdhospital.gov.lr', 'first_name': 'Sufiya', 'last_name': 'Kollie', 'job_title': 'Triage Head Nurse', 'department': dept_er}
    )
    nurse_sufiya.set_password('nurse123')
    nurse_sufiya.save()

    cashier_ghulam, _ = User.objects.get_or_create(
        username='cashier_ghulam',
        defaults={'email': 'ghulam@jfdhospital.gov.lr', 'first_name': 'Ghulam', 'last_name': 'Product', 'job_title': 'Lead Cashier', 'department': dept_fin}
    )
    cashier_ghulam.set_password('cashier123')
    cashier_ghulam.save()

    # 3. Wards, Rooms, Beds
    ward_med, _ = Ward.objects.get_or_create(code='MED1', defaults={'name': 'Medical Ward 1', 'department': dept_med, 'capacity': 20})
    ward_surg, _ = Ward.objects.get_or_create(code='SURG1', defaults={'name': 'Surgical Ward 1', 'department': dept_surg, 'capacity': 15})
    ward_mat, _ = Ward.objects.get_or_create(code='MAT1', defaults={'name': 'Maternity Ward', 'department': dept_obgyn, 'capacity': 15})
    ward_er, _ = Ward.objects.get_or_create(code='ER1', defaults={'name': 'ER Resuscitation & Holding', 'department': dept_er, 'capacity': 10})

    room_med_101, _ = Room.objects.get_or_create(ward=ward_med, room_number='101', defaults={'capacity': 4})
    room_med_102, _ = Room.objects.get_or_create(ward=ward_med, room_number='102', defaults={'capacity': 4})
    room_mat_201, _ = Room.objects.get_or_create(ward=ward_mat, room_number='201', defaults={'capacity': 2})

    bed_101_a, _ = Bed.objects.get_or_create(room=room_med_101, bed_number='Bed 1A', defaults={'is_occupied': True})
    bed_101_b, _ = Bed.objects.get_or_create(room=room_med_101, bed_number='Bed 1B', defaults={'is_occupied': False})
    bed_102_a, _ = Bed.objects.get_or_create(room=room_med_102, bed_number='Bed 2A', defaults={'is_occupied': False})
    bed_mat_1, _ = Bed.objects.get_or_create(room=room_mat_201, bed_number='Bed M1', defaults={'is_occupied': True})

    # 4. Service Catalogue & Price Lists
    price_list, _ = PriceList.objects.get_or_create(code='STD-2026', defaults={'name': 'Standard Hospital Tariffs 2026', 'is_default': True})

    svc_opd, _ = ServiceItem.objects.get_or_create(code='CONS-OPD', defaults={'name': 'Outpatient General Consultation', 'category': 'Consultation'})
    svc_er, _ = ServiceItem.objects.get_or_create(code='CONS-ER', defaults={'name': 'Emergency Resuscitation & Assessment', 'category': 'Emergency'})
    svc_lab_cbc, _ = ServiceItem.objects.get_or_create(code='LAB-CBC', defaults={'name': 'Complete Blood Count (CBC)', 'category': 'Laboratory'})
    svc_lab_mal, _ = ServiceItem.objects.get_or_create(code='LAB-MAL', defaults={'name': 'Malaria Parasite RDT / Smear', 'category': 'Laboratory'})
    svc_rad_cxr, _ = ServiceItem.objects.get_or_create(code='RAD-CXR', defaults={'name': 'Chest X-Ray Digital', 'category': 'Radiology'})

    ServicePrice.objects.get_or_create(service_item=svc_opd, price_list=price_list, effective_date=date(2026,1,1), defaults={'price': Decimal('10.00')})
    ServicePrice.objects.get_or_create(service_item=svc_er, price_list=price_list, effective_date=date(2026,1,1), defaults={'price': Decimal('20.00')})
    ServicePrice.objects.get_or_create(service_item=svc_lab_cbc, price_list=price_list, effective_date=date(2026,1,1), defaults={'price': Decimal('15.00')})
    ServicePrice.objects.get_or_create(service_item=svc_lab_mal, price_list=price_list, effective_date=date(2026,1,1), defaults={'price': Decimal('8.00')})
    ServicePrice.objects.get_or_create(service_item=svc_rad_cxr, price_list=price_list, effective_date=date(2026,1,1), defaults={'price': Decimal('25.00')})

    # 5. Diagnostic Catalogues
    LabTestCatalogue.objects.get_or_create(code='CBC-01', defaults={'name': 'Complete Blood Count (CBC)', 'category': 'Hematology', 'specimen_type': 'Whole Blood', 'price': Decimal('15.00')})
    LabTestCatalogue.objects.get_or_create(code='MAL-01', defaults={'name': 'Malaria RDT & Thick Film', 'category': 'Parasitology', 'specimen_type': 'Capillary Blood', 'price': Decimal('8.00')})
    LabTestCatalogue.objects.get_or_create(code='WIDAL-01', defaults={'name': 'Typhoid Widal Screen', 'category': 'Serology', 'specimen_type': 'Serum', 'price': Decimal('10.00')})

    RadiologyTestCatalogue.objects.get_or_create(code='CXR-01', defaults={'name': 'Chest X-Ray AP/Lateral', 'modality': 'X-Ray', 'body_part': 'Chest', 'price': Decimal('25.00')})
    RadiologyTestCatalogue.objects.get_or_create(code='USG-OB', defaults={'name': 'Obstetric Ultrasound Scan', 'modality': 'Ultrasound', 'body_part': 'Abdomen/Pelvis', 'price': Decimal('30.00')})

    # 6. Medications & Inventory Stores
    med_coartem, _ = Medication.objects.get_or_create(name='Coartem (Artemether 20mg / Lumefantrine 120mg)', defaults={'generic_name': 'Artemether + Lumefantrine', 'category': 'Antimalarial', 'dosage_form': 'Tablet', 'strength': '20/120mg'})
    med_amox, _ = Medication.objects.get_or_create(name='Amoxicillin 500mg Capsules', defaults={'generic_name': 'Amoxicillin', 'category': 'Antibiotic', 'dosage_form': 'Capsule', 'strength': '500mg'})
    med_para, _ = Medication.objects.get_or_create(name='Paracetamol 500mg Tablets', defaults={'generic_name': 'Paracetamol', 'category': 'Analgesic', 'dosage_form': 'Tablet', 'strength': '500mg'})
    med_saline, _ = Medication.objects.get_or_create(name='Normal Saline 0.9% IV Infusion 500ml', defaults={'generic_name': 'Sodium Chloride', 'category': 'IV Fluids', 'dosage_form': 'Infusion', 'strength': '0.9% 500ml'})
    med_oxy, _ = Medication.objects.get_or_create(name='Oxytocin 10 IU/ml Ampoule', defaults={'generic_name': 'Oxytocin', 'category': 'Uterotonic', 'dosage_form': 'Injection', 'strength': '10 IU/ml'})

    main_store, _ = Store.objects.get_or_create(code='MAIN-STORE', defaults={'name': 'Central Medical Store', 'store_type': 'Central'})
    pharm_store, _ = Store.objects.get_or_create(code='OPD-PHARM', defaults={'name': 'Outpatient Pharmacy Dispensing', 'store_type': 'Dispensary'})

    cat_pharma, _ = Category.objects.get_or_create(code='CAT-MED', defaults={'name': 'Pharmaceuticals'})
    item_coartem, _ = Item.objects.get_or_create(code='ITEM-COAR', defaults={'name': 'Coartem 20/120mg', 'unit_of_measure': 'Box of 24', 'category': cat_pharma, 'is_medication': True, 'medication': med_coartem, 'reorder_level': 20})
    item_amox, _ = Item.objects.get_or_create(code='ITEM-AMOX', defaults={'name': 'Amoxicillin 500mg', 'unit_of_measure': 'Pack of 100', 'category': cat_pharma, 'is_medication': True, 'medication': med_amox, 'reorder_level': 15})

    Stock.objects.get_or_create(item=item_coartem, store=pharm_store, batch_lot_number='BATCH-2026-A1', defaults={'quantity_on_hand': Decimal('150.00'), 'expiry_date': date(2027, 6, 30), 'unit_cost': Decimal('5.00')})
    Stock.objects.get_or_create(item=item_amox, store=pharm_store, batch_lot_number='BATCH-2026-B2', defaults={'quantity_on_hand': Decimal('80.00'), 'expiry_date': date(2027, 8, 15), 'unit_cost': Decimal('4.50')})

    # 7. Patients
    p1, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00001',
        defaults={
            'first_name': 'Varun',
            'last_name': 'Bose',
            'gender': 'M',
            'date_of_birth': date(1994, 5, 12),
            'phone': '0770994748',
            'city': 'Tappita',
            'country': 'Liberia',
            'address_line1': 'Central Tappita, Nimba County',
            'emergency_contact_name': 'Mary Bose',
            'emergency_contact_phone': '0770112233',
            'payer_category': 'Private Cash'
        }
    )

    p2, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00002',
        defaults={
            'first_name': 'Jhon',
            'last_name': 'Wick',
            'gender': 'M',
            'date_of_birth': date(1981, 8, 20),
            'phone': '0880152912',
            'city': 'Tappita',
            'country': 'Liberia',
            'payer_category': 'Insurance'
        }
    )

    p3, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00003',
        defaults={
            'first_name': 'Johny',
            'last_name': 'Ive',
            'gender': 'M',
            'date_of_birth': date(1995, 3, 14),
            'phone': '02035006370',
            'city': 'Monrovia',
            'country': 'Liberia',
            'payer_category': 'Private Cash'
        }
    )

    p4, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00004',
        defaults={
            'first_name': 'Sufiya',
            'last_name': 'Flomo',
            'gender': 'F',
            'date_of_birth': date(1998, 11, 4),
            'phone': '09245787845',
            'city': 'Tappita',
            'country': 'Liberia',
            'payer_category': 'Maternal Free Care'
        }
    )

    p5, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00005',
        defaults={
            'first_name': 'David',
            'last_name': 'John',
            'gender': 'M',
            'date_of_birth': date(1971, 1, 15),
            'phone': '06154817037',
            'city': 'Ganta',
            'country': 'Liberia',
            'payer_category': 'Private Cash'
        }
    )

    p6, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00006',
        defaults={
            'first_name': 'Emma',
            'last_name': 'Kollie',
            'gender': 'F',
            'date_of_birth': date(1996, 7, 22),
            'phone': '07608440455',
            'city': 'Sanniquellie',
            'country': 'Liberia',
            'payer_category': 'Emergency Care'
        }
    )

    p7, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00007',
        defaults={
            'first_name': 'Martha',
            'last_name': 'Clarke',
            'gender': 'F',
            'date_of_birth': date(1988, 4, 10),
            'phone': '0770123456',
            'city': 'Monrovia',
            'country': 'Liberia',
            'payer_category': 'Insurance'
        }
    )

    p8, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00008',
        defaults={
            'first_name': 'Samuel',
            'last_name': 'Doe',
            'gender': 'M',
            'date_of_birth': date(1965, 12, 1),
            'phone': '0880987654',
            'city': 'Buchanan',
            'country': 'Liberia',
            'payer_category': 'Government'
        }
    )

    p9, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00009',
        defaults={
            'first_name': 'Ruth',
            'last_name': 'Tweh',
            'gender': 'F',
            'date_of_birth': date(2001, 6, 18),
            'phone': '0770555123',
            'city': 'Harper',
            'country': 'Liberia',
            'payer_category': 'Private Cash'
        }
    )

    p10, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00010',
        defaults={
            'first_name': 'Emmanuel',
            'last_name': 'Mensah',
            'gender': 'M',
            'date_of_birth': date(1978, 9, 30),
            'phone': '0880444987',
            'city': 'Robertsport',
            'country': 'Liberia',
            'payer_category': 'Insurance'
        }
    )

    p11, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00011',
        defaults={
            'first_name': 'Grace',
            'last_name': 'Weah',
            'gender': 'F',
            'date_of_birth': date(1992, 2, 14),
            'phone': '0770666789',
            'city': 'Gbarnga',
            'country': 'Liberia',
            'payer_category': 'Maternal Free Care'
        }
    )

    p12, _ = Patient.objects.get_or_create(
        mrn='JFD-2026-00012',
        defaults={
            'first_name': 'Joseph',
            'last_name': 'Sackor',
            'gender': 'M',
            'date_of_birth': date(1955, 8, 25),
            'phone': '0880222345',
            'city': 'Voinjama',
            'country': 'Liberia',
            'payer_category': 'Private Cash'
        }
    )

    # 8. Visits & Triage Queue
    # Visit 1: In Triage Queue (Varun Bose)
    v1, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00001',
        defaults={
            'patient': p1,
            'visit_type': 'opd',
            'status': 'checked_in',
            'chief_complaint': 'Fever, chills, and severe headache for 3 days',
            'triage_priority': 'urgent',
            'check_in_time': datetime.now() - timedelta(minutes=56)
        }
    )
    TriageRecord.objects.get_or_create(
        visit=v1,
        defaults={
            'patient': p1,
            'chief_complaint': v1.chief_complaint,
            'acuity_level': 3,
            'temperature': Decimal('38.9'),
            'heart_rate': 98,
            'respiratory_rate': 20,
            'blood_pressure_systolic': 124,
            'blood_pressure_diastolic': 82,
            'oxygen_saturation': Decimal('97.5'),
            'weight': Decimal('68.5'),
            'height': Decimal('172.0'),
            'pain_scale': 5,
            'triage_nurse': nurse_sufiya
        }
    )

    # Visit 2: OPD Consultation Active (Jhon Wick)
    v2, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00002',
        defaults={
            'patient': p2,
            'visit_type': 'opd',
            'status': 'in_progress',
            'chief_complaint': 'Routine BP check, mild dizziness',
            'triage_priority': 'routine',
            'check_in_time': datetime.now() - timedelta(minutes=30),
            'provider': dr_nishant
        }
    )
    enc2, _ = Encounter.objects.get_or_create(
        visit=v2,
        defaults={
            'patient': p2,
            'encounter_type': 'opd',
            'provider': dr_nishant,
            'department': dept_opd,
            'subjective': 'Patient presents for routine BP check. Reports occasional dizziness.',
            'objective': 'BP: 145/92 mmHg, HR: 76 bpm, Temp: 36.6 C',
            'assessment': 'Essential Hypertension - Moderate control',
            'plan': 'Refill Amlodipine 5mg OD, order Lipid Profile & ECG, low salt diet counseling.',
            'diagnosis_primary': 'I10 - Essential (primary) hypertension'
        }
    )

    # Visit 3: In Triage (Johny Ive)
    v3, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00003',
        defaults={
            'patient': p3,
            'visit_type': 'opd',
            'status': 'checked_in',
            'chief_complaint': 'Abdominal discomfort after eating',
            'triage_priority': 'routine',
            'check_in_time': datetime.now() - timedelta(minutes=25)
        }
    )

    # Visit 4: OBGYN ANC Visit (Sufiya Flomo)
    v4, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00004',
        defaults={
            'patient': p4,
            'visit_type': 'obgyn',
            'status': 'in_progress',
            'chief_complaint': 'Routine Antenatal Visit - 32 weeks gestation',
            'triage_priority': 'routine',
            'check_in_time': datetime.now() - timedelta(hours=1, minutes=35),
            'provider': dr_sarah
        }
    )

    # Visit 5: IPD Admission (David John)
    v5, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00005',
        defaults={
            'patient': p5,
            'visit_type': 'ipd',
            'status': 'in_progress',
            'chief_complaint': 'Severe pneumonia with hypoxia',
            'triage_priority': 'stat',
            'check_in_time': datetime.now() - timedelta(days=2),
            'provider': dr_nishant
        }
    )
    Admission.objects.get_or_create(
        admission_number='ADM-2026-00001',
        defaults={
            'patient': p5,
            'visit': v5,
            'admitting_diagnosis': 'Community-Acquired Pneumonia (J18.9)',
            'ward': ward_med,
            'room': room_med_101,
            'bed': bed_101_a,
            'admitting_provider': dr_nishant,
            'status': 'active'
        }
    )

    # Visit 6: ER Resuscitation (Emma Kollie)
    v6, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00006',
        defaults={
            'patient': p6,
            'visit_type': 'er',
            'status': 'checked_in',
            'chief_complaint': 'Acute onset crushing chest pain radiating to jaw',
            'triage_priority': 'stat',
            'check_in_time': datetime.now() - timedelta(minutes=10)
        }
    )

    # Visit 7: OPD - Martha Clarke (pending prescription)
    v7, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00007',
        defaults={
            'patient': p7,
            'visit_type': 'opd',
            'status': 'in_progress',
            'chief_complaint': 'Persistent cough and fever for 5 days',
            'triage_priority': 'urgent',
            'check_in_time': datetime.now() - timedelta(minutes=45),
            'provider': dr_nishant
        }
    )
    enc7, _ = Encounter.objects.get_or_create(
        visit=v7,
        defaults={
            'patient': p7,
            'encounter_type': 'opd',
            'provider': dr_nishant,
            'department': dept_opd,
            'subjective': 'Patient reports productive cough, fever, and fatigue for 5 days.',
            'objective': 'Temp: 38.5C, RR: 22, SpO2: 96%, Chest: crackles right lower lobe.',
            'assessment': 'Community-Acquired Pneumonia (J18.9)',
            'plan': 'Chest X-Ray, CBC, Amoxicillin 500mg TDS x 7 days, Paracetamol PRN.',
            'diagnosis_primary': 'J18.9 - Pneumonia, unspecified organism'
        }
    )

    # Visit 8: OPD - Samuel Doe (unpaid invoice)
    v8, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00008',
        defaults={
            'patient': p8,
            'visit_type': 'opd',
            'status': 'in_progress',
            'chief_complaint': 'Lower back pain radiating to left leg for 2 weeks',
            'triage_priority': 'routine',
            'check_in_time': datetime.now() - timedelta(hours=2),
            'provider': dr_sarah
        }
    )

    # Visit 9: OBGYN - Ruth Tweh (ANC)
    v9, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00009',
        defaults={
            'patient': p9,
            'visit_type': 'obgyn',
            'status': 'in_progress',
            'chief_complaint': 'ANC visit - 28 weeks gestation',
            'triage_priority': 'routine',
            'check_in_time': datetime.now() - timedelta(hours=3),
            'provider': dr_sarah
        }
    )

    # Visit 10: OPD - Emmanuel Mensah (diabetes follow-up)
    v10, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00010',
        defaults={
            'patient': p10,
            'visit_type': 'opd',
            'status': 'checked_in',
            'chief_complaint': 'Diabetes follow-up, poor glycemic control',
            'triage_priority': 'routine',
            'check_in_time': datetime.now() - timedelta(hours=4),
            'provider': dr_nishant
        }
    )

    # Visit 11: OBGYN - Grace Weah (labor)
    v11, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00011',
        defaults={
            'patient': p11,
            'visit_type': 'obgyn',
            'status': 'in_progress',
            'chief_complaint': 'Active labor - 39 weeks, contractions every 5 minutes',
            'triage_priority': 'urgent',
            'check_in_time': datetime.now() - timedelta(hours=1),
            'provider': dr_sarah
        }
    )

    # Visit 12: ER - Joseph Sackor (trauma)
    v12, _ = Visit.objects.get_or_create(
        visit_number='VIS-2026-00012',
        defaults={
            'patient': p12,
            'visit_type': 'er',
            'status': 'in_progress',
            'chief_complaint': 'Fall from height, right wrist deformity',
            'triage_priority': 'urgent',
            'check_in_time': datetime.now() - timedelta(minutes=30)
        }
    )

    # 9. Cashier Invoices & Shifts
    shift, _ = CashierShift.objects.get_or_create(
        shift_number='SHIFT-2026-001',
        defaults={'cashier': cashier_ghulam, 'opening_balance': Decimal('100.00'), 'total_cash': Decimal('570.00')}
    )

    inv1, _ = Invoice.objects.get_or_create(
        invoice_number='INV-2026-00001',
        defaults={
            'patient': p2,
            'visit': v2,
            'subtotal': Decimal('35.00'),
            'total_amount': Decimal('35.00'),
            'amount_paid': Decimal('35.00'),
            'balance_due': Decimal('0.00'),
            'status': 'paid'
        }
    )
    Payment.objects.get_or_create(
        payment_number='PAY-2026-00001',
        receipt_number='REC-2026-00001',
        defaults={
            'invoice': inv1,
            'patient': p2,
            'amount': Decimal('35.00'),
            'payment_method': 'cash',
            'cashier_shift': shift,
            'received_by': cashier_ghulam
        }
    )

    # 10. Prescription & Dispensing
    rx, _ = Prescription.objects.get_or_create(
        prescription_number='RX-2026-00001',
        defaults={
            'visit': v2,
            'patient': p2,
            'encounter': enc2,
            'prescribed_by': dr_nishant,
            'status': 'completed'
        }
    )
    rx_item, _ = PrescriptionItem.objects.get_or_create(
        prescription=rx,
        medication=med_coartem,
        defaults={
            'dosage': '1 tablet',
            'frequency': 'Twice Daily (BD)',
            'duration': '3 days',
            'quantity_prescribed': Decimal('1.00'),
            'quantity_dispensed': Decimal('1.00'),
            'status': 'completed',
            'dispensed_by': admin_user,
            'dispensed_at': datetime.now()
        }
    )

    # Prescription for Martha Clarke (pending dispensing)
    rx7, _ = Prescription.objects.get_or_create(
        prescription_number='RX-2026-00002',
        defaults={
            'visit': v7,
            'patient': p7,
            'encounter': enc7,
            'prescribed_by': dr_nishant,
            'status': 'active'
        }
    )
    PrescriptionItem.objects.get_or_create(
        prescription=rx7,
        medication=med_amox,
        defaults={
            'dosage': '500mg',
            'frequency': 'Three Times Daily (TDS)',
            'duration': '7 days',
            'quantity_prescribed': Decimal('21.00'),
            'quantity_dispensed': Decimal('0.00'),
            'status': 'pending'
        }
    )
    PrescriptionItem.objects.get_or_create(
        prescription=rx7,
        medication=med_para,
        defaults={
            'dosage': '500mg',
            'frequency': 'As Needed (PRN)',
            'duration': '7 days',
            'quantity_prescribed': Decimal('14.00'),
            'quantity_dispensed': Decimal('0.00'),
            'status': 'pending'
        }
    )

    # Prescription for David John (pending)
    rx5, _ = Prescription.objects.get_or_create(
        prescription_number='RX-2026-00003',
        defaults={
            'visit': v5,
            'patient': p5,
            'prescribed_by': dr_nishant,
            'status': 'active'
        }
    )
    PrescriptionItem.objects.get_or_create(
        prescription=rx5,
        medication=med_amox,
        defaults={
            'dosage': '1g',
            'frequency': 'TDS',
            'duration': '10 days',
            'quantity_prescribed': Decimal('30.00'),
            'quantity_dispensed': Decimal('0.00'),
            'status': 'pending'
        }
    )
    PrescriptionItem.objects.get_or_create(
        prescription=rx5,
        medication=med_saline,
        defaults={
            'dosage': '500ml',
            'frequency': 'Once Daily',
            'duration': '5 days',
            'quantity_prescribed': Decimal('5.00'),
            'quantity_dispensed': Decimal('0.00'),
            'status': 'pending'
        }
    )

    # 11. More Invoices (unpaid)
    inv7, _ = Invoice.objects.get_or_create(
        invoice_number='INV-2026-00002',
        defaults={
            'patient': p7,
            'visit': v7,
            'subtotal': Decimal('53.00'),
            'total_amount': Decimal('53.00'),
            'amount_paid': Decimal('0.00'),
            'balance_due': Decimal('53.00'),
            'status': 'pending'
        }
    )

    inv8, _ = Invoice.objects.get_or_create(
        invoice_number='INV-2026-00003',
        defaults={
            'patient': p8,
            'visit': v8,
            'subtotal': Decimal('35.00'),
            'total_amount': Decimal('35.00'),
            'amount_paid': Decimal('0.00'),
            'balance_due': Decimal('35.00'),
            'status': 'pending'
        }
    )

    inv9, _ = Invoice.objects.get_or_create(
        invoice_number='INV-2026-00004',
        defaults={
            'patient': p10,
            'visit': v10,
            'subtotal': Decimal('25.00'),
            'total_amount': Decimal('25.00'),
            'amount_paid': Decimal('0.00'),
            'balance_due': Decimal('25.00'),
            'status': 'pending'
        }
    )

    # 12. Lab orders for active visits
    Order.objects.get_or_create(
        visit=v7, patient=p7, order_type='lab',
        order_description='Chest X-Ray AP/Lateral',
        defaults={'status': 'pending', 'ordering_provider': dr_nishant}
    )
    Order.objects.get_or_create(
        visit=v7, patient=p7, order_type='lab',
        order_description='Complete Blood Count (CBC)',
        defaults={'status': 'pending', 'ordering_provider': dr_nishant}
    )
    Order.objects.get_or_create(
        visit=v10, patient=p10, order_type='lab',
        order_description='Fasting Blood Glucose, HbA1c',
        defaults={'status': 'pending', 'ordering_provider': dr_nishant}
    )
    Order.objects.get_or_create(
        visit=v12, patient=p12, order_type='radiology',
        order_description='X-Ray Right Wrist AP/Lateral',
        defaults={'status': 'pending', 'ordering_provider': dr_nishant}
    )

    # 13. More stock items
    item_para, _ = Item.objects.get_or_create(code='ITEM-PARA', defaults={'name': 'Paracetamol 500mg', 'unit_of_measure': 'Pack of 100', 'category': cat_pharma, 'is_medication': True, 'medication': med_para, 'reorder_level': 30})
    item_saline, _ = Item.objects.get_or_create(code='ITEM-SAL', defaults={'name': 'Normal Saline 0.9% 500ml', 'unit_of_measure': 'Box of 20', 'category': cat_pharma, 'is_medication': True, 'medication': med_saline, 'reorder_level': 10})
    item_oxy, _ = Item.objects.get_or_create(code='ITEM-OXY', defaults={'name': 'Oxytocin 10 IU/ml', 'unit_of_measure': 'Box of 10 ampoules', 'category': cat_pharma, 'is_medication': True, 'medication': med_oxy, 'reorder_level': 5})

    Stock.objects.get_or_create(item=item_para, store=pharm_store, batch_lot_number='BATCH-2026-P1', defaults={'quantity_on_hand': Decimal('45.00'), 'expiry_date': date(2027, 3, 15), 'unit_cost': Decimal('2.00')})
    Stock.objects.get_or_create(item=item_saline, store=pharm_store, batch_lot_number='BATCH-2026-S1', defaults={'quantity_on_hand': Decimal('8.00'), 'expiry_date': date(2027, 12, 31), 'unit_cost': Decimal('3.00')})
    Stock.objects.get_or_create(item=item_oxy, store=pharm_store, batch_lot_number='BATCH-2026-O1', defaults={'quantity_on_hand': Decimal('15.00'), 'expiry_date': date(2027, 9, 30), 'unit_cost': Decimal('6.00')})

    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed()
