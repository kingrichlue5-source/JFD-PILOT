"""
Pilot Test Reset — Clears all non-user data, re-seeds catalogues, creates test users.
Usage: python manage.py pilot_reset
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from decimal import Decimal
from datetime import date, timedelta

from users_auth.models import Department, User, Role, Permission, UserRole, RolePermission


class Command(BaseCommand):
    help = 'Clear all non-user data and re-seed for pilot testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('PILOT TEST RESET'))
        self.stdout.write(self.style.WARNING('This will DELETE all clinical, billing, pharmacy,'))
        self.stdout.write(self.style.WARNING('inventory, and audit data.'))
        self.stdout.write(self.style.WARNING('Users and roles will be PRESERVED.'))
        self.stdout.write(self.style.WARNING('=' * 60))

        # Step 1: Clear non-user tables
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 1: Clearing non-user tables...'))
        self.clear_non_user_tables()

        # Step 2: Seed departments, roles, permissions, catalogues
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 2: Seeding departments, roles, permissions, catalogues...'))
        from django.core.management import call_command
        call_command('seed_data')

        # Step 3: Create test users for each role
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 3: Creating test user accounts...'))
        self.create_test_users()

        # Step 4: Create wards, rooms, beds
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 4: Creating wards, rooms, beds...'))
        self.create_ward_infrastructure()

        # Step 5: Create price list and service prices
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 5: Creating price list and service prices...'))
        self.create_pricing()

        # Step 6: Seed default triage criteria
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 6: Seeding default triage criteria...'))
        self.seed_triage_criteria()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('PILOT TEST DATABASE READY'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.print_login_credentials()

    def clear_non_user_tables(self):
        """Delete all data from non-user tables."""
        is_sqlite = connection.vendor == 'sqlite'

        if is_sqlite:
            with connection.cursor() as cursor:
                cursor.execute('PRAGMA foreign_keys = OFF')

        tables_to_clear = [
            # Clinical (actual db_table names from models)
            'appointments', 'referrals', 'surgical_cases',
            'postnatal_visits', 'birth_records', 'delivery_records',
            'labor_records', 'antenatal_visits',
            'specimens', 'patient_movements',
            'diagnostic_results', 'admission_transfers', 'admissions',
            'progress_notes', 'nursing_notes',
            'orders', 'diagnoses', 'vital_signs',
            'encounters', 'triage_records', 'visits',
            'beds', 'rooms', 'wards',
            'triage_criteria', 'workflow_transitions',
            'er_nurse_evaluations', 'pediatric_assessments',
            # Patients
            'patient_consents', 'patient_documents', 'patient_alerts', 'patient_allergies', 'patients',
            # Pharmacy
            'drug_interactions', 'medication_dispensing', 'prescription_items', 'prescriptions', 'medications',
            # Billing
            'refunds', 'credit_adjustments', 'payments', 'invoice_line_items', 'invoices',
            'service_prices', 'service_items', 'price_lists', 'cashier_shifts',
            # Inventory
            'stock_count_items', 'stock_counts', 'stock_movements', 'stock', 'items', 'stores', 'categories',
            # Audit
            'login_logs', 'audit_logs',
        ]

        with connection.cursor() as cursor:
            cleared = 0
            for table in tables_to_clear:
                try:
                    if is_sqlite:
                        cursor.execute(f'DELETE FROM "{table}"')
                    else:
                        cursor.execute(f'TRUNCATE TABLE "{table}" CASCADE')
                    count = cursor.rowcount
                    if count > 0:
                        self.stdout.write(f'  Cleared {count} rows from {table}')
                    cleared += 1
                except Exception:
                    pass

            if is_sqlite:
                cursor.execute('PRAGMA foreign_keys = ON')

        self.stdout.write(f'  Cleared {cleared} tables')

    def create_test_users(self):
        """Create user accounts for testing each role."""
        dept_opd = Department.objects.filter(code='OPD').first()
        dept_er = Department.objects.filter(code='ER').first()
        dept_obgyn = Department.objects.filter(code='OBGYN').first()
        dept_pharm = Department.objects.filter(code='PHARM').first()
        dept_lab = Department.objects.filter(code='LAB').first()
        dept_fin = Department.objects.filter(code='FIN').first()
        dept_surg = Department.objects.filter(code='SURG').first()
        dept_ipd = Department.objects.filter(code='IPD').first()
        dept_admin = Department.objects.filter(code='ADMIN').first()

        users_data = [
            {
                'username': 'admin',
                'password': 'admin123',
                'first_name': 'System',
                'last_name': 'Administrator',
                'email': 'admin@jfdhospital.gov.lr',
                'job_title': 'System Administrator',
                'department': dept_admin or dept_opd,
                'is_staff': True,
                'is_superuser': True,
                'role_code': 'ADMIN',
            },
            {
                'username': 'doctor',
                'password': 'doctor123',
                'first_name': 'Dr. James',
                'last_name': 'Togba',
                'email': 'doctor@jfdhospital.gov.lr',
                'job_title': 'Consultant Physician',
                'department': dept_opd,
                'role_code': 'DOCTOR',
            },
            {
                'username': 'nurse',
                'password': 'nurse123',
                'first_name': 'Martha',
                'last_name': 'Kpriah',
                'email': 'nurse@jfdhospital.gov.lr',
                'job_title': 'Registered Nurse',
                'department': dept_er or dept_opd,
                'role_code': 'NURSE',
            },
            {
                'username': 'triage',
                'password': 'triage123',
                'first_name': 'Ruth',
                'last_name': 'Weah',
                'email': 'triage@jfdhospital.gov.lr',
                'job_title': 'Triage Nurse',
                'department': dept_er,
                'role_code': 'TRIAGE_NURSE',
            },
            {
                'username': 'pharmacist',
                'password': 'pharm123',
                'first_name': 'Ibrahim',
                'last_name': 'Sesay',
                'email': 'pharmacist@jfdhospital.gov.lr',
                'job_title': 'Chief Pharmacist',
                'department': dept_pharm,
                'role_code': 'PHARMACIST',
            },
            {
                'username': 'cashier',
                'password': 'cash123',
                'first_name': 'Beatrice',
                'last_name': 'Mensah',
                'email': 'cashier@jfdhospital.gov.lr',
                'job_title': 'Senior Cashier',
                'department': dept_fin,
                'role_code': 'CASHIER',
            },
            {
                'username': 'labtech',
                'password': 'lab123',
                'first_name': 'Emmanuel',
                'last_name': 'Doe',
                'email': 'labtech@jfdhospital.gov.lr',
                'job_title': 'Laboratory Technician',
                'department': dept_lab,
                'role_code': 'LAB_TECH',
            },
            {
                'username': 'obgyn',
                'password': 'obgyn123',
                'first_name': 'Dr. Sarah',
                'last_name': 'Flomo',
                'email': 'obgyn@jfdhospital.gov.lr',
                'job_title': 'OBGYN Specialist',
                'department': dept_obgyn,
                'role_code': 'DOCTOR',
            },
            {
                'username': 'surgeon',
                'password': 'surg123',
                'first_name': 'Dr. Emmanuel',
                'last_name': 'Kromah',
                'email': 'surgeon@jfdhospital.gov.lr',
                'job_title': 'General Surgeon',
                'department': dept_surg,
                'role_code': 'DOCTOR',
            },
        ]

        for data in users_data:
            role_code = data.pop('role_code')
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults=data
            )
            user.set_password(data.get('password', 'pass123'))
            user.save()

            if created:
                self.stdout.write(f'  Created user: {data["username"]} ({data["first_name"]} {data["last_name"]})')
            else:
                self.stdout.write(f'  Updated user: {data["username"]}')

            # Assign role
            role = Role.objects.filter(code=role_code).first()
            if role:
                UserRole.objects.get_or_create(user=user, role=role)

    def create_ward_infrastructure(self):
        """Create wards, rooms, and beds for IPD/ER/OBGYN."""
        dept_ipd = Department.objects.filter(code='IPD').first()
        dept_er = Department.objects.filter(code='ER').first()
        dept_obgyn = Department.objects.filter(code='OBGYN').first()
        dept_surg = Department.objects.filter(code='SURG').first()

        from clinical.models import Ward, Room, Bed

        wards_data = [
            ('MED1', 'Medical Ward 1', dept_ipd, 'medical', 20),
            ('MED2', 'Medical Ward 2', dept_ipd, 'medical', 20),
            ('SURG1', 'Surgical Ward 1', dept_surg, 'surgical', 15),
            ('ER1', 'ER Resuscitation', dept_er, 'emergency', 10),
            ('MAT1', 'Maternity Ward', dept_obgyn, 'maternity', 15),
            ('ICU1', 'Intensive Care Unit', dept_ipd, 'critical', 8),
        ]

        for code, name, dept, ward_type, cap in wards_data:
            ward, created = Ward.objects.get_or_create(
                code=code,
                defaults={'name': name, 'department': dept, 'ward_type': ward_type, 'capacity': cap}
            )
            if created:
                self.stdout.write(f'  Created ward: {name}')

            for room_num in range(1, 3):
                room, _ = Room.objects.get_or_create(
                    ward=ward, room_number=f'{room_num:02d}',
                    defaults={'capacity': 3}
                )
                for bed_num in range(1, 4):
                    Bed.objects.get_or_create(
                        room=room, bed_number=f'Bed {room_num}{chr(64+bed_num)}',
                        defaults={'bed_type': 'standard'}
                    )

        self.stdout.write(f'  Created 6 wards with rooms and beds')

    def create_pricing(self):
        """Create price list with service prices."""
        from billing.models import PriceList, ServiceItem, ServicePrice

        price_list, _ = PriceList.objects.get_or_create(
            code='STD-2026',
            defaults={'name': 'Standard Hospital Tariffs 2026', 'is_default': True}
        )

        services = [
            ('CONS-OPD', 'OPD Consultation', 'Consultation', 25.00),
            ('CONS-ER', 'ER Consultation', 'Emergency', 50.00),
            ('CONS-SURG', 'Surgical Consultation', 'Surgery', 75.00),
            ('CONS-OBGYN', 'OBGYN Consultation', 'Consultation', 40.00),
            ('LAB-CBC', 'Complete Blood Count', 'Laboratory', 15.00),
            ('LAB-MAL', 'Malaria RDT', 'Laboratory', 8.00),
            ('LAB-GLU', 'Blood Glucose', 'Laboratory', 5.00),
            ('LAB-UA', 'Urinalysis', 'Laboratory', 10.00),
            ('RAD-CXR', 'Chest X-Ray', 'Radiology', 40.00),
            ('RAD-AXR', 'Abdominal X-Ray', 'Radiology', 35.00),
            ('RAD-US', 'Ultrasound', 'Radiology', 80.00),
            ('RAD-CT', 'CT Scan', 'Radiology', 150.00),
            ('BED-STD', 'Standard Bed (per day)', 'Bed', 30.00),
            ('BED-ICU', 'ICU Bed (per day)', 'Bed', 100.00),
            ('OP-GENERAL', 'General Surgery', 'Surgery', 200.00),
            ('OP-APPENDIX', 'Appendectomy', 'Surgery', 350.00),
            ('OP-CSECTION', 'Caesarean Section', 'Surgery', 400.00),
        ]

        for code, name, category, price in services:
            svc, _ = ServiceItem.objects.get_or_create(
                code=code, defaults={'name': name, 'category': category}
            )
            ServicePrice.objects.get_or_create(
                service_item=svc, price_list=price_list,
                effective_date=date(2026, 1, 1),
                defaults={'price': Decimal(str(price))}
            )

        self.stdout.write(f'  Created {len(services)} services with prices')

    def print_login_credentials(self):
        """Print login credentials and navigation guide."""
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('LOGIN CREDENTIALS'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write('')
        self.stdout.write('  USERNAME         PASSWORD      ROLE')
        self.stdout.write('  ---------------  -----------   -------------')
        self.stdout.write('  admin            admin123      Administrator (superuser)')
        self.stdout.write('  doctor           doctor123     Doctor / Consultant')
        self.stdout.write('  nurse            nurse123      Nurse')
        self.stdout.write('  triage           triage123     Triage Nurse')
        self.stdout.write('  pharmacist       pharm123      Pharmacist')
        self.stdout.write('  cashier          cash123       Cashier')
        self.stdout.write('  labtech          lab123        Lab Technician')
        self.stdout.write('  obgyn            obgyn123      OBGYN Specialist')
        self.stdout.write('  surgeon          surg123       General Surgeon')
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('PILOT TEST NAVIGATION'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write('')
        self.stdout.write('  1. Register Patient:  /patients/register/')
        self.stdout.write('  2. Search Patients:   /patients/search/')
        self.stdout.write('  3. Triage Queue:      /clinical/triage/')
        self.stdout.write('  4. OPD Consultation:  /opd/')
        self.stdout.write('  5. ER Dashboard:      /er/')
        self.stdout.write('  6. IPD Management:    /ipd/')
        self.stdout.write('  7. OBGYN:             /obgyn/')
        self.stdout.write('  8. Surgery:           /surgery/')
        self.stdout.write('  9. Pharmacy:          /pharmacy/')
        self.stdout.write(' 10. Dispensing:        /pharmacy/dispensing/')
        self.stdout.write(' 11. Cashier:           /cashier/')
        self.stdout.write(' 12. Inventory:         /inventory/')
        self.stdout.write(' 13. Reports:           /reports/hmis/')
        self.stdout.write(' 14. Admin:             /admin/')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Ready for pilot testing!'))

    def seed_triage_criteria(self):
        """Create default triage criteria rules for the algorithmic triage engine."""
        from clinical.models import TriageCriteria
        from decimal import Decimal

        default_criteria = [
            {
                'name': 'Severe Hypotension',
                'vital_sign': 'blood_pressure_systolic',
                'operator': 'lt',
                'threshold_low': Decimal('90'),
                'suggested_acuity': 2,
                'suggested_department': 'ER',
                'priority': 10,
            },
            {
                'name': 'Hypertensive Crisis',
                'vital_sign': 'blood_pressure_systolic',
                'operator': 'gt',
                'threshold_low': Decimal('180'),
                'suggested_acuity': 2,
                'suggested_department': 'ER',
                'priority': 11,
            },
            {
                'name': 'Severe Hypoxia',
                'vital_sign': 'oxygen_saturation',
                'operator': 'lt',
                'threshold_low': Decimal('90'),
                'suggested_acuity': 1,
                'suggested_department': 'ER',
                'priority': 5,
            },
            {
                'name': 'Mild Hypoxia',
                'vital_sign': 'oxygen_saturation',
                'operator': 'lt',
                'threshold_low': Decimal('94'),
                'suggested_acuity': 3,
                'suggested_department': 'ER',
                'priority': 15,
            },
            {
                'name': 'Severe Tachycardia',
                'vital_sign': 'heart_rate',
                'operator': 'gt',
                'threshold_low': Decimal('120'),
                'suggested_acuity': 3,
                'suggested_department': 'ER',
                'priority': 20,
            },
            {
                'name': 'Severe Bradycardia',
                'vital_sign': 'heart_rate',
                'operator': 'lt',
                'threshold_low': Decimal('50'),
                'suggested_acuity': 2,
                'suggested_department': 'ER',
                'priority': 21,
            },
            {
                'name': 'High Fever',
                'vital_sign': 'temperature',
                'operator': 'gt',
                'threshold_low': Decimal('40'),
                'suggested_acuity': 3,
                'suggested_department': 'OPD',
                'priority': 30,
            },
            {
                'name': 'Hypothermia',
                'vital_sign': 'temperature',
                'operator': 'lt',
                'threshold_low': Decimal('35'),
                'suggested_acuity': 2,
                'suggested_department': 'ER',
                'priority': 31,
            },
            {
                'name': 'Severe Tachypnea',
                'vital_sign': 'respiratory_rate',
                'operator': 'gt',
                'threshold_low': Decimal('30'),
                'suggested_acuity': 2,
                'suggested_department': 'ER',
                'priority': 40,
            },
            {
                'name': 'Hypoglycemia',
                'vital_sign': 'blood_glucose',
                'operator': 'lt',
                'threshold_low': Decimal('60'),
                'suggested_acuity': 2,
                'suggested_department': 'ER',
                'priority': 50,
            },
            {
                'name': 'Severe Hyperglycemia',
                'vital_sign': 'blood_glucose',
                'operator': 'gt',
                'threshold_low': Decimal('400'),
                'suggested_acuity': 2,
                'suggested_department': 'ER',
                'priority': 51,
            },
            {
                'name': 'Severe Pain',
                'vital_sign': 'pain_scale',
                'operator': 'gte',
                'threshold_low': Decimal('8'),
                'suggested_acuity': 3,
                'suggested_department': 'OPD',
                'priority': 60,
            },
        ]

        created_count = 0
        for criteria_data in default_criteria:
            _, created = TriageCriteria.objects.get_or_create(
                name=criteria_data['name'],
                defaults=criteria_data
            )
            if created:
                created_count += 1

        self.stdout.write(f'  Created {created_count} triage criteria rules')
