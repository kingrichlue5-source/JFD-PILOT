"""
Seed hospital settings and the standard test accounts on the active database.

Intended for the live (Railway) database, run from the service shell:

    python manage.py setup_test_users

Steps:
  1. Seed hospital settings (branding, contact details, registration fee, follow-up window)
     and download the hospital logo from jfdhospital.com into the default storage
  2. Seed reference data — departments, roles, permissions, lab/radiology catalogues,
     medications, service prices, inventory stores (existing `seed_data` via `create_demo_users`),
     plus wards/rooms/beds and the standard price list
  3. Create or refresh the ten test accounts and their role assignments

Idempotent: re-running updates the same rows and resets the test passwords.
Nothing is deleted — no patient, visit, invoice, or stock data is touched.
"""
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import IntegrityError

from users_auth.models import Department, HospitalSetting, Role, User, UserRole


# username -> login credentials, profile and role assignment for the test accounts
TEST_USERS = [
    {
        'username': 'admin', 'password': 'admin123',
        'first_name': 'System', 'last_name': 'Administrator',
        'job_title': 'Administrator', 'department': 'ADMIN',
        'roles': ['ADMIN'], 'is_staff': True, 'is_superuser': True,
    },
    {
        'username': 'doctor', 'password': 'doctor123',
        'first_name': 'Dr. James', 'last_name': 'Togba',
        'job_title': 'Consultant Physician', 'department': 'OPD',
        'roles': ['DOCTOR'],
    },
    {
        'username': 'triage', 'password': 'triage123',
        'first_name': 'Ruth', 'last_name': 'Weah',
        'job_title': 'Triage Nurse', 'department': 'ER',
        'roles': ['TRIAGE_NURSE'],
    },
    {
        'username': 'pharmacist', 'password': 'pharm123',
        'first_name': 'Ibrahim', 'last_name': 'Sesay',
        'job_title': 'Chief Pharmacist', 'department': 'PHARM',
        'roles': ['PHARMACIST'],
    },
    {
        'username': 'cashier', 'password': 'cash123',
        'first_name': 'Beatrice', 'last_name': 'Mensah',
        'job_title': 'Senior Cashier', 'department': 'FIN',
        'roles': ['CASHIER'],
    },
    {
        'username': 'labtech', 'password': 'lab123',
        'first_name': 'Emmanuel', 'last_name': 'Doe',
        'job_title': 'Laboratory Technician', 'department': 'LAB',
        'roles': ['LAB_TECH'],
    },
    {
        'username': 'nurse', 'password': 'nurse123',
        'first_name': 'Martha', 'last_name': 'Kpriah',
        'job_title': 'Registered Nurse', 'department': 'ER',
        'roles': ['NURSE'],
    },
    {
        'username': 'obgyn', 'password': 'obgyn123',
        'first_name': 'Dr. Sarah', 'last_name': 'Flomo',
        'job_title': 'OBGYN Specialist', 'department': 'OBGYN',
        'roles': ['DOCTOR'],
    },
    {
        'username': 'surgeon', 'password': 'surg123',
        'first_name': 'Dr. Emmanuel', 'last_name': 'Kromah',
        'job_title': 'General Surgeon', 'department': 'SURG',
        'roles': ['DOCTOR'],
    },
    {
        'username': 'inventory', 'password': 'inv123',
        'first_name': 'Joseph', 'last_name': 'Mensah',
        'job_title': 'Inventory Manager', 'department': 'PHARM',
        'roles': ['INV_MGR'],
    },
]

# Contact details used to fill any blank field (never overwrites a value already entered)
HOSPITAL_CONTACT = {
    'phone': 'Local: +231 778-932-543 Mobile: +231 888-150-385',
    'email': 'info@jfdhospital.com',
    'address': 'Tappita Nimba, Liberia',
    'website': 'https://jfdhospital.com/',
}

# Hospital logo published on the official website (uploaded to default storage: Cloudinary in production)
LOGO_URL = 'https://jfdhospital.com/wp-content/uploads/2025/04/JFD-Original_logo.png'
LOGO_FILENAME = 'jfd-logo.png'


