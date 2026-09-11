import uuid
from django.db import models


class SyncStatus(models.TextChoices):
    LOCAL = 'local', 'Local'
    SYNCED = 'synced', 'Synced'


class Gender(models.TextChoices):
    MALE = 'M', 'Male'
    FEMALE = 'F', 'Female'


class BloodType(models.TextChoices):
    A_POS = 'A+', 'A+'
    A_NEG = 'A-', 'A-'
    B_POS = 'B+', 'B+'
    B_NEG = 'B-', 'B-'
    AB_POS = 'AB+', 'AB+'
    AB_NEG = 'AB-', 'AB-'
    O_POS = 'O+', 'O+'
    O_NEG = 'O-', 'O-'
    UNKNOWN = 'UNKNOWN', 'Unknown'


class MaritalStatus(models.TextChoices):
    SINGLE = 'single', 'Single'
    MARRIED = 'married', 'Married'
    DIVORCED = 'divorced', 'Divorced'
    WIDOWED = 'widowed', 'Widowed'
    SEPARATED = 'separated', 'Separated'
    UNKNOWN = 'unknown', 'Unknown'


class PatientStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    DECEASED = 'deceased', 'Deceased'
    MERGED = 'merged', 'Merged'


class Severity(models.TextChoices):
    CRITICAL = 'critical', 'Critical'
    HIGH = 'high', 'High'
    MEDIUM = 'medium', 'Medium'
    LOW = 'low', 'Low'


class Patient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mrn = models.CharField(max_length=20, unique=True, editable=False, blank=True, null=True)
    is_temporary = models.BooleanField(default=False, help_text='True for emergency bypass patients awaiting formal registration')
    temporary_token = models.CharField(max_length=30, blank=True, null=True, editable=False, help_text='Temporary identifier (TEMP-ER-YYYY-XXXXX)')
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, default=Gender.MALE)
    blood_type = models.CharField(max_length=7, choices=BloodType.choices, default=BloodType.UNKNOWN)
    marital_status = models.CharField(max_length=10, choices=MaritalStatus.choices, default=MaritalStatus.UNKNOWN)
    nationality = models.CharField(max_length=50, blank=True, null=True)
    ethnicity = models.CharField(max_length=50, blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    education_level = models.CharField(max_length=50, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state_province = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, default='Liberia')
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    photo = models.ImageField(upload_to='patients/photos/', blank=True, null=True)
    identification_type = models.CharField(max_length=50, blank=True, null=True)
    identification_number = models.CharField(max_length=100, blank=True, null=True)
    next_of_kin_name = models.CharField(max_length=200, blank=True, null=True)
    next_of_kin_phone = models.CharField(max_length=20, blank=True, null=True)
    next_of_kin_relationship = models.CharField(max_length=50, blank=True, null=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True, null=True)
    insurance_provider = models.CharField(max_length=100, blank=True, null=True)
    insurance_policy_number = models.CharField(max_length=100, blank=True, null=True)
    insurance_group_number = models.CharField(max_length=100, blank=True, null=True)
    insurance_expiry_date = models.DateField(blank=True, null=True)
    payer_category = models.CharField(max_length=50, blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=PatientStatus.choices, default=PatientStatus.ACTIVE)
    merged_into = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='merged_patients')
    registered_by = models.UUIDField(null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'patients'
        managed = True
        ordering = ['-created_at']

    def __str__(self):
        if self.is_temporary:
            return f"{self.temporary_token or 'TEMP'} - {self.first_name} {self.last_name}"
        return f"{self.mrn or 'NO_MRN'} - {self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        if self.is_temporary and not self.temporary_token:
            self.temporary_token = self._generate_temporary_token()
        elif not self.mrn and not self.is_temporary:
            self.mrn = self._generate_mrn_with_retry()
        super().save(*args, **kwargs)

    def _generate_temporary_token(self):
        """Generate unique temporary token in format TEMP-{PREFIX}-YYYY-XXXXX."""
        from datetime import date
        from django.db import connection
        year = date.today().year
        prefix = 'TEMP-ER'
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM patients WHERE temporary_token LIKE %s",
                [f'{prefix}-{year}-%']
            )
            count = cursor.fetchone()[0]
        seq = count + 1
        return f'{prefix}-{year}-{seq:05d}'

    def _generate_mrn_with_retry(self, max_retries=5):
        """Generate unique MRN with retry logic to handle race conditions."""
        from django.db import IntegrityError
        for attempt in range(max_retries):
            mrn = self._generate_mrn()
            try:
                Patient.objects.get(mrn=mrn)
            except Patient.DoesNotExist:
                return mrn
            except Exception:
                return mrn
        raise IntegrityError('Could not generate unique MRN after %d attempts' % max_retries)

    def _generate_mrn(self):
        """Generate unique MRN in format JFD-YYYY-XXXXX."""
        from datetime import date
        from django.db import connection
        year = date.today().year
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM patients WHERE mrn LIKE %s",
                [f'JFD-{year}-%']
            )
            count = cursor.fetchone()[0]
        seq = count + 1
        return f'JFD-{year}-{seq:05d}'

    @property
    def full_name(self):
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class PatientAllergy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='allergies')
    allergen = models.CharField(max_length=200)
    allergy_type = models.CharField(max_length=50, blank=True, null=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MEDIUM)
    reaction = models.TextField(blank=True, null=True)
    onset_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, default='active')
    notes = models.TextField(blank=True, null=True)
    recorded_by = models.UUIDField(null=True, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patient_allergies'
        managed = True

    def __str__(self):
        return f"{self.patient.mrn} - {self.allergen}"


class PatientAlert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50)
    alert_text = models.TextField()
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.HIGH)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    created_by = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patient_alerts'
        managed = True

    def __str__(self):
        return f"{self.patient.mrn} - {self.alert_type}: {self.alert_text[:50]}"


class PatientDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50)
    document_name = models.CharField(max_length=255)
    file_url = models.CharField(max_length=500)
    file_size = models.IntegerField(blank=True, null=True)
    mime_type = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    uploaded_by = models.UUIDField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'patient_documents'
        managed = True

    def __str__(self):
        return f"{self.patient.mrn} - {self.document_name}"


class PatientConsent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='consents')
    consent_type = models.CharField(max_length=100)
    consent_given = models.BooleanField()
    consent_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(blank=True, null=True)
    witness_name = models.CharField(max_length=200, blank=True, null=True)
    witness_signature_url = models.CharField(max_length=500, blank=True, null=True)
    patient_signature_url = models.CharField(max_length=500, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'patient_consents'
        managed = True

    def __str__(self):
        return f"{self.patient.mrn} - {self.consent_type}"
