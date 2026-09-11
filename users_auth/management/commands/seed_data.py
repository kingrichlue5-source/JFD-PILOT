from django.core.management.base import BaseCommand
from users_auth.models import Department, Role, Permission, RolePermission
from clinical.models import LabTestCatalogue, RadiologyTestCatalogue
from pharmacy.models import Medication
from billing.models import ServiceItem, ServicePrice, PriceList
from inventory.models import Category, Item as InventoryItem, Store, Stock


class Command(BaseCommand):
    help = 'Seed departments, roles, permissions, and catalogues for JFD Hospital'

    def handle(self, *args, **options):
        self.stdout.write('Seeding departments...')
        departments = self.seed_departments()

        self.stdout.write('Seeding roles...')
        roles = self.seed_roles()

        self.stdout.write('Seeding permissions...')
        permissions = self.seed_permissions()

        self.stdout.write('Assigning permissions to roles...')
        self.assign_permissions(roles, permissions)

        self.stdout.write('Seeding lab test catalogue...')
        self.seed_lab_tests()

        self.stdout.write('Seeding radiology test catalogue...')
        self.seed_radiology_tests()

        self.stdout.write('Seeding medications...')
        self.seed_medications()

        self.stdout.write('Seeding service items and prices...')
        self.seed_service_items()

        self.stdout.write('Seeding inventory stores and stock...')
        self.seed_inventory()

        self.stdout.write('Seeding drug interactions...')
        self.seed_drug_interactions()

        self.stdout.write(self.style.SUCCESS('Successfully seeded database!'))

    def seed_departments(self):
        departments_data = [
            {'name': 'Emergency Room', 'code': 'ER', 'is_clinical': True, 'ward_type': 'emergency'},
            {'name': 'Outpatient Department', 'code': 'OPD', 'is_clinical': True, 'ward_type': 'outpatient'},
            {'name': 'Inpatient Department', 'code': 'IPD', 'is_clinical': True, 'ward_type': 'inpatient'},
            {'name': 'Obstetrics & Gynecology', 'code': 'OBGYN', 'is_clinical': True, 'ward_type': 'specialty'},
            {'name': 'Pediatrics', 'code': 'PEDS', 'is_clinical': True, 'ward_type': 'specialty'},
            {'name': 'Surgery', 'code': 'SURG', 'is_clinical': True, 'ward_type': 'specialty'},
            {'name': 'Internal Medicine', 'code': 'IM', 'is_clinical': True, 'ward_type': 'specialty'},
            {'name': 'Laboratory', 'code': 'LAB', 'is_clinical': True, 'ward_type': 'diagnostic'},
            {'name': 'Radiology', 'code': 'RAD', 'is_clinical': True, 'ward_type': 'diagnostic'},
            {'name': 'Pharmacy', 'code': 'PHARM', 'is_clinical': True, 'ward_type': 'pharmacy'},
            {'name': 'Nursing Services', 'code': 'NURSE', 'is_clinical': True, 'ward_type': 'nursing'},
            {'name': 'Medical Records', 'code': 'MRO', 'is_clinical': False, 'ward_type': 'admin'},
            {'name': 'Finance', 'code': 'FIN', 'is_clinical': False, 'ward_type': 'admin'},
            {'name': 'Human Resources', 'code': 'HR', 'is_clinical': False, 'ward_type': 'admin'},
            {'name': 'ICT', 'code': 'ICT', 'is_clinical': False, 'ward_type': 'admin'},
            {'name': 'Procurement', 'code': 'PROC', 'is_clinical': False, 'ward_type': 'admin'},
            {'name': 'Administration', 'code': 'ADMIN', 'is_clinical': False, 'ward_type': 'admin'},
            {'name': 'Intensive Care Unit', 'code': 'ICU', 'is_clinical': True, 'ward_type': 'critical'},
            {'name': 'Theatre', 'code': 'THEATRE', 'is_clinical': True, 'ward_type': 'surgical'},
            {'name': 'Maternity Ward', 'code': 'MAT', 'is_clinical': True, 'ward_type': 'maternity'},
        ]

        departments = {}
        for data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'is_clinical': data['is_clinical'],
                    'is_active': True,
                    'sync_status': 'synced'
                }
            )
            departments[data['code']] = dept
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  {data["code"]}: {data["name"]} [{status}]')

        return departments

    def seed_roles(self):
        roles_data = [
            {'name': 'Administrator', 'code': 'ADMIN', 'description': 'Full system administrator access', 'is_system_role': True},
            {'name': 'Medical Director', 'code': 'MED_DIRECTOR', 'description': 'Medical director with full clinical access', 'is_system_role': True},
            {'name': 'Doctor', 'code': 'DOCTOR', 'description': 'Physician with clinical documentation access', 'is_system_role': True},
            {'name': 'Nurse', 'code': 'NURSE', 'description': 'Nursing staff with patient care access', 'is_system_role': True},
            {'name': 'Triage Nurse', 'code': 'TRIAGE_NURSE', 'description': 'Triage nurse with triage-specific access', 'is_system_role': True},
            {'name': 'Pharmacist', 'code': 'PHARMACIST', 'description': 'Pharmacy staff with medication management access', 'is_system_role': True},
            {'name': 'Laboratory Technician', 'code': 'LAB_TECH', 'description': 'Laboratory staff with diagnostic access', 'is_system_role': True},
            {'name': 'Radiologist', 'code': 'RADIOLOGIST', 'description': 'Radiology staff with imaging access', 'is_system_role': True},
            {'name': 'Cashier', 'code': 'CASHIER', 'description': 'Billing and payment processing access', 'is_system_role': True},
            {'name': 'Medical Records Officer', 'code': 'MRO', 'description': 'Medical records and HMIS reporting access', 'is_system_role': True},
            {'name': 'Inventory Manager', 'code': 'INV_MGR', 'description': 'Inventory and supply chain management access', 'is_system_role': True},
            {'name': 'Nurse Manager', 'code': 'NURSE_MGR', 'description': 'Nursing management with supervisory access', 'is_system_role': True},
            {'name': 'Finance Officer', 'code': 'FIN_OFF', 'description': 'Financial oversight and reporting access', 'is_system_role': True},
            {'name': 'Internal Auditor', 'code': 'INT_AUDIT', 'description': 'Audit and compliance access', 'is_system_role': True},
            {'name': 'System Administrator', 'code': 'SYS_ADMIN', 'description': 'Technical system administration access', 'is_system_role': True},
        ]

        roles = {}
        for data in roles_data:
            role, created = Role.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'is_system_role': data['is_system_role'],
                    'is_active': True,
                    'sync_status': 'synced'
                }
            )
            roles[data['code']] = role
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  {data["code"]}: {data["name"]} [{status}]')

        return roles

    def seed_permissions(self):
        permissions_data = [
            {'name': 'View Patients', 'code': 'PATIENT_VIEW', 'description': 'View patient records', 'category': 'Patient'},
            {'name': 'Create Patients', 'code': 'PATIENT_CREATE', 'description': 'Create new patient records', 'category': 'Patient'},
            {'name': 'Edit Patients', 'code': 'PATIENT_EDIT', 'description': 'Edit patient information', 'category': 'Patient'},
            {'name': 'Merge Patients', 'code': 'PATIENT_MERGE', 'description': 'Merge duplicate patient records', 'category': 'Patient'},
            {'name': 'View Encounters', 'code': 'ENCOUNTER_VIEW', 'description': 'View clinical encounters', 'category': 'Clinical'},
            {'name': 'Create Encounters', 'code': 'ENCOUNTER_CREATE', 'description': 'Create clinical encounters', 'category': 'Clinical'},
            {'name': 'Edit Encounters', 'code': 'ENCOUNTER_EDIT', 'description': 'Edit clinical encounters', 'category': 'Clinical'},
            {'name': 'Sign Encounters', 'code': 'ENCOUNTER_SIGN', 'description': 'Sign and finalize encounters', 'category': 'Clinical'},
            {'name': 'View Orders', 'code': 'ORDER_VIEW', 'description': 'View clinical orders', 'category': 'Orders'},
            {'name': 'Create Orders', 'code': 'ORDER_CREATE', 'description': 'Create clinical orders', 'category': 'Orders'},
            {'name': 'Cancel Orders', 'code': 'ORDER_CANCEL', 'description': 'Cancel clinical orders', 'category': 'Orders'},
            {'name': 'View Prescriptions', 'code': 'RX_VIEW', 'description': 'View prescriptions', 'category': 'Pharmacy'},
            {'name': 'Create Prescriptions', 'code': 'RX_CREATE', 'description': 'Create prescriptions', 'category': 'Pharmacy'},
            {'name': 'Dispense Medications', 'code': 'RX_DISPENSE', 'description': 'Dispense medications', 'category': 'Pharmacy'},
            {'name': 'View Invoices', 'code': 'INVOICE_VIEW', 'description': 'View invoices', 'category': 'Billing'},
            {'name': 'Create Invoices', 'code': 'INVOICE_CREATE', 'description': 'Create invoices', 'category': 'Billing'},
            {'name': 'Process Payments', 'code': 'PAYMENT_PROCESS', 'description': 'Process payments', 'category': 'Billing'},
            {'name': 'Issue Refunds', 'code': 'REFUND_ISSUE', 'description': 'Issue refunds', 'category': 'Billing'},
            {'name': 'Void Transactions', 'code': 'TRANSACTION_VOID', 'description': 'Void financial transactions', 'category': 'Billing'},
            {'name': 'View Inventory', 'code': 'INVENTORY_VIEW', 'description': 'View inventory', 'category': 'Inventory'},
            {'name': 'Manage Inventory', 'code': 'INVENTORY_MANAGE', 'description': 'Manage inventory items', 'category': 'Inventory'},
            {'name': 'Process Stock Movements', 'code': 'STOCK_MOVE', 'description': 'Process stock movements', 'category': 'Inventory'},
            {'name': 'View Reports', 'code': 'REPORT_VIEW', 'description': 'View reports', 'category': 'Reports'},
            {'name': 'Generate Reports', 'code': 'REPORT_GENERATE', 'description': 'Generate reports', 'category': 'Reports'},
            {'name': 'Export Reports', 'code': 'REPORT_EXPORT', 'description': 'Export reports', 'category': 'Reports'},
            {'name': 'Manage Users', 'code': 'USER_MANAGE', 'description': 'Manage user accounts', 'category': 'Admin'},
            {'name': 'Manage Roles', 'code': 'ROLE_MANAGE', 'description': 'Manage roles and permissions', 'category': 'Admin'},
            {'name': 'View Audit Logs', 'code': 'AUDIT_VIEW', 'description': 'View audit logs', 'category': 'Admin'},
            {'name': 'System Configuration', 'code': 'SYS_CONFIG', 'description': 'Configure system settings', 'category': 'Admin'},
            {'name': 'Perform Triage', 'code': 'TRIAGE_PERFORM', 'description': 'Perform patient triage', 'category': 'Clinical'},
        ]

        permissions = {}
        for data in permissions_data:
            perm, created = Permission.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'category': data['category'],
                    'is_active': True
                }
            )
            permissions[data['code']] = perm
            status = 'CREATED' if created else 'EXISTS'
            self.stdout.write(f'  {data["code"]}: {data["name"]} [{status}]')

        return permissions

    def assign_permissions(self, roles, permissions):
        role_permissions_map = {
            'ADMIN': list(permissions.keys()),
            'SYS_ADMIN': list(permissions.keys()),
            'MED_DIRECTOR': ['PATIENT_VIEW', 'PATIENT_CREATE', 'PATIENT_EDIT',
                           'ENCOUNTER_VIEW', 'ENCOUNTER_CREATE', 'ENCOUNTER_EDIT', 'ENCOUNTER_SIGN',
                           'ORDER_VIEW', 'ORDER_CREATE', 'ORDER_CANCEL',
                           'RX_VIEW', 'RX_CREATE',
                           'INVOICE_VIEW', 'INVOICE_CREATE',
                           'REPORT_VIEW', 'REPORT_GENERATE', 'REPORT_EXPORT',
                           'TRIAGE_PERFORM'],
            'DOCTOR': ['PATIENT_VIEW', 'PATIENT_CREATE', 'PATIENT_EDIT',
                      'ENCOUNTER_VIEW', 'ENCOUNTER_CREATE', 'ENCOUNTER_EDIT', 'ENCOUNTER_SIGN',
                      'ORDER_VIEW', 'ORDER_CREATE', 'ORDER_CANCEL',
                      'RX_VIEW', 'RX_CREATE',
                      'REPORT_VIEW', 'TRIAGE_PERFORM'],
            'NURSE': ['PATIENT_VIEW', 'PATIENT_CREATE',
                     'ENCOUNTER_VIEW', 'ENCOUNTER_CREATE',
                     'ORDER_VIEW', 'ORDER_CREATE',
                     'RX_VIEW',
                     'TRIAGE_PERFORM'],
            'TRIAGE_NURSE': ['PATIENT_VIEW', 'PATIENT_CREATE',
                            'ENCOUNTER_VIEW',
                            'TRIAGE_PERFORM'],
            'PHARMACIST': ['PATIENT_VIEW', 'RX_VIEW', 'RX_CREATE', 'RX_DISPENSE',
                          'INVENTORY_VIEW', 'INVENTORY_MANAGE'],
            'LAB_TECH': ['PATIENT_VIEW', 'ENCOUNTER_VIEW', 'ORDER_VIEW'],
            'RADIOLOGIST': ['PATIENT_VIEW', 'ENCOUNTER_VIEW', 'ORDER_VIEW'],
            'CASHIER': ['PATIENT_VIEW', 'INVOICE_VIEW', 'INVOICE_CREATE',
                       'PAYMENT_PROCESS', 'REFUND_ISSUE'],
            'MRO': ['PATIENT_VIEW', 'PATIENT_CREATE', 'PATIENT_EDIT',
                   'ENCOUNTER_VIEW', 'REPORT_VIEW', 'REPORT_GENERATE', 'REPORT_EXPORT'],
            'INV_MGR': ['INVENTORY_VIEW', 'INVENTORY_MANAGE', 'STOCK_MOVE'],
            'NURSE_MGR': ['PATIENT_VIEW', 'ENCOUNTER_VIEW', 'ORDER_VIEW',
                         'REPORT_VIEW', 'TRIAGE_PERFORM'],
            'FIN_OFF': ['PATIENT_VIEW', 'INVOICE_VIEW', 'PAYMENT_PROCESS',
                       'REPORT_VIEW', 'REPORT_GENERATE'],
            'INT_AUDIT': ['PATIENT_VIEW', 'INVOICE_VIEW', 'AUDIT_VIEW', 'REPORT_VIEW'],
        }

        for role_code, perm_codes in role_permissions_map.items():
            if role_code in roles:
                for perm_code in perm_codes:
                    if perm_code in permissions:
                        RolePermission.objects.get_or_create(
                            role=roles[role_code],
                            permission=permissions[perm_code]
                        )
                self.stdout.write(f'  {role_code}: {len(perm_codes)} permissions assigned')

    def seed_lab_tests(self):
        lab_tests = [
            {'name': 'Complete Blood Count', 'code': 'CBC', 'category': 'Hematology', 'specimen_type': 'Blood', 'turnaround_time': '4 hours', 'price': 25.00},
            {'name': 'Hemoglobin', 'code': 'HGB', 'category': 'Hematology', 'specimen_type': 'Blood', 'turnaround_time': '4 hours', 'price': 10.00},
            {'name': 'White Blood Cell Count', 'code': 'WBC', 'category': 'Hematology', 'specimen_type': 'Blood', 'turnaround_time': '4 hours', 'price': 10.00},
            {'name': 'Platelet Count', 'code': 'PLT', 'category': 'Hematology', 'specimen_type': 'Blood', 'turnaround_time': '4 hours', 'price': 10.00},
            {'name': 'Blood Glucose', 'code': 'GLU', 'category': 'Chemistry', 'specimen_type': 'Blood', 'turnaround_time': '1 hour', 'price': 8.00},
            {'name': 'Basic Metabolic Panel', 'code': 'BMP', 'category': 'Chemistry', 'specimen_type': 'Blood', 'turnaround_time': '4 hours', 'price': 35.00},
            {'name': 'Comprehensive Metabolic Panel', 'code': 'CMP', 'category': 'Chemistry', 'specimen_type': 'Blood', 'turnaround_time': '4 hours', 'price': 50.00},
            {'name': 'Lipid Panel', 'code': 'LIPID', 'category': 'Chemistry', 'specimen_type': 'Blood', 'turnaround_time': '4 hours', 'price': 30.00},
            {'name': 'Liver Function Tests', 'code': 'LFT', 'category': 'Chemistry', 'specimen_type': 'Blood', 'turnaround_time': '4 hours', 'price': 35.00},
            {'name': 'Thyroid Stimulating Hormone', 'code': 'TSH', 'category': 'Endocrinology', 'specimen_type': 'Blood', 'turnaround_time': '24 hours', 'price': 40.00},
            {'name': 'Urinalysis', 'code': 'UA', 'category': 'Urinalysis', 'specimen_type': 'Urine', 'turnaround_time': '1 hour', 'price': 12.00},
            {'name': 'Urine Culture', 'code': 'UCULT', 'category': 'Microbiology', 'specimen_type': 'Urine', 'turnaround_time': '48 hours', 'price': 25.00},
            {'name': 'Blood Culture', 'code': 'BCULT', 'category': 'Microbiology', 'specimen_type': 'Blood', 'turnaround_time': '48 hours', 'price': 35.00},
            {'name': 'Stool Occult Blood', 'code': 'FOBT', 'category': 'Chemistry', 'specimen_type': 'Stool', 'turnaround_time': '24 hours', 'price': 15.00},
            {'name': 'Prothrombin Time', 'code': 'PT', 'category': 'Coagulation', 'specimen_type': 'Blood', 'turnaround_time': '2 hours', 'price': 18.00},
            {'name': 'INR', 'code': 'INR', 'category': 'Coagulation', 'specimen_type': 'Blood', 'turnaround_time': '2 hours', 'price': 18.00},
            {'name': 'Hemoglobin A1c', 'code': 'HBA1C', 'category': 'Endocrinology', 'specimen_type': 'Blood', 'turnaround_time': '24 hours', 'price': 30.00},
            {'name': 'Pregnancy Test (hCG)', 'code': 'HCG', 'category': 'Endocrinology', 'specimen_type': 'Urine', 'turnaround_time': '1 hour', 'price': 15.00},
            {'name': 'ESR', 'code': 'ESR', 'category': 'Hematology', 'specimen_type': 'Blood', 'turnaround_time': '1 hour', 'price': 10.00},
            {'name': 'CRP', 'code': 'CRP', 'category': 'Chemistry', 'specimen_type': 'Blood', 'turnaround_time': '4 hours', 'price': 20.00},
        ]

        for data in lab_tests:
            LabTestCatalogue.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
        self.stdout.write(f'  Seeded {len(lab_tests)} lab tests')

    def seed_radiology_tests(self):
        radiology_tests = [
            {'name': 'Chest X-Ray (PA View)', 'code': 'CXR_PA', 'body_part': 'Chest', 'modality': 'X-Ray', 'turnaround_time': '2 hours', 'price': 40.00},
            {'name': 'Chest X-Ray (Lateral View)', 'code': 'CXR_LAT', 'body_part': 'Chest', 'modality': 'X-Ray', 'turnaround_time': '2 hours', 'price': 40.00},
            {'name': 'Abdominal X-Ray', 'code': 'AXR', 'body_part': 'Abdomen', 'modality': 'X-Ray', 'turnaround_time': '2 hours', 'price': 35.00},
            {'name': 'Pelvic X-Ray', 'code': 'PXR', 'body_part': 'Pelvis', 'modality': 'X-Ray', 'turnaround_time': '2 hours', 'price': 35.00},
            {'name': 'Skull X-Ray', 'code': 'SKULL', 'body_part': 'Head', 'modality': 'X-Ray', 'turnaround_time': '2 hours', 'price': 35.00},
            {'name': 'Spine X-Ray (Cervical)', 'code': 'CSPINE', 'body_part': 'Spine', 'modality': 'X-Ray', 'turnaround_time': '2 hours', 'price': 40.00},
            {'name': 'Spine X-Ray (Lumbar)', 'code': 'LSPINE', 'body_part': 'Spine', 'modality': 'X-Ray', 'turnaround_time': '2 hours', 'price': 40.00},
            {'name': 'Extremity X-Ray', 'code': 'EXTR', 'body_part': 'Extremity', 'modality': 'X-Ray', 'turnaround_time': '2 hours', 'price': 30.00},
            {'name': 'CT Head', 'code': 'CT_HEAD', 'body_part': 'Head', 'modality': 'CT', 'turnaround_time': '4 hours', 'price': 120.00},
            {'name': 'CT Chest', 'code': 'CT_CHEST', 'body_part': 'Chest', 'modality': 'CT', 'turnaround_time': '4 hours', 'price': 150.00},
            {'name': 'CT Abdomen', 'code': 'CT_ABD', 'body_part': 'Abdomen', 'modality': 'CT', 'turnaround_time': '4 hours', 'price': 150.00},
            {'name': 'CT Pelvis', 'code': 'CT_PEL', 'body_part': 'Pelvis', 'modality': 'CT', 'turnaround_time': '4 hours', 'price': 150.00},
            {'name': 'CT Spine', 'code': 'CT_SPINE', 'body_part': 'Spine', 'modality': 'CT', 'turnaround_time': '4 hours', 'price': 150.00},
            {'name': 'Ultrasound Abdomen', 'code': 'US_ABD', 'body_part': 'Abdomen', 'modality': 'Ultrasound', 'turnaround_time': '4 hours', 'price': 80.00},
            {'name': 'Ultrasound Pelvis', 'code': 'US_PEL', 'body_part': 'Pelvis', 'modality': 'Ultrasound', 'turnaround_time': '4 hours', 'price': 80.00},
            {'name': 'Ultrasound Obstetric', 'code': 'US_OB', 'body_part': 'Obstetric', 'modality': 'Ultrasound', 'turnaround_time': '4 hours', 'price': 100.00},
            {'name': 'Ultrasound Thyroid', 'code': 'US_THY', 'body_part': 'Thyroid', 'modality': 'Ultrasound', 'turnaround_time': '4 hours', 'price': 80.00},
            {'name': 'Ultrasound Breast', 'code': 'US_BR', 'body_part': 'Breast', 'modality': 'Ultrasound', 'turnaround_time': '4 hours', 'price': 80.00},
            {'name': 'MRI Brain', 'code': 'MRI_HEAD', 'body_part': 'Head', 'modality': 'MRI', 'turnaround_time': '24 hours', 'price': 300.00},
            {'name': 'MRI Spine', 'code': 'MRI_SPINE', 'body_part': 'Spine', 'modality': 'MRI', 'turnaround_time': '24 hours', 'price': 350.00},
        ]

        for data in radiology_tests:
            RadiologyTestCatalogue.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
        self.stdout.write(f'  Seeded {len(radiology_tests)} radiology tests')

    def seed_medications(self):
        medications = [
            {'name': 'Paracetamol', 'generic_name': 'Acetaminophen', 'category': 'Analgesic', 'dosage_form': 'Tablet', 'strength': '500mg', 'route': 'Oral', 'price': 0.05},
            {'name': 'Ibuprofen', 'generic_name': 'Ibuprofen', 'category': 'NSAID', 'dosage_form': 'Tablet', 'strength': '400mg', 'route': 'Oral', 'price': 0.08},
            {'name': 'Amoxicillin', 'generic_name': 'Amoxicillin', 'category': 'Antibiotic', 'dosage_form': 'Capsule', 'strength': '500mg', 'route': 'Oral', 'price': 0.15},
            {'name': 'Metformin', 'generic_name': 'Metformin', 'category': 'Antidiabetic', 'dosage_form': 'Tablet', 'strength': '500mg', 'route': 'Oral', 'price': 0.10},
            {'name': 'Amlodipine', 'generic_name': 'Amlodipine', 'category': 'Antihypertensive', 'dosage_form': 'Tablet', 'strength': '5mg', 'route': 'Oral', 'price': 0.12},
            {'name': 'Omeprazole', 'generic_name': 'Omeprazole', 'category': 'Proton Pump Inhibitor', 'dosage_form': 'Capsule', 'strength': '20mg', 'route': 'Oral', 'price': 0.20},
            {'name': 'Cetirizine', 'generic_name': 'Cetirizine', 'category': 'Antihistamine', 'dosage_form': 'Tablet', 'strength': '10mg', 'route': 'Oral', 'price': 0.08},
            {'name': 'Salbutamol', 'generic_name': 'Salbutamol', 'category': 'Bronchodilator', 'dosage_form': 'Inhaler', 'strength': '100mcg', 'route': 'Inhalation', 'price': 5.00},
            {'name': 'Diclofenac', 'generic_name': 'Diclofenac', 'category': 'NSAID', 'dosage_form': 'Tablet', 'strength': '50mg', 'route': 'Oral', 'price': 0.10},
            {'name': 'Azithromycin', 'generic_name': 'Azithromycin', 'category': 'Antibiotic', 'dosage_form': 'Tablet', 'strength': '500mg', 'route': 'Oral', 'price': 0.25},
            {'name': 'Ciprofloxacin', 'generic_name': 'Ciprofloxacin', 'category': 'Antibiotic', 'dosage_form': 'Tablet', 'strength': '500mg', 'route': 'Oral', 'price': 0.20},
            {'name': 'Cotrimoxazole', 'generic_name': 'Sulfamethoxazole/Trimethoprim', 'category': 'Antibiotic', 'dosage_form': 'Tablet', 'strength': '480mg', 'route': 'Oral', 'price': 0.10},
            {'name': 'Artemether-Lumefantrine', 'generic_name': 'Artemether/Lumefantrine', 'category': 'Antimalarial', 'dosage_form': 'Tablet', 'strength': '20/120mg', 'route': 'Oral', 'price': 1.50},
            {'name': 'ORS Salts', 'generic_name': 'Oral Rehydration Salts', 'category': 'Electrolyte', 'dosage_form': 'Powder', 'strength': '1L', 'route': 'Oral', 'price': 0.30},
            {'name': 'Diazepam', 'generic_name': 'Diazepam', 'category': 'Benzodiazepine', 'dosage_form': 'Tablet', 'strength': '5mg', 'route': 'Oral', 'price': 0.15},
            {'name': 'Morphine Sulfate', 'generic_name': 'Morphine', 'category': 'Opioid Analgesic', 'dosage_form': 'Injection', 'strength': '10mg/ml', 'route': 'Intramuscular', 'price': 2.00, 'is_controlled': True, 'controlled_schedule': 2},
            {'name': 'Tramadol', 'generic_name': 'Tramadol', 'category': 'Opioid Analgesic', 'dosage_form': 'Capsule', 'strength': '50mg', 'route': 'Oral', 'price': 0.20, 'is_controlled': True, 'controlled_schedule': 3},
            {'name': 'Pantoprazole', 'generic_name': 'Pantoprazole', 'category': 'Proton Pump Inhibitor', 'dosage_form': 'Tablet', 'strength': '40mg', 'route': 'Oral', 'price': 0.25},
            {'name': 'Enalapril', 'generic_name': 'Enalapril', 'category': 'ACE Inhibitor', 'dosage_form': 'Tablet', 'strength': '10mg', 'route': 'Oral', 'price': 0.12},
            {'name': 'Atorvastatin', 'generic_name': 'Atorvastatin', 'category': 'Statin', 'dosage_form': 'Tablet', 'strength': '20mg', 'route': 'Oral', 'price': 0.30},
            {'name': 'Warfarin', 'generic_name': 'Warfarin', 'category': 'Anticoagulant', 'dosage_form': 'Tablet', 'strength': '5mg', 'route': 'Oral', 'price': 0.15},
            {'name': 'Aspirin', 'generic_name': 'Acetylsalicylic Acid', 'category': 'NSAID', 'dosage_form': 'Tablet', 'strength': '81mg', 'route': 'Oral', 'price': 0.03},
            {'name': 'Lisinopril', 'generic_name': 'Lisinopril', 'category': 'ACE Inhibitor', 'dosage_form': 'Tablet', 'strength': '10mg', 'route': 'Oral', 'price': 0.10},
            {'name': 'Simvastatin', 'generic_name': 'Simvastatin', 'category': 'Statin', 'dosage_form': 'Tablet', 'strength': '20mg', 'route': 'Oral', 'price': 0.12},
            {'name': 'Metoprolol', 'generic_name': 'Metoprolol', 'category': 'Beta Blocker', 'dosage_form': 'Tablet', 'strength': '50mg', 'route': 'Oral', 'price': 0.08},
            {'name': 'Lithium', 'generic_name': 'Lithium Carbonate', 'category': 'Mood Stabilizer', 'dosage_form': 'Tablet', 'strength': '300mg', 'route': 'Oral', 'price': 0.20},
            {'name': 'Phenytoin', 'generic_name': 'Phenytoin', 'category': 'Anticonvulsant', 'dosage_form': 'Capsule', 'strength': '100mg', 'route': 'Oral', 'price': 0.10},
            {'name': 'Digoxin', 'generic_name': 'Digoxin', 'category': 'Cardiac Glycoside', 'dosage_form': 'Tablet', 'strength': '0.25mg', 'route': 'Oral', 'price': 0.15},
            {'name': 'Methotrexate', 'generic_name': 'Methotrexate', 'category': 'Antifolate', 'dosage_form': 'Tablet', 'strength': '2.5mg', 'route': 'Oral', 'price': 0.50},
            {'name': 'Fluoxetine', 'generic_name': 'Fluoxetine', 'category': 'SSRI', 'dosage_form': 'Capsule', 'strength': '20mg', 'route': 'Oral', 'price': 0.15},
            {'name': 'Carbamazepine', 'generic_name': 'Carbamazepine', 'category': 'Anticonvulsant', 'dosage_form': 'Tablet', 'strength': '200mg', 'route': 'Oral', 'price': 0.10},
        ]

        for data in medications:
            price = data.pop('price', 0)
            Medication.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
        self.stdout.write(f'  Seeded {len(medications)} medications')

    def seed_service_items(self):
        default_list, _ = PriceList.objects.get_or_create(
            code='DEFAULT',
            defaults={'name': 'Standard Price List', 'is_default': True, 'is_active': True}
        )

        payer_categories = ['self_pay', 'insurance', 'corporate']

        clinical_items = [
            {'name': 'Consultation Fee', 'code': 'CONSULT', 'category': 'Clinical',
             'prices': {'self_pay': 25.00, 'insurance': 30.00, 'corporate': 28.00}},
            {'name': 'Triage Fee', 'code': 'TRIAGE', 'category': 'Clinical',
             'prices': {'self_pay': 10.00, 'insurance': 12.00, 'corporate': 11.00}},
            {'name': 'Registration Fee', 'code': 'REG', 'category': 'Administrative',
             'prices': {'self_pay': 5.00, 'insurance': 5.00, 'corporate': 5.00}},
            {'name': 'General Service Fee', 'code': 'SERVICE', 'category': 'General',
             'prices': {'self_pay': 15.00, 'insurance': 18.00, 'corporate': 16.00}},
            {'name': 'Laboratory Test Fee', 'code': 'LAB_TEST', 'category': 'Laboratory',
             'prices': {'self_pay': 20.00, 'insurance': 24.00, 'corporate': 22.00}},
            {'name': 'Radiology Test Fee', 'code': 'RAD_TEST', 'category': 'Radiology',
             'prices': {'self_pay': 30.00, 'insurance': 35.00, 'corporate': 32.00}},
        ]

        lab_items = [
            {'name': 'CBC', 'code': 'LAB_CBC', 'category': 'Laboratory',
             'prices': {'self_pay': 25.00, 'insurance': 30.00, 'corporate': 28.00}},
            {'name': 'Hemoglobin', 'code': 'LAB_HGB', 'category': 'Laboratory',
             'prices': {'self_pay': 10.00, 'insurance': 12.00, 'corporate': 11.00}},
            {'name': 'WBC', 'code': 'LAB_WBC', 'category': 'Laboratory',
             'prices': {'self_pay': 10.00, 'insurance': 12.00, 'corporate': 11.00}},
            {'name': 'Blood Glucose', 'code': 'LAB_GLU', 'category': 'Laboratory',
             'prices': {'self_pay': 8.00, 'insurance': 10.00, 'corporate': 9.00}},
            {'name': 'BMP', 'code': 'LAB_BMP', 'category': 'Laboratory',
             'prices': {'self_pay': 35.00, 'insurance': 42.00, 'corporate': 38.00}},
            {'name': 'CMP', 'code': 'LAB_CMP', 'category': 'Laboratory',
             'prices': {'self_pay': 50.00, 'insurance': 60.00, 'corporate': 55.00}},
            {'name': 'Lipid Panel', 'code': 'LAB_LIPID', 'category': 'Laboratory',
             'prices': {'self_pay': 30.00, 'insurance': 36.00, 'corporate': 33.00}},
            {'name': 'LFT', 'code': 'LAB_LFT', 'category': 'Laboratory',
             'prices': {'self_pay': 35.00, 'insurance': 42.00, 'corporate': 38.00}},
            {'name': 'TSH', 'code': 'LAB_TSH', 'category': 'Laboratory',
             'prices': {'self_pay': 40.00, 'insurance': 48.00, 'corporate': 44.00}},
            {'name': 'Urinalysis', 'code': 'LAB_UA', 'category': 'Laboratory',
             'prices': {'self_pay': 12.00, 'insurance': 15.00, 'corporate': 13.00}},
            {'name': 'HbA1c', 'code': 'LAB_HBA1C', 'category': 'Laboratory',
             'prices': {'self_pay': 30.00, 'insurance': 36.00, 'corporate': 33.00}},
            {'name': 'Pregnancy Test', 'code': 'LAB_HCG', 'category': 'Laboratory',
             'prices': {'self_pay': 15.00, 'insurance': 18.00, 'corporate': 16.00}},
        ]

        rad_items = [
            {'name': 'Chest X-Ray', 'code': 'RAD_CXR', 'category': 'Radiology',
             'prices': {'self_pay': 40.00, 'insurance': 48.00, 'corporate': 44.00}},
            {'name': 'Abdominal X-Ray', 'code': 'RAD_AXR', 'category': 'Radiology',
             'prices': {'self_pay': 35.00, 'insurance': 42.00, 'corporate': 38.00}},
            {'name': 'CT Head', 'code': 'RAD_CT_HEAD', 'category': 'Radiology',
             'prices': {'self_pay': 120.00, 'insurance': 144.00, 'corporate': 132.00}},
            {'name': 'CT Chest', 'code': 'RAD_CT_CHEST', 'category': 'Radiology',
             'prices': {'self_pay': 150.00, 'insurance': 180.00, 'corporate': 165.00}},
            {'name': 'CT Abdomen', 'code': 'RAD_CT_ABD', 'category': 'Radiology',
             'prices': {'self_pay': 150.00, 'insurance': 180.00, 'corporate': 165.00}},
            {'name': 'US Abdomen', 'code': 'RAD_US_ABD', 'category': 'Radiology',
             'prices': {'self_pay': 80.00, 'insurance': 96.00, 'corporate': 88.00}},
            {'name': 'US Pelvis', 'code': 'RAD_US_PEL', 'category': 'Radiology',
             'prices': {'self_pay': 80.00, 'insurance': 96.00, 'corporate': 88.00}},
            {'name': 'US Obstetric', 'code': 'RAD_US_OB', 'category': 'Radiology',
             'prices': {'self_pay': 100.00, 'insurance': 120.00, 'corporate': 110.00}},
            {'name': 'MRI Brain', 'code': 'RAD_MRI_HEAD', 'category': 'Radiology',
             'prices': {'self_pay': 300.00, 'insurance': 360.00, 'corporate': 330.00}},
            {'name': 'MRI Spine', 'code': 'RAD_MRI_SPINE', 'category': 'Radiology',
             'prices': {'self_pay': 350.00, 'insurance': 420.00, 'corporate': 385.00}},
        ]

        pharmacy_items = [
            {'name': 'Paracetamol 500mg', 'code': 'PHARM_PARA', 'category': 'Pharmacy',
             'prices': {'self_pay': 0.05, 'insurance': 0.06, 'corporate': 0.05}},
            {'name': 'Ibuprofen 400mg', 'code': 'PHARM_IBU', 'category': 'Pharmacy',
             'prices': {'self_pay': 0.08, 'insurance': 0.10, 'corporate': 0.09}},
            {'name': 'Amoxicillin 500mg', 'code': 'PHARM_AMOX', 'category': 'Pharmacy',
             'prices': {'self_pay': 0.15, 'insurance': 0.18, 'corporate': 0.16}},
            {'name': 'Metformin 500mg', 'code': 'PHARM_MET', 'category': 'Pharmacy',
             'prices': {'self_pay': 0.10, 'insurance': 0.12, 'corporate': 0.11}},
            {'name': 'Amlodipine 5mg', 'code': 'PHARM_AMLO', 'category': 'Pharmacy',
             'prices': {'self_pay': 0.12, 'insurance': 0.15, 'corporate': 0.13}},
            {'name': 'Omeprazole 20mg', 'code': 'PHARM_OMEP', 'category': 'Pharmacy',
             'prices': {'self_pay': 0.20, 'insurance': 0.24, 'corporate': 0.22}},
            {'name': 'Cetirizine 10mg', 'code': 'PHARM_CETI', 'category': 'Pharmacy',
             'prices': {'self_pay': 0.08, 'insurance': 0.10, 'corporate': 0.09}},
            {'name': 'Salbutamol Inhaler', 'code': 'PHARM_SALB', 'category': 'Pharmacy',
             'prices': {'self_pay': 5.00, 'insurance': 6.00, 'corporate': 5.50}},
            {'name': 'Azithromycin 500mg', 'code': 'PHARM_AZIT', 'category': 'Pharmacy',
             'prices': {'self_pay': 0.25, 'insurance': 0.30, 'corporate': 0.28}},
            {'name': 'Artemether-Lumefantrine', 'code': 'PHARM_AL', 'category': 'Pharmacy',
             'prices': {'self_pay': 1.50, 'insurance': 1.80, 'corporate': 1.65}},
            {'name': 'ORS Salts', 'code': 'PHARM_ORS', 'category': 'Pharmacy',
             'prices': {'self_pay': 0.30, 'insurance': 0.36, 'corporate': 0.33}},
            {'name': 'Tramadol 50mg', 'code': 'PHARM_TRAM', 'category': 'Pharmacy',
             'prices': {'self_pay': 0.20, 'insurance': 0.24, 'corporate': 0.22}},
        ]

        all_items = clinical_items + lab_items + rad_items + pharmacy_items
        count = 0

        for data in all_items:
            prices = data.pop('prices')
            item, _ = ServiceItem.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            for payer, price in prices.items():
                ServicePrice.objects.get_or_create(
                    service_item=item,
                    price_list=default_list,
                    payer_category=payer,
                    effective_date='2024-01-01',
                    defaults={'price': price}
                )
            count += 1

        self.stdout.write(f'  Seeded {count} service items with prices for {len(payer_categories)} payer categories')

    def seed_inventory(self):
        main_pharmacy, _ = Store.objects.get_or_create(
            code='PHARM_MAIN',
            defaults={
                'name': 'Main Pharmacy',
                'store_type': 'pharmacy',
                'location': 'Ground Floor, Block A',
                'is_active': True,
            }
        )

        ward_pharmacy, _ = Store.objects.get_or_create(
            code='PHARM_WARD',
            defaults={
                'name': 'Ward Pharmacy',
                'store_type': 'pharmacy',
                'location': 'Ward Block, Level 2',
                'is_active': True,
            }
        )

        lab_store, _ = Store.objects.get_or_create(
            code='LAB_STORE',
            defaults={
                'name': 'Laboratory Store',
                'store_type': 'laboratory',
                'location': 'Laboratory Block',
                'is_active': True,
            }
        )

        central_store, _ = Store.objects.get_or_create(
            code='CENTRAL',
            defaults={
                'name': 'Central Warehouse',
                'store_type': 'warehouse',
                'location': 'Main Building, Basement',
                'is_active': True,
            }
        )

        surgical_store, _ = Store.objects.get_or_create(
            code='SURG_STORE',
            defaults={
                'name': 'Surgical Supplies Store',
                'store_type': 'supplies',
                'location': 'Theatre Block, Level 1',
                'is_active': True,
            }
        )

        self.stdout.write(f'  Created stores: Main Pharmacy, Ward Pharmacy, Laboratory Store, Central Warehouse, Surgical Supplies Store')

        med_category, _ = Category.objects.get_or_create(
            code='MED',
            defaults={'name': 'Medications', 'is_active': True}
        )

        consumable_category, _ = Category.objects.get_or_create(
            code='CONS',
            defaults={'name': 'Consumables', 'is_active': True}
        )

        equipment_category, _ = Category.objects.get_or_create(
            code='EQUIP',
            defaults={'name': 'Medical Equipment', 'is_active': True}
        )

        surgical_category, _ = Category.objects.get_or_create(
            code='SURG',
            defaults={'name': 'Surgical Supplies', 'is_active': True}
        )

        lab_category, _ = Category.objects.get_or_create(
            code='LAB_CAT',
            defaults={'name': 'Laboratory Supplies', 'is_active': True}
        )

        self.stdout.write(f'  Created categories: Medications, Consumables, Medical Equipment, Surgical Supplies, Laboratory Supplies')

        # Seed inventory items for medications
        medications = Medication.objects.filter(is_active=True)
        stock_count = 0

        for med in medications:
            inventory_item, _ = InventoryItem.objects.get_or_create(
                code=f'MED_{med.medication_code or med.name[:10].upper().replace(" ", "")}',
                defaults={
                    'name': med.name,
                    'category': med_category,
                    'unit_of_measure': 'tablets' if med.dosage_form in ['Tablet', 'Capsule'] else 'units',
                    'is_medication': True,
                    'medication': med,
                    'reorder_level': 100,
                    'reorder_quantity': 500,
                    'minimum_stock': 50,
                    'maximum_stock': 2000,
                    'unit_cost': 0.10,
                }
            )

            Stock.objects.get_or_create(
                item=inventory_item,
                store=main_pharmacy,
                batch_lot_number=f'BATCH-{med.name[:5].upper()}-001',
                defaults={
                    'quantity_on_hand': 1000,
                    'unit_cost': 0.10,
                    'expiry_date': '2026-12-31',
                }
            )
            stock_count += 1

        self.stdout.write(f'  Created {stock_count} medication inventory items with stock')

        # Seed consumable items
        consumables_data = [
            {'name': 'Disposable Gloves (Box of 100)', 'code': 'CONS_GLOVES', 'uom': 'box', 'reorder': 50, 'qty': 200, 'cost': 8.00},
            {'name': 'Surgical Masks (Box of 50)', 'code': 'CONS_MASKS', 'uom': 'box', 'reorder': 30, 'qty': 150, 'cost': 12.00},
            {'name': 'Face Shields', 'code': 'CONS_SHIELDS', 'uom': 'pieces', 'reorder': 20, 'qty': 80, 'cost': 5.00},
            {'name': 'Syringes 5ml (Box of 100)', 'code': 'CONS_SYR5', 'uom': 'box', 'reorder': 40, 'qty': 180, 'cost': 15.00},
            {'name': 'Syringes 10ml (Box of 100)', 'code': 'CONS_SYR10', 'uom': 'box', 'reorder': 30, 'qty': 120, 'cost': 18.00},
            {'name': 'IV Cannula 18G (Box of 50)', 'code': 'CONS_IV18', 'uom': 'box', 'reorder': 25, 'qty': 100, 'cost': 25.00},
            {'name': 'IV Cannula 22G (Box of 50)', 'code': 'CONS_IV22', 'uom': 'box', 'reorder': 25, 'qty': 100, 'cost': 25.00},
            {'name': 'IV Tubling Set', 'code': 'CONS_IVTUB', 'uom': 'pieces', 'reorder': 50, 'qty': 200, 'cost': 2.50},
            {'name': 'Normal Saline 1000ml', 'code': 'CONS_NS', 'uom': 'bottles', 'reorder': 40, 'qty': 150, 'cost': 3.00},
            {'name': 'Ringers Lactate 1000ml', 'code': 'CONS_RL', 'uom': 'bottles', 'reorder': 30, 'qty': 100, 'cost': 3.50},
            {'name': 'Gauze Pads 10x10 (Pack of 100)', 'code': 'CONS_GAUZE', 'uom': 'pack', 'reorder': 30, 'qty': 120, 'cost': 6.00},
            {'name': 'Adhesive Tape Roll', 'code': 'CONS_TAPE', 'uom': 'rolls', 'reorder': 40, 'qty': 200, 'cost': 1.50},
            {'name': 'Cotton Wool 500g', 'code': 'CONS_COTTON', 'uom': 'packs', 'reorder': 20, 'qty': 80, 'cost': 4.00},
            {'name': 'Alcohol Swabs (Box of 100)', 'code': 'CONS_ALC', 'uom': 'box', 'reorder': 30, 'qty': 150, 'cost': 5.00},
            {'name': 'Disposable Needles 23G (Box of 100)', 'code': 'CONS_NEED23', 'uom': 'box', 'reorder': 30, 'qty': 120, 'cost': 8.00},
            {'name': 'Urine Bags 2000ml', 'code': 'CONS_UBAG', 'uom': 'pieces', 'reorder': 20, 'qty': 80, 'cost': 3.00},
            {'name': 'Nasal Oxygen Cannula', 'code': 'CONS_NASAL', 'uom': 'pieces', 'reorder': 20, 'qty': 60, 'cost': 4.00},
            {'name': 'Oxygen Mask', 'code': 'CONS_OMASK', 'uom': 'pieces', 'reorder': 15, 'qty': 50, 'cost': 3.50},
            {'name': 'Stethoscope (Single Use)', 'code': 'CONS_STETH', 'uom': 'pieces', 'reorder': 10, 'qty': 30, 'cost': 2.00},
            {'name': 'Examination Gloves Nitrile (Box of 100)', 'code': 'CONS_NGLV', 'uom': 'box', 'reorder': 40, 'qty': 160, 'cost': 12.00},
        ]

        consumable_count = 0
        for data in consumables_data:
            item, _ = InventoryItem.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'category': consumable_category,
                    'unit_of_measure': data['uom'],
                    'is_consumable': True,
                    'reorder_level': data['reorder'],
                    'reorder_quantity': data['reorder'] * 3,
                    'minimum_stock': data['reorder'] // 2,
                    'maximum_stock': data['reorder'] * 5,
                    'unit_cost': data['cost'],
                }
            )
            Stock.objects.get_or_create(
                item=item,
                store=main_pharmacy,
                batch_lot_number=f'BATCH-{data["code"][-6:]}-001',
                defaults={
                    'quantity_on_hand': data['qty'],
                    'unit_cost': data['cost'],
                    'expiry_date': '2027-06-30',
                }
            )
            consumable_count += 1

        self.stdout.write(f'  Created {consumable_count} consumable items with stock')

        # Seed equipment items
        equipment_data = [
            {'name': 'Digital Thermometer', 'code': 'EQUIP_THERM', 'uom': 'pieces', 'reorder': 5, 'qty': 20, 'cost': 15.00},
            {'name': 'Blood Pressure Monitor (Manual)', 'code': 'EQUIP_BPM', 'uom': 'pieces', 'reorder': 3, 'qty': 12, 'cost': 25.00},
            {'name': 'Pulse Oximeter', 'code': 'EQUIP_PULSE', 'uom': 'pieces', 'reorder': 3, 'qty': 10, 'cost': 45.00},
            {'name': 'Nebulizer Machine', 'code': 'EQUIP_NEB', 'uom': 'pieces', 'reorder': 2, 'qty': 6, 'cost': 80.00},
            {'name': 'Suction Machine', 'code': 'EQUIP_SUCTION', 'uom': 'pieces', 'reorder': 1, 'qty': 3, 'cost': 200.00},
            {'name': 'Defibrillator Pads', 'code': 'EQUIP_DEFIB', 'uom': 'pairs', 'reorder': 4, 'qty': 15, 'cost': 50.00},
            {'name': 'ECG Electrodes (Pack of 50)', 'code': 'EQUIP_ECG', 'uom': 'pack', 'reorder': 10, 'qty': 30, 'cost': 20.00},
            {'name': 'Glucometer Strips (Box of 50)', 'code': 'EQUIP_GSTRIP', 'uom': 'box', 'reorder': 15, 'qty': 60, 'cost': 18.00},
        ]

        equipment_count = 0
        for data in equipment_data:
            item, _ = InventoryItem.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'category': equipment_category,
                    'unit_of_measure': data['uom'],
                    'is_equipment': True,
                    'reorder_level': data['reorder'],
                    'reorder_quantity': data['reorder'] * 2,
                    'minimum_stock': data['reorder'],
                    'maximum_stock': data['reorder'] * 4,
                    'unit_cost': data['cost'],
                }
            )
            Stock.objects.get_or_create(
                item=item,
                store=central_store,
                batch_lot_number=f'BATCH-{data["code"][-6:]}-001',
                defaults={
                    'quantity_on_hand': data['qty'],
                    'unit_cost': data['cost'],
                }
            )
            equipment_count += 1

        self.stdout.write(f'  Created {equipment_count} equipment items with stock')

        # Seed surgical supplies
        surgical_data = [
            {'name': 'Suture Kit (Absorbable)', 'code': 'SURG_SUT_A', 'uom': 'packs', 'reorder': 10, 'qty': 40, 'cost': 15.00},
            {'name': 'Suture Kit (Non-Absorbable)', 'code': 'SURG_SUT_N', 'uom': 'packs', 'reorder': 10, 'qty': 40, 'cost': 12.00},
            {'name': 'Surgical Gloves (Box of 50)', 'code': 'SURG_GLOV', 'uom': 'box', 'reorder': 15, 'qty': 60, 'cost': 20.00},
            {'name': 'Scalpel Blades (Box of 100)', 'code': 'SURG_SCAL', 'uom': 'box', 'reorder': 5, 'qty': 25, 'cost': 18.00},
            {'name': 'Surgical Drapes (Disposable)', 'code': 'SURG_DRAP', 'uom': 'pieces', 'reorder': 20, 'qty': 80, 'cost': 8.00},
            {'name': 'Sterile Dressing Pack', 'code': 'SURG_DRES', 'uom': 'packs', 'reorder': 20, 'qty': 70, 'cost': 5.00},
            {'name': 'Bone Cement', 'code': 'SURG_BONE', 'uom': 'units', 'reorder': 3, 'qty': 10, 'cost': 120.00},
            {'name': 'Drainage Tube', 'code': 'SURG_DRAIN', 'uom': 'pieces', 'reorder': 10, 'qty': 30, 'cost': 6.00},
        ]

        surgical_count = 0
        for data in surgical_data:
            item, _ = InventoryItem.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'category': surgical_category,
                    'unit_of_measure': data['uom'],
                    'is_consumable': True,
                    'reorder_level': data['reorder'],
                    'reorder_quantity': data['reorder'] * 2,
                    'minimum_stock': data['reorder'],
                    'maximum_stock': data['reorder'] * 4,
                    'unit_cost': data['cost'],
                }
            )
            Stock.objects.get_or_create(
                item=item,
                store=surgical_store,
                batch_lot_number=f'BATCH-{data["code"][-6:]}-001',
                defaults={
                    'quantity_on_hand': data['qty'],
                    'unit_cost': data['cost'],
                    'expiry_date': '2027-12-31',
                }
            )
            surgical_count += 1

        self.stdout.write(f'  Created {surgical_count} surgical supply items with stock')

        # Seed lab supplies
        lab_supplies_data = [
            {'name': 'Test Tubes (Box of 100)', 'code': 'LAB_TTUBE', 'uom': 'box', 'reorder': 20, 'qty': 80, 'cost': 8.00},
            {'name': 'Microscope Slides (Box of 50)', 'code': 'LAB_SLIDE', 'uom': 'box', 'reorder': 15, 'qty': 60, 'cost': 6.00},
            {'name': 'Blood Collection Tubes EDTA', 'code': 'LAB_EDTA', 'uom': 'box', 'reorder': 20, 'qty': 100, 'cost': 10.00},
            {'name': 'Blood Collection Tubes Plain', 'code': 'LAB_PLAIN', 'uom': 'box', 'reorder': 20, 'qty': 100, 'cost': 8.00},
            {'name': 'Reagent Kit - Malaria Rapid', 'code': 'LAB_MALARIA', 'uom': 'kits', 'reorder': 10, 'qty': 50, 'cost': 25.00},
            {'name': 'Reagent Kit - HIV Rapid', 'code': 'LAB_HIV', 'uom': 'kits', 'reorder': 10, 'qty': 40, 'cost': 30.00},
            {'name': 'Reagent Kit - Pregnancy Test', 'code': 'LAB_PREG', 'uom': 'kits', 'reorder': 15, 'qty': 60, 'cost': 12.00},
            {'name': 'Urinalysis Strips (Box of 100)', 'code': 'LAB_UASTRIP', 'uom': 'box', 'reorder': 10, 'qty': 40, 'cost': 15.00},
        ]

        lab_count = 0
        for data in lab_supplies_data:
            item, _ = InventoryItem.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'category': lab_category,
                    'unit_of_measure': data['uom'],
                    'is_consumable': True,
                    'reorder_level': data['reorder'],
                    'reorder_quantity': data['reorder'] * 3,
                    'minimum_stock': data['reorder'],
                    'maximum_stock': data['reorder'] * 5,
                    'unit_cost': data['cost'],
                }
            )
            Stock.objects.get_or_create(
                item=item,
                store=lab_store,
                batch_lot_number=f'BATCH-{data["code"][-6:]}-001',
                defaults={
                    'quantity_on_hand': data['qty'],
                    'unit_cost': data['cost'],
                    'expiry_date': '2027-06-30',
                }
            )
            lab_count += 1

        self.stdout.write(f'  Created {lab_count} laboratory supply items with stock')

    def seed_drug_interactions(self):
        from pharmacy.models import Medication, DrugInteraction

        interactions_data = [
            ('Warfarin', 'Aspirin', 'severe', 'Increased risk of bleeding. INR monitoring required.', 'Avoid combination or monitor INR closely'),
            ('Warfarin', 'Ibuprofen', 'severe', 'NSAIDs increase bleeding risk with warfarin.', 'Use acetaminophen instead'),
            ('Metformin', 'Alcohol', 'severe', 'Alcohol increases risk of lactic acidosis with metformin.', 'Limit alcohol intake'),
            ('Lisinopril', 'Potassium', 'moderate', 'ACE inhibitors increase potassium levels.', 'Monitor serum potassium'),
            ('Simvastatin', 'Amiodarone', 'severe', 'Increased risk of rhabdomyolysis.', 'Limit simvastatin to 20mg/day'),
            ('Ciprofloxacin', 'Antacids', 'moderate', 'Antacids reduce ciprofloxacin absorption.', 'Take ciprofloxacin 2 hours before antacids'),
            ('Omeprazole', 'Clopidogrel', 'severe', 'PPIs reduce antiplatelet effect of clopidogrel.', 'Use pantoprazole instead'),
            ('Fluoxetine', 'Tramadol', 'severe', 'Increased risk of serotonin syndrome.', 'Avoid combination'),
            ('Metoprolol', 'Verapamil', 'severe', 'Risk of severe bradycardia and heart block.', 'Avoid combination'),
            ('Lithium', 'Ibuprofen', 'moderate', 'NSAIDs increase lithium levels.', 'Use acetaminophen or monitor lithium levels'),
            ('Phenytoin', 'Amiodarone', 'moderate', 'Amiodarone increases phenytoin levels.', 'Monitor phenytoin levels'),
            ('Digoxin', 'Amiodarone', 'moderate', 'Amiodarone increases digoxin levels.', 'Reduce digoxin dose by 50%'),
            ('Methotrexate', 'Ibuprofen', 'severe', 'NSAIDs reduce methotrexate clearance.', 'Use acetaminophen'),
            ('Clarithromycin', 'Statins', 'moderate', 'Macrolides increase statin levels.', 'Monitor for muscle pain'),
            ('Carbamazepine', 'Erythromycin', 'moderate', 'Erythromycin increases carbamazepine levels.', 'Monitor carbamazepine levels'),
            ('Fluconazole', 'Warfarin', 'severe', 'Fluconazole increases warfarin effect.', 'Monitor INR closely'),
            ('Rifampin', 'Oral Contraceptives', 'severe', 'Rifampin reduces contraceptive efficacy.', 'Use alternative contraception'),
            ('Ketoconazole', 'Simvastatin', 'severe', 'Increased risk of rhabdomyolysis.', 'Avoid combination'),
            ('Ciprofloxacin', 'Tizanidine', 'severe', 'Ciprofloxacin dramatically increases tizanidine levels.', 'Contraindicated'),
            ('Fluoxetine', 'MAOIs', 'severe', 'Risk of fatal serotonin syndrome.', 'Contraindicated - washout period required'),
        ]

        count = 0
        for drug_a_name, drug_b_name, severity, desc, rec in interactions_data:
            try:
                drug_a = Medication.objects.filter(name__icontains=drug_a_name).first()
                drug_b = Medication.objects.filter(name__icontains=drug_b_name).first()
                if not drug_a or not drug_b:
                    continue
                DrugInteraction.objects.get_or_create(
                    drug_a=drug_a, drug_b=drug_b,
                    defaults={
                        'severity': severity,
                        'description': desc,
                        'recommendation': rec,
                    }
                )
                count += 1
            except Exception:
                continue

        self.stdout.write(f'  Created {count} drug interactions')
