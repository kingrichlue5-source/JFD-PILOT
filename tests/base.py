"""
Base test infrastructure for JFD HMS tests.

Since all models use managed=False, Django's test runner won't create tables.
This base class creates necessary tables via schema_editor in setUp.
"""
import uuid
from decimal import Decimal
from datetime import date, timedelta

from django.test import TestCase, TransactionTestCase, override_settings
from django.db import connection
from rest_framework.test import APIClient


def create_all_tables():
    """Create all tables needed for tests using Django's schema editor."""
    from django.apps import apps

    with connection.schema_editor() as schema_editor:
        # Get all models that have managed=False but need tables for testing
        model_names = [
            'users_auth.Department',
            'users_auth.User',
            'users_auth.Role',
            'users_auth.Permission',
            'users_auth.UserRole',
            'users_auth.RolePermission',
            'users_auth.HospitalSetting',
            'patients.Patient',
            'patients.PatientAllergy',
            'patients.PatientAlert',
            'patients.PatientDocument',
            'patients.PatientConsent',
            'clinical.Ward',
            'clinical.Room',
            'clinical.Bed',
            'clinical.Visit',
            'clinical.TriageRecord',
            'clinical.Encounter',
            'clinical.VitalSigns',
            'clinical.Diagnosis',
            'clinical.Order',
            'clinical.ProgressNote',
            'clinical.NursingNote',
            'clinical.Admission',
            'clinical.AdmissionTransfer',
            'clinical.LabTestCatalogue',
            'clinical.RadiologyTestCatalogue',
            'clinical.DiagnosticResult',
            'clinical.PatientMovement',
            'pharmacy.Medication',
            'pharmacy.Prescription',
            'pharmacy.PrescriptionItem',
            'pharmacy.MedicationDispensing',
            'billing.PriceList',
            'billing.ServiceItem',
            'billing.ServicePrice',
            'billing.Invoice',
            'billing.InvoiceLineItem',
            'billing.Payment',
            'billing.Refund',
            'billing.CreditAdjustment',
            'billing.CashierShift',
            'inventory.Category',
            'inventory.Item',
            'inventory.Store',
            'inventory.Stock',
            'inventory.StockMovement',
            'inventory.StockCount',
            'inventory.StockCountItem',
            'audit.AuditLog',
            'audit.LoginLog',
            'pharmacy.DrugInteraction',
            'clinical.Specimen',
            'clinical.AntenatalVisit',
            'clinical.LaborRecord',
            'clinical.DeliveryRecord',
            'clinical.BirthRecord',
            'clinical.PostnatalVisit',
            'clinical.SurgicalCase',
            'clinical.Referral',
            'clinical.Appointment',
        ]

        for model_name in model_names:
            try:
                model = apps.get_model(model_name)
                schema_editor.create_model(model)
            except Exception:
                pass  # Table may already exist


def drop_all_tables():
    """Drop all test tables."""
    from django.apps import apps

    with connection.schema_editor() as schema_editor:
        model_names = [
            'clinical.Appointment',
            'clinical.Referral',
            'clinical.SurgicalCase',
            'clinical.PostnatalVisit',
            'clinical.BirthRecord',
            'clinical.DeliveryRecord',
            'clinical.LaborRecord',
            'clinical.AntenatalVisit',
            'clinical.Specimen',
            'pharmacy.DrugInteraction',
            'audit.LoginLog',
            'audit.AuditLog',
            'inventory.StockCountItem',
            'inventory.StockCount',
            'inventory.StockMovement',
            'inventory.Stock',
            'inventory.Item',
            'inventory.Store',
            'inventory.Category',
            'billing.CashierShift',
            'billing.CreditAdjustment',
            'billing.Refund',
            'billing.Payment',
            'billing.InvoiceLineItem',
            'billing.Invoice',
            'billing.ServicePrice',
            'billing.ServiceItem',
            'billing.PriceList',
            'pharmacy.MedicationDispensing',
            'pharmacy.PrescriptionItem',
            'pharmacy.Prescription',
            'pharmacy.Medication',
            'clinical.PatientMovement',
            'clinical.DiagnosticResult',
            'clinical.RadiologyTestCatalogue',
            'clinical.LabTestCatalogue',
            'clinical.AdmissionTransfer',
            'clinical.Admission',
            'clinical.NursingNote',
            'clinical.ProgressNote',
            'clinical.Order',
            'clinical.Diagnosis',
            'clinical.VitalSigns',
            'clinical.Encounter',
            'clinical.TriageRecord',
            'clinical.Visit',
            'clinical.Bed',
            'clinical.Room',
            'clinical.Ward',
            'patients.PatientConsent',
            'patients.PatientDocument',
            'patients.PatientAlert',
            'patients.PatientAllergy',
            'patients.Patient',
            'users_auth.RolePermission',
            'users_auth.UserRole',
            'users_auth.HospitalSetting',
            'users_auth.Permission',
            'users_auth.Role',
            'users_auth.User',
            'users_auth.Department',
        ]

        for model_name in model_names:
            try:
                model = apps.get_model(model_name)
                schema_editor.delete_model(model)
            except Exception:
                pass