class Command(BaseCommand):
    help = 'Seed hospital settings and the ten test accounts (idempotent, resets test passwords)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true', dest='dry_run',
            help='Report what would change without writing to the database',
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']

        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('TEST ENVIRONMENT SETUP' + (' (DRY RUN)' if self.dry_run else '')))
        self.stdout.write(self.style.WARNING('Settings + reference data + 10 test accounts'))
        self.stdout.write(self.style.WARNING('=' * 60))

        # Step 1: hospital settings
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 1: Hospital settings...'))
        setting = self.seed_settings()
        self.seed_logo(setting)

        # Step 2: reference data, demo users, wards/beds, pricing
        if self.dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('Step 2: Reference data (skipped in dry run)'))
            self.stdout.write('  Would run: seed_data + create_demo_users + add_inventory_user')
        else:
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO('Step 2: Departments, roles, permissions, catalogues, wards, pricing...'))
            call_command('create_demo_users')
            call_command('add_inventory_user')

        # Step 3: the ten test accounts
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Step 3: Test accounts...'))
        self.sync_users()

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Hospital settings'))
        self.stdout.write(f'  Name:              {setting.hospital_name}')
        self.stdout.write(f'  Short name:        {setting.short_name}')
        self.stdout.write(f'  Registration fee:  ${setting.registration_fee}')
        self.stdout.write(f'  Follow-up window:  {setting.followup_window_days} days')
        self.stdout.write(f'  Phone:             {setting.phone or "(not set)"}')
        self.stdout.write(f'  Email:             {setting.email or "(not set)"}')
        self.stdout.write(f'  Address:           {setting.address or "(not set — add at /admin/settings/)"}')
        self.stdout.write(f'  Logo:              {setting.logo.url if setting.logo else "(not set)"}')

        self.print_credentials()

    # ------------------------------------------------------------------ settings
    def seed_settings(self):
        """Create or patch the singleton HospitalSetting row. Never wipes entered values."""
        setting = HospitalSetting.get_settings()

        if self.dry_run:
            self.stdout.write(f'  Existing row: {setting.hospital_name}')
            return setting

        changed = []
        if not setting.tagline:
            setting.tagline = 'Hospital Management Information System'
            changed.append('tagline')
        for field, value in HOSPITAL_CONTACT.items():
            if not getattr(setting, field):
                setattr(setting, field, value)
                changed.append(field)
        if setting.registration_fee is None:
            setting.registration_fee = Decimal('5.00')
            changed.append('registration_fee')
        if not setting.followup_window_days:
            setting.followup_window_days = 30
            changed.append('followup_window_days')

        setting.updated_by = 'setup_test_users'
        setting.save()

        if changed:
            self.stdout.write(self.style.SUCCESS(f'  Updated: {", ".join(changed)}'))
        else:
            self.stdout.write('  Settings already populated — left unchanged')
        return setting

    def seed_logo(self, setting):
        """Download the hospital logo from the official site and store it via the default storage."""
        if setting.logo:
            self.stdout.write(f'  Logo already set: {setting.logo.name}')
            return
        if self.dry_run:
            self.stdout.write(f'  Would download logo: {LOGO_URL}')
            return
        try:
            import requests
            from django.core.files.base import ContentFile

            response = requests.get(LOGO_URL, timeout=30)
            response.raise_for_status()
            setting.logo.save(LOGO_FILENAME, ContentFile(response.content), save=True)
            self.stdout.write(self.style.SUCCESS(f'  Logo uploaded: {setting.logo.url}'))
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f'  Logo skipped ({exc}) — set it later at /admin/settings/'))

    # ------------------------------------------------------------------- accounts
    def sync_users(self):
        """Create/refresh the test accounts, reset passwords and make sure roles are assigned."""
        for data in TEST_USERS:
            user = User.objects.filter(username=data['username']).first()
            created = user is None

            if created:
                email = f"{data['username']}@jfdhospital.gov.lr"
                if User.objects.filter(email=email).exists():
                    email = f"{data['username']}.test@jfdhospital.gov.lr"
                user = User(
                    username=data['username'],
                    email=email,
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                )

            if self.dry_run:
                label = 'would create' if created else 'would update'
                self.stdout.write(f'  {label}: {data["username"]} / {data["password"]}')
                continue

            try:
                user.first_name = data['first_name']
                user.last_name = data['last_name']
                user.job_title = data['job_title']
                user.status = 'active'
                user.is_active = True
                user.failed_login_attempts = 0
                user.locked_until = None
                user.is_staff = data.get('is_staff', user.is_staff)
                user.is_superuser = data.get('is_superuser', user.is_superuser)
                user.set_password(data['password'])

                department = Department.objects.filter(code=data['department']).first()
                if department:
                    user.department = department

                user.save()
            except IntegrityError as exc:
                self.stdout.write(self.style.ERROR(f'  FAILED: {data["username"]} ({exc})'))
                continue

            self.stdout.write(
                self.style.SUCCESS(
                    f'  {"Created" if created else "Updated"}: {data["username"]} / {data["password"]}'
                )
            )

            for role_code in data['roles']:
                role = Role.objects.filter(code=role_code).first()
                if role:
                    UserRole.objects.get_or_create(user=user, role=role)
                    self.stdout.write(f'      role -> {role_code}')
                else:
                    self.stdout.write(self.style.WARNING(
                        f'      role {role_code} not found — run seed_data first'
                    ))

    # ------------------------------------------------------------------- reporting
    def print_credentials(self):
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('TEST LOGIN CREDENTIALS'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write('')
        self.stdout.write('  USERNAME         PASSWORD       ROLE / TITLE')
        self.stdout.write('  ---------------  ------------   ---------------------------')
        for data in TEST_USERS:
            role_label = data['roles'][0]
            self.stdout.write(
                f'  {data["username"]:<15}  {data["password"]:<12}   {role_label} — {data["job_title"]}'
            )
        self.stdout.write('')
        self.stdout.write('  Contact details are seeded from the pilot settings — edit at /admin/settings/')
        self.stdout.write(self.style.SUCCESS('=' * 60))
