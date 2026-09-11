"""
Create Demo Users for Pilot Walkthrough — clean database with users, departments,
roles, permissions, wards, inventory, medications, and pricing. No patient/clinical data.
Usage: set JFD_DB=pilot && python manage.py migrate && python manage.py create_demo_users
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from decimal import Decimal
from datetime import date

from users_auth.models import Department, User, Role, Permission, UserRole, RolePermission


class Command(BaseCommand):
    help = 'Create demo users and seed infrastructure for pilot walkthrough (no patient data)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('PILOT WALKTHROUGH SETUP'))
        self.stdout.write(self.style.WARNING('Creates users + infrastructure only.'))
        self.stdout.write(self.style.WARNING('No patients, visits, or invoices.'))
        self.stdout.write(self.style.WARNING('=' * 60))

        # Step 1: Seed departments, roles, permissions, catalogues
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 1: Seeding departments, roles, permissions, catalogues...'))
        call_command('seed_data')

        # Step 2: Create demo users
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 2: Creating demo user accounts...'))
        self.create_demo_users()

        # Step 3: Create wards, rooms, beds
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 3: Creating wards, rooms, beds...'))
        self.create_ward_infrastructure()

        # Step 4: Create pricing
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 4: Creating price list and service prices...'))
        self.create_pricing()

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('PILOT WALKTHROUGH DATABASE READY'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.print_credentials()

    def create_demo_users(self):
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

            status = 'Created' if created else 'Updated'
            self.stdout.write(f'  {status}: {data["username"]} / {data.get("password", "pass123")} ({data["first_name"]} {data["last_name"]})')

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

    def print_credentials(self):
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
        self.stdout.write(self.style.HTTP_INFO('WALKTHROUGH NAVIGATION'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write('')
        self.stdout.write('  1. Register Patient:  /patients/register/')
        self.stdout.write('  2. Search Patients:   /patients/search/')
        self.stdout.write('  3. Triage Queue:      /clinical/triage/')
        self.stdout.write('  4. OPD Consultation:  /opd/')
        self.stdout.write('  5. ER Dashboard:      /clinical/emergency/')
        self.stdout.write('  6. IPD Management:    /clinical/ipd/')
        self.stdout.write('  7. OBGYN:             /clinical/obgyn/')
        self.stdout.write('  8. Surgery:           /clinical/surgery/')
        self.stdout.write('  9. Diagnostics:       /clinical/diagnostics/')
        self.stdout.write(' 10. Dispensing:        /pharmacy/dispensing/')
        self.stdout.write(' 11. Cashier:           /cashier/')
        self.stdout.write(' 12. Inventory:         /inventory/')
        self.stdout.write(' 13. Reports:           /reports/hmis/')
        self.stdout.write(' 14. Admin:             /admin/')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Database is clean. Follow TEST_WALKTHROUGH.md'))
        self.stdout.write(self.style.SUCCESS('to walk through the full patient journey.'))