class BaseTestCase(TransactionTestCase):
    """Base test case for JFD HMS tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.client = APIClient()
        self._setup_seed_data()
        self.client.force_authenticate(user=self.user_doctor)

    def _setup_seed_data(self):
        """Create minimal seed data needed for tests."""
        from users_auth.models import Department, Role, Permission, UserRole
        from billing.models import PriceList, ServiceItem, ServicePrice
        from inventory.models import Category, Item, Store, Stock
        from pharmacy.models import Medication

        # Departments
        self.dept_opd, _ = Department.objects.get_or_create(
            code='OPD', defaults={'name': 'Outpatient Department', 'is_clinical': True}
        )
        self.dept_er, _ = Department.objects.get_or_create(
            code='ER', defaults={'name': 'Emergency Room', 'is_clinical': True}
        )
        self.dept_obgyn, _ = Department.objects.get_or_create(
            code='OBGYN', defaults={'name': 'Obstetrics & Gynecology', 'is_clinical': True}
        )
        self.dept_pharmacy, _ = Department.objects.get_or_create(
            code='PHARM', defaults={'name': 'Pharmacy', 'is_clinical': True}
        )
        self.dept_lab, _ = Department.objects.get_or_create(
            code='LAB', defaults={'name': 'Laboratory', 'is_clinical': True}
        )

        # Roles
        self.role_pharmacist, _ = Role.objects.get_or_create(
            code='PHARMACIST', defaults={'name': 'Pharmacist'}
        )
        self.role_doctor, _ = Role.objects.get_or_create(
            code='DOCTOR', defaults={'name': 'Doctor'}
        )
        self.role_admin, _ = Role.objects.get_or_create(
            code='ADMIN', defaults={'name': 'Administrator'}
        )
        self.role_cashier, _ = Role.objects.get_or_create(
            code='CASHIER', defaults={'name': 'Cashier'}
        )

        # Users
        from users_auth.models import User
        self.user_doctor, _ = User.objects.get_or_create(
            username='testdoctor',
            defaults={
                'email': 'doctor@jfd.test',
                'first_name': 'Test',
                'last_name': 'Doctor',
                'department': self.dept_opd,
            }
        )
        self.user_doctor.set_password('testpass123')
        self.user_doctor.save()

        self.user_pharmacist, _ = User.objects.get_or_create(
            username='testpharmacist',
            defaults={
                'email': 'pharmacist@jfd.test',
                'first_name': 'Test',
                'last_name': 'Pharmacist',
                'department': self.dept_pharmacy,
            }
        )
        self.user_pharmacist.set_password('testpass123')
        self.user_pharmacist.save()

        self.user_cashier, _ = User.objects.get_or_create(
            username='testcashier',
            defaults={
                'email': 'cashier@jfd.test',
                'first_name': 'Test',
                'last_name': 'Cashier',
            }
        )
        self.user_cashier.set_password('testpass123')
        self.user_cashier.save()

        # User roles
        UserRole.objects.get_or_create(user=self.user_doctor, role=self.role_doctor)
        UserRole.objects.get_or_create(user=self.user_pharmacist, role=self.role_pharmacist)
        UserRole.objects.get_or_create(user=self.user_cashier, role=self.role_cashier)

        # Permissions (needed for RBAC)
        from users_auth.models import Permission, RolePermission
        perms_data = [
            ('PATIENT_VIEW', 'Patient', 'View Patients'),
            ('PATIENT_CREATE', 'Patient', 'Create Patients'),
            ('PATIENT_EDIT', 'Patient', 'Edit Patients'),
            ('PATIENT_MERGE', 'Patient', 'Merge Patients'),
            ('ENCOUNTER_VIEW', 'Clinical', 'View Encounters'),
            ('ENCOUNTER_CREATE', 'Clinical', 'Create Encounters'),
            ('ENCOUNTER_EDIT', 'Clinical', 'Edit Encounters'),
            ('ENCOUNTER_SIGN', 'Clinical', 'Sign Encounters'),
            ('TRIAGE_PERFORM', 'Clinical', 'Perform Triage'),
            ('ORDER_VIEW', 'Orders', 'View Orders'),
            ('ORDER_CREATE', 'Orders', 'Create Orders'),
            ('ORDER_CANCEL', 'Orders', 'Cancel Orders'),
            ('RX_VIEW', 'Pharmacy', 'View Prescriptions'),
            ('RX_CREATE', 'Pharmacy', 'Create Prescriptions'),
            ('RX_DISPENSE', 'Pharmacy', 'Dispense Medications'),
            ('INVOICE_VIEW', 'Billing', 'View Invoices'),
            ('INVOICE_CREATE', 'Billing', 'Create Invoices'),
            ('PAYMENT_PROCESS', 'Billing', 'Process Payments'),
            ('REFUND_ISSUE', 'Billing', 'Issue Refunds'),
            ('TRANSACTION_VOID', 'Billing', 'Void Transactions'),
            ('INVENTORY_VIEW', 'Inventory', 'View Inventory'),
            ('INVENTORY_MANAGE', 'Inventory', 'Manage Inventory'),
            ('STOCK_MOVE', 'Inventory', 'Process Stock Movements'),
            ('REPORT_VIEW', 'Reports', 'View Reports'),
            ('REPORT_GENERATE', 'Reports', 'Generate Reports'),
            ('REPORT_EXPORT', 'Reports', 'Export Reports'),
            ('USER_MANAGE', 'Admin', 'Manage Users'),
            ('ROLE_MANAGE', 'Admin', 'Manage Roles'),
            ('AUDIT_VIEW', 'Admin', 'View Audit Logs'),
            ('SYS_CONFIG', 'Admin', 'System Configuration'),
        ]
        self.all_permissions = {}
        for code, cat, name in perms_data:
            perm, _ = Permission.objects.get_or_create(
                code=code, defaults={'name': name, 'category': cat}
            )
            self.all_permissions[code] = perm

        # Assign all permissions to admin and doctor roles
        for role in [self.role_admin, self.role_doctor]:
            for perm in Permission.objects.all():
                RolePermission.objects.get_or_create(role=role, permission=perm)

        # Assign pharmacy permissions to pharmacist
        for code in ['PATIENT_VIEW', 'RX_VIEW', 'RX_CREATE', 'RX_DISPENSE', 'INVENTORY_VIEW', 'INVENTORY_MANAGE']:
            if code in self.all_permissions:
                RolePermission.objects.get_or_create(
                    role=self.role_pharmacist, permission=self.all_permissions[code]
                )

        # Assign billing permissions to cashier
        for code in ['PATIENT_VIEW', 'INVOICE_VIEW', 'INVOICE_CREATE', 'PAYMENT_PROCESS', 'REFUND_ISSUE']:
            if code in self.all_permissions:
                RolePermission.objects.get_or_create(
                    role=self.role_cashier, permission=self.all_permissions[code]
                )

        # Price list
        self.price_list, _ = PriceList.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Default Price List', 'is_default': True}
        )

        # Service items
        self.svc_consult, _ = ServiceItem.objects.get_or_create(
            code='CONSULT',
            defaults={'name': 'Consultation Fee', 'category': 'Clinical', 'is_billable': True}
        )
        self.svc_lab, _ = ServiceItem.objects.get_or_create(
            code='LAB_TEST',
            defaults={'name': 'Laboratory Test', 'category': 'Laboratory', 'is_billable': True}
        )
        self.svc_rad, _ = ServiceItem.objects.get_or_create(
            code='RAD_TEST',
            defaults={'name': 'Radiology Test', 'category': 'Radiology', 'is_billable': True}
        )
        self.svc_pharm, _ = ServiceItem.objects.get_or_create(
            code='PHARM',
            defaults={'name': 'Pharmacy Service', 'category': 'Pharmacy', 'is_billable': True}
        )

        # Service prices (self_pay)
        today = date.today()
        for svc in [self.svc_consult, self.svc_lab, self.svc_rad, self.svc_pharm]:
            ServicePrice.objects.get_or_create(
                service_item=svc,
                price_list=self.price_list,
                payer_category='self_pay',
                effective_date=today,
                defaults={'price': Decimal('500.00')}
            )

        # Medications
        self.med_paracetamol, _ = Medication.objects.get_or_create(
            name='Paracetamol',
            defaults={
                'generic_name': 'Acetaminophen',
                'medication_code': 'PARA500',
                'category': 'Analgesic',
                'dosage_form': 'Tablet',
                'strength': '500mg',
                'unit': 'tablet',
            }
        )
        self.med_amoxicillin, _ = Medication.objects.get_or_create(
            name='Amoxicillin',
            defaults={
                'generic_name': 'Amoxicillin',
                'medication_code': 'AMOX250',
                'category': 'Antibiotic',
                'dosage_form': 'Capsule',
                'strength': '250mg',
                'unit': 'capsule',
            }
        )

        # Pharmacy service items for medications
        self.svc_pharm_para, _ = ServiceItem.objects.get_or_create(
            code='PHARM_PARA500',
            defaults={'name': 'Paracetamol 500mg', 'category': 'Pharmacy', 'is_billable': True}
        )
        self.svc_pharm_amox, _ = ServiceItem.objects.get_or_create(
            code='PHARM_AMOX250',
            defaults={'name': 'Amoxicillin 250mg', 'category': 'Pharmacy', 'is_billable': True}
        )

        # Service prices for specific pharmacy items
        for svc in [self.svc_pharm_para, self.svc_pharm_amox]:
            ServicePrice.objects.get_or_create(
                service_item=svc,
                price_list=self.price_list,
                payer_category='self_pay',
                effective_date=today,
                defaults={'price': Decimal('500.00')}
            )

        # Inventory
        self.store_main, _ = Store.objects.get_or_create(
            code='PHARM_MAIN',
            defaults={'name': 'Main Pharmacy', 'store_type': 'pharmacy'}
        )
        self.store_ward, _ = Store.objects.get_or_create(
            code='PHARM_WARD',
            defaults={'name': 'Ward Pharmacy', 'store_type': 'pharmacy'}
        )

        cat_pharm, _ = Category.objects.get_or_create(
            code='PHARM_CAT', defaults={'name': 'Pharmaceuticals'}
        )

        self.item_paracetamol, _ = Item.objects.get_or_create(
            code='ITEM_PARA500',
            defaults={
                'name': 'Paracetamol 500mg Tablet',
                'category': cat_pharm,
                'unit_of_measure': 'tablet',
                'is_medication': True,
                'medication': self.med_paracetamol,
                'reorder_level': 100,
            }
        )
        self.item_amoxicillin, _ = Item.objects.get_or_create(
            code='ITEM_AMOX250',
            defaults={
                'name': 'Amoxicillin 250mg Capsule',
                'category': cat_pharm,
                'unit_of_measure': 'capsule',
                'is_medication': True,
                'medication': self.med_amoxicillin,
                'reorder_level': 50,
            }
        )

        # Stock
        self.stock_paracetamol, _ = Stock.objects.get_or_create(
            item=self.item_paracetamol,
            store=self.store_main,
            batch_lot_number='BATCH-001',
            defaults={
                'quantity_on_hand': Decimal('1000'),
                'expiry_date': today + timedelta(days=365),
                'unit_cost': Decimal('0.50'),
            }
        )
        self.stock_amoxicillin, _ = Stock.objects.get_or_create(
            item=self.item_amoxicillin,
            store=self.store_main,
            batch_lot_number='BATCH-002',
            defaults={
                'quantity_on_hand': Decimal('500'),
                'expiry_date': today + timedelta(days=365),
                'unit_cost': Decimal('1.00'),
            }
        )

    def _create_patient(self, **kwargs):
        """Create a test patient with auto-generated MRN."""
        from patients.models import Patient
        mrn = f"JFD-2026-{str(uuid.uuid4().int)[:5].zfill(5)}"
        defaults = {
            'mrn': mrn,
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': date(1990, 1, 15),
            'gender': 'M',
            'phone': '+231-77-000-0001',
            'payer_category': 'self_pay',
        }
        defaults.update(kwargs)
        return Patient.objects.create(**defaults)

    def _create_visit(self, patient, **kwargs):
        """Create a test visit with auto-generated visit_number."""
        from clinical.models import Visit
        visit_number = f"VIS-{str(uuid.uuid4().int)[:5].zfill(5)}"
        defaults = {
            'patient': patient,
            'visit_number': visit_number,
            'visit_type': 'opd',
            'status': 'checked_in',
            'chief_complaint': 'Headache and fever',
        }
        defaults.update(kwargs)
        return Visit.objects.create(**defaults)

    def _create_invoice(self, patient, visit, **kwargs):
        """Create a test invoice."""
        from billing.models import Invoice
        from billing.services import generate_invoice_number
        defaults = {
            'invoice_number': generate_invoice_number(),
            'patient': patient,
            'visit': visit,
            'payer_type': 'self_pay',
            'status': 'pending',
        }
        defaults.update(kwargs)
        return Invoice.objects.create(**defaults)
