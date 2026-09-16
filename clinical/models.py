import uuid
from django.db import models
from django.utils import timezone


class SyncStatus(models.TextChoices):
    LOCAL = 'local', 'Local'
    SYNCED = 'synced', 'Synced'


class VisitStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    CHECKED_IN = 'checked_in', 'Checked In'
    IN_TRIAGE = 'in_triage', 'In Triage'
    IN_PROGRESS = 'in_progress', 'In Progress'
    PENDING_REGISTRATION = 'pending_registration', 'Pending Registration'
    AWAITING_RECONCILIATION = 'awaiting_reconciliation', 'Awaiting Reconciliation'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    NO_SHOW = 'no_show', 'No Show'


class EncounterType(models.TextChoices):
    OPD = 'opd', 'Outpatient Department'
    IPD = 'ipd', 'Inpatient Department'
    ER = 'er', 'Emergency Room'
    PEDIATRIC = 'pediatric', 'Pediatric'
    OBGYN = 'obgyn', 'Obstetrics & Gynecology'
    ANC = 'anc', 'Antenatal Care'
    LABOR_DELIVERY = 'labor_delivery', 'Labor & Delivery'
    POSTPARTUM = 'postpartum', 'Postpartum'
    SURGERY = 'surgery', 'Surgery'
    TELEMEDICINE = 'telemedicine', 'Telemedicine'


class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    FAILED = 'failed', 'Failed'


class Priority(models.TextChoices):
    ROUTINE = 'routine', 'Routine'
    URGENT = 'urgent', 'Urgent'
    STAT = 'stat', 'STAT'
    ASAP = 'asap', 'ASAP'


class DischargeStatus(models.TextChoices):
    ROUTINE = 'routine', 'Routine'
    AGAINST_MEDICAL_ADVICE = 'against_medical_advice', 'Against Medical Advice'
    REFERRED = 'referred', 'Referred'
    TRANSFERRED = 'transferred', 'Transferred'
    DECEASED = 'deceased', 'Deceased'


class AdmissionStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    DISCHARGED = 'discharged', 'Discharged'
    TRANSFERRED = 'transferred', 'Transferred'
    AMENDED = 'amended', 'Amended'


class Ward(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey('users_auth.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='wards')
    ward_type = models.CharField(max_length=50, blank=True, null=True)
    floor = models.CharField(max_length=20, blank=True, null=True)
    capacity = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wards'
        managed = True

    def __str__(self):
        return f"{self.code} - {self.name}"


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=50, blank=True, null=True)
    capacity = models.IntegerField(default=1)
    is_private = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rooms'
        managed = True
        unique_together = ('ward', 'room_number')

    def __str__(self):
        return f"{self.ward.code} - Room {self.room_number}"


class Bed(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=20)
    bed_type = models.CharField(max_length=50, default='standard')
    is_occupied = models.BooleanField(default=False)
    is_reserved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'beds'
        managed = True
        unique_together = ('room', 'bed_number')

    def __str__(self):
        return f"{self.room.ward.code} - {self.room.room_number} - Bed {self.bed_number}"


class Visit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='visits', null=True, blank=True)
    visit_number = models.CharField(max_length=20, unique=True, editable=False)
    visit_date = models.DateField(auto_now_add=True)
    visit_type = models.CharField(max_length=20, choices=EncounterType.choices)
    department = models.ForeignKey('users_auth.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='visits')
    status = models.CharField(max_length=30, choices=VisitStatus.choices, default=VisitStatus.SCHEDULED)
    chief_complaint = models.TextField(blank=True, null=True)
    triage_priority = models.CharField(max_length=10, choices=Priority.choices, blank=True, null=True)
    triage_notes = models.TextField(blank=True, null=True)
    triage_time = models.DateTimeField(blank=True, null=True)
    check_in_time = models.DateTimeField(blank=True, null=True)
    check_out_time = models.DateTimeField(blank=True, null=True)
    provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='visits_as_provider')
    attending_physician = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='visits_as_attending')
    nurse = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='visits_as_nurse')
    appointment_id = models.UUIDField(null=True, blank=True)
    is_follow_up = models.BooleanField(default=False)
    follow_up_date = models.DateField(blank=True, null=True)
    is_emergency_bypass = models.BooleanField(default=False)
    emergency_bypass_reason = models.TextField(blank=True, null=True)
    temporary_token = models.CharField(max_length=30, blank=True, null=True, editable=False)
    route_override = models.CharField(max_length=20, blank=True, null=True)
    route_override_reason = models.TextField(blank=True, null=True)
    acuity_override = models.BooleanField(default=False)
    acuity_override_reason = models.TextField(blank=True, null=True)
    suggested_acuity = models.IntegerField(blank=True, null=True)
    suggested_department = models.CharField(max_length=20, blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'visits'
        managed = True
        ordering = ['-visit_date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.visit_number:
            from django.conf import settings
            fmt = getattr(settings, 'HMS_VISIT_FORMAT', 'VIS-{date}-{sequence:05d}')
            today = timezone.now().strftime('%Y%m%d')
            prefix = fmt.replace('{date}', today).replace('{sequence:05d}', '')
            from jfd_hms.utils import generate_sequence_number
            self.visit_number = generate_sequence_number(prefix, Visit, 'visit_number')
        super().save(*args, **kwargs)

    def __str__(self):
        patient_id = self.patient.mrn if self.patient else self.temporary_token or 'NO_PATIENT'
        return f"{self.visit_number} - {patient_id}"


class TriageRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='triage_records')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='triage_records', null=True, blank=True)
    queue_number = models.CharField(max_length=20, blank=True, editable=False)
    chief_complaint = models.TextField()
    acuity_level = models.IntegerField(blank=True, null=True)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    heart_rate = models.IntegerField(blank=True, null=True)
    respiratory_rate = models.IntegerField(blank=True, null=True)
    blood_pressure_systolic = models.IntegerField(blank=True, null=True)
    blood_pressure_diastolic = models.IntegerField(blank=True, null=True)
    oxygen_saturation = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    pain_scale = models.IntegerField(blank=True, null=True)
    blood_glucose = models.IntegerField(blank=True, null=True)
    screening_notes = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='triage/photos/', blank=True, null=True)
    triage_nurse = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='triage_records')
    triage_time = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'triage_records'
        managed = True

    def save(self, *args, **kwargs):
        if not self.queue_number:
            from django.utils import timezone as tz
            today = tz.now().strftime('%Y%m%d')
            prefix = f"Q-{today}-"
            from jfd_hms.utils import generate_sequence_number
            self.queue_number = generate_sequence_number(prefix, TriageRecord, 'queue_number')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.visit.visit_number} - Triage at {self.triage_time}"


class Encounter(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='encounters')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='encounters', null=True, blank=True)
    encounter_type = models.CharField(max_length=20, choices=EncounterType.choices)
    encounter_date = models.DateTimeField(auto_now_add=True)
    provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='encounters')
    department = models.ForeignKey('users_auth.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='encounters')
    location = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=15, choices=OrderStatus.choices, default=OrderStatus.IN_PROGRESS)
    subjective = models.TextField(blank=True, null=True)
    objective = models.TextField(blank=True, null=True)
    assessment = models.TextField(blank=True, null=True)
    plan = models.TextField(blank=True, null=True)
    diagnosis_primary = models.CharField(max_length=100, blank=True, null=True)
    diagnosis_secondary = models.CharField(max_length=100, blank=True, null=True)
    diagnosis_notes = models.TextField(blank=True, null=True)
    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(blank=True, null=True)
    signed_by = models.UUIDField(null=True, blank=True)
    signed_at = models.DateTimeField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'encounters'
        managed = True
        ordering = ['-encounter_date']

    def __str__(self):
        return f"{self.visit.visit_number} - {self.encounter_type} - {self.encounter_date}"


class VitalSigns(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='vital_signs')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='vital_signs', null=True, blank=True)
    encounter = models.ForeignKey(Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name='vital_signs')
    temperature = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    heart_rate = models.IntegerField(blank=True, null=True)
    respiratory_rate = models.IntegerField(blank=True, null=True)
    blood_pressure_systolic = models.IntegerField(blank=True, null=True)
    blood_pressure_diastolic = models.IntegerField(blank=True, null=True)
    oxygen_saturation = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    bmi = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    pain_scale = models.IntegerField(blank=True, null=True)
    blood_glucose = models.IntegerField(blank=True, null=True)
    recorded_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='vital_signs_recorded')
    recorded_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vital_signs'
        managed = True
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.visit.visit_number} - Vitals at {self.recorded_at}"


class Diagnosis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='diagnoses')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='diagnoses', null=True, blank=True)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='diagnoses')
    diagnosis_code = models.CharField(max_length=20, blank=True, null=True)
    diagnosis_code_system = models.CharField(max_length=20, default='ICD-10')
    diagnosis_description = models.TextField()
    diagnosis_type = models.CharField(max_length=20, default='primary')
    is_principal = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='active')
    onset_date = models.DateField(blank=True, null=True)
    resolved_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    coded_by = models.UUIDField(null=True, blank=True)
    coded_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'diagnoses'
        managed = True

    def __str__(self):
        return f"{self.diagnosis_code} - {self.diagnosis_description[:50]}"


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='orders')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    encounter = models.ForeignKey(Encounter, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_type = models.CharField(max_length=50)
    order_description = models.TextField()
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.ROUTINE)
    status = models.CharField(max_length=15, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    ordering_provider = models.ForeignKey('users_auth.User', on_delete=models.CASCADE, related_name='orders')
    ordered_at = models.DateTimeField(auto_now_add=True)
    required_by = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'
        managed = True
        ordering = ['-ordered_at']

    def __str__(self):
        return f"{self.order_type} - {self.visit.visit_number} - {self.status}"


class ProgressNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='progress_notes')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='progress_notes')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='progress_notes')
    note_type = models.CharField(max_length=50, default='progress')
    subjective = models.TextField(blank=True, null=True)
    objective = models.TextField(blank=True, null=True)
    assessment = models.TextField(blank=True, null=True)
    plan = models.TextField(blank=True, null=True)
    note_text = models.TextField()
    author = models.ForeignKey('users_auth.User', on_delete=models.CASCADE, related_name='progress_notes')
    authored_at = models.DateTimeField(auto_now_add=True)
    is_signed = models.BooleanField(default=False)
    signed_at = models.DateTimeField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'progress_notes'
        managed = True
        ordering = ['-authored_at']

    def __str__(self):
        return f"{self.visit.visit_number} - Progress Note - {self.authored_at}"


class NursingNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='nursing_notes')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='nursing_notes')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='nursing_notes')
    note_type = models.CharField(max_length=50, default='nursing')
    note_text = models.TextField()
    interventions = models.TextField(blank=True, null=True)
    patient_response = models.TextField(blank=True, null=True)
    author = models.ForeignKey('users_auth.User', on_delete=models.CASCADE, related_name='nursing_notes')
    authored_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'nursing_notes'
        managed = True
        ordering = ['-authored_at']

    def __str__(self):
        return f"{self.visit.visit_number} - Nursing Note - {self.authored_at}"


class Admission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='admissions')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='admissions')
    admission_number = models.CharField(max_length=20, unique=True, editable=False)
    admission_date = models.DateTimeField(auto_now_add=True)
    admission_type = models.CharField(max_length=50, blank=True, null=True)
    admitting_diagnosis = models.TextField(blank=True, null=True)
    admitting_provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='admissions_as_admitting')
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True, related_name='admissions')
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='admissions')
    bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True, blank=True, related_name='admissions')
    expected_discharge_date = models.DateField(blank=True, null=True)
    actual_discharge_date = models.DateTimeField(blank=True, null=True)
    discharge_type = models.CharField(max_length=30, choices=DischargeStatus.choices, blank=True, null=True)
    discharge_summary = models.TextField(blank=True, null=True)
    discharge_provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='admissions_as_discharging')
    status = models.CharField(max_length=20, choices=AdmissionStatus.choices, default=AdmissionStatus.ACTIVE)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = 'admissions'
        managed = True
        ordering = ['-admission_date']

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_bed = None
        if not is_new:
            try:
                old_bed = Admission.objects.get(pk=self.pk).bed
            except Admission.DoesNotExist:
                pass

        if not self.admission_number:
            from datetime import date
            today = date.today()
            prefix = f"ADM-{today.strftime('%Y%m%d')}-"
            from jfd_hms.utils import generate_sequence_number
            self.admission_number = generate_sequence_number(prefix, Admission, 'admission_number')

        super().save(*args, **kwargs)

        if is_new and self.bed:
            self.bed.is_occupied = True
            self.bed.save(update_fields=['is_occupied'])
        elif old_bed and old_bed != self.bed:
            old_bed.is_occupied = False
            old_bed.save(update_fields=['is_occupied'])
            if self.bed:
                self.bed.is_occupied = True
                self.bed.save(update_fields=['is_occupied'])
        elif not old_bed and self.bed:
            self.bed.is_occupied = True
            self.bed.save(update_fields=['is_occupied'])

    def __str__(self):
        return f"{self.admission_number} - {self.patient.mrn}"


class AdmissionTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admission = models.ForeignKey(Admission, on_delete=models.CASCADE, related_name='transfers')
    from_ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_from')
    from_room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_from')
    from_bed = models.ForeignKey(Bed, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_from')
    to_ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name='transfers_to')
    to_room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='transfers_to')
    to_bed = models.ForeignKey(Bed, on_delete=models.CASCADE, related_name='transfers_to')
    transfer_reason = models.TextField(blank=True, null=True)
    transferred_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers')
    transferred_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admission_transfers'
        managed = True
        ordering = ['-transferred_at']

    def __str__(self):
        return f"Transfer for {self.admission.admission_number} - {self.transferred_at}"


class LabTestCatalogue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    specimen_type = models.CharField(max_length=50, blank=True, null=True)
    turnaround_time = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lab_test_catalogue'
        managed = True
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class RadiologyTestCatalogue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    body_part = models.CharField(max_length=100, blank=True, null=True)
    modality = models.CharField(max_length=50, blank=True, null=True)
    turnaround_time = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'radiology_test_catalogue'
        managed = True
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class DiagnosticResult(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_verification', 'Pending Verification'),
        ('verified', 'Verified'),
        ('published', 'Published'),
        ('rejected', 'Rejected'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='diagnostic_results')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='diagnostic_results')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='diagnostic_results')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='draft')
    result_text = models.TextField(blank=True, null=True)
    result_file_url = models.CharField(max_length=500, blank=True, null=True)
    is_abnormal = models.BooleanField(default=False)
    critical_flag = models.BooleanField(default=False)
    entered_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='entered_results')
    verified_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_results')
    verified_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'diagnostic_results'
        managed = True
        ordering = ['-created_at']

    def __str__(self):
        return f"Result for {self.order.order_type} - {self.visit.visit_number}"


class CriticalResultNotification(models.Model):
    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('urgent', 'Urgent'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    result = models.ForeignKey(DiagnosticResult, on_delete=models.CASCADE, related_name='notifications')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='critical_notifications')
    notification_type = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='critical')
    message = models.TextField()
    notified_to = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='critical_notifications_received')
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='critical_notifications_acknowledged')
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'critical_result_notifications'
        managed = True
        ordering = ['-created_at']

    def __str__(self):
        return f"Critical: {self.result.order.order_type} for {self.patient.mrn}"


class Specimen(models.Model):
    STATUS_CHOICES = [
        ('collected', 'Collected'),
        ('in_transit', 'In Transit'),
        ('received', 'Received in Lab'),
        ('analyzing', 'Analyzing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    specimen_number = models.CharField(max_length=30, unique=True, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='specimens')
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='specimens')
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name='specimens')
    specimen_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='collected')
    collection_datetime = models.DateTimeField()
    collected_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='specimens_collected')
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    storage_location = models.CharField(max_length=200, blank=True, null=True)
    received_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='specimens_received')
    received_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'specimens'
        managed = True
        ordering = ['-collection_datetime']

    def save(self, *args, **kwargs):
        if not self.specimen_number:
            from datetime import date
            today = date.today()
            prefix = f"SPM-{today.strftime('%Y%m%d')}-"
            last = Specimen.objects.filter(
                specimen_number__startswith=prefix
            ).order_by('-specimen_number').first()
            if last:
                seq = int(last.specimen_number.split('-')[-1]) + 1
            else:
                seq = 1
            self.specimen_number = f"{prefix}{seq:05d}"
        if not self.barcode:
            import hashlib
            raw = f"{self.specimen_number}-{self.patient_id}-{timezone.now().isoformat()}"
            self.barcode = hashlib.md5(raw.encode()).hexdigest()[:12].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.specimen_number} - {self.specimen_type} ({self.status})"


class PatientMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='movements')
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements')
    admission = models.ForeignKey(Admission, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements')
    movement_type = models.CharField(max_length=50)
    from_location = models.CharField(max_length=200, blank=True, null=True)
    to_location = models.CharField(max_length=200, blank=True, null=True)
    movement_time = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True, null=True)
    recorded_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_recorded')
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'patient_movements'
        managed = True
        ordering = ['-movement_time']

    def __str__(self):
        return f"{self.patient.mrn} - {self.movement_type} - {self.movement_time}"


class AntenatalVisit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='antenatal_visits')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='antenatal_visits', null=True, blank=True)
    admission = models.ForeignKey('Admission', on_delete=models.SET_NULL, null=True, blank=True, related_name='antenatal_visits')
    visit_number = models.CharField(max_length=20, editable=False)
    lmp_date = models.DateField(help_text='Last Menstrual Period')
    edd_date = models.DateField(help_text='Expected Date of Delivery')
    ga_weeks = models.IntegerField(help_text='Gestational Age in weeks')
    gravida = models.IntegerField(default=1)
    parity = models.IntegerField(default=0)
    previous_c_section = models.BooleanField(default=False)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    hemoglobin = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    blood_pressure_systolic = models.IntegerField(blank=True, null=True)
    blood_pressure_diastolic = models.IntegerField(blank=True, null=True)
    weight = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    fundal_height = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    fetal_heart_rate = models.IntegerField(blank=True, null=True)
    presentation = models.CharField(max_length=50, blank=True, null=True)
    hiv_status = models.CharField(max_length=20, blank=True, null=True)
    syphilis_status = models.CharField(max_length=20, blank=True, null=True)
    hepatitis_b_status = models.CharField(max_length=20, blank=True, null=True)
    urine_protein = models.CharField(max_length=10, blank=True, null=True)
    urine_glucose = models.CharField(max_length=10, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    next_visit_date = models.DateField(blank=True, null=True)
    provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='antenatal_visits')
    status = models.CharField(max_length=20, default='active')
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'antenatal_visits'
        managed = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.mrn} - ANC Visit {self.visit_number} (GA {self.ga_weeks}w)"

    def save(self, *args, **kwargs):
        if not self.visit_number:
            prefix = f"ANC-{timezone.now().strftime('%Y%m%d')}-"
            count = AntenatalVisit.objects.filter(visit_number__startswith=prefix).count()
            self.visit_number = f"{prefix}{count + 1:04d}"
        super().save(*args, **kwargs)


class LaborRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='labor_records')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='labor_records', null=True, blank=True)
    antenatal_visit = models.ForeignKey(AntenatalVisit, on_delete=models.SET_NULL, null=True, blank=True, related_name='labor_records')
    labor_number = models.CharField(max_length=20, editable=False)
    admission_time = models.DateTimeField()
    membrane_rupture_time = models.DateTimeField(blank=True, null=True)
    membrane_rupture_type = models.CharField(max_length=30, blank=True, null=True, choices=[
        ('spontaneous', 'Spontaneous'),
        ('artificial', 'Artificial'),
        ('intact', 'Intact'),
    ])
    cervical_dilation = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    labor_progress_notes = models.TextField(blank=True, null=True)
    fetal_heart_rate = models.IntegerField(blank=True, null=True)
    contraction_frequency = models.CharField(max_length=50, blank=True, null=True)
    presentation = models.CharField(max_length=50, blank=True, null=True)
    provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='labor_records')
    status = models.CharField(max_length=20, default='in_progress', choices=[
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
    ])
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'labor_records'
        managed = True
        ordering = ['-admission_time']

    def __str__(self):
        return f"{self.patient.mrn} - Labor {self.labor_number}"

    def save(self, *args, **kwargs):
        if not self.labor_number:
            prefix = f"LBR-{timezone.now().strftime('%Y%m%d')}-"
            count = LaborRecord.objects.filter(labor_number__startswith=prefix).count()
            self.labor_number = f"{prefix}{count + 1:04d}"
        super().save(*args, **kwargs)


class DeliveryRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    labor_record = models.ForeignKey(LaborRecord, on_delete=models.CASCADE, related_name='deliveries')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='delivery_records')
    delivery_time = models.DateTimeField()
    delivery_method = models.CharField(max_length=30, choices=[
        ('vaginal', 'Vaginal'),
        ('vacuum', 'Vacuum Assisted'),
        ('forceps', 'Forceps Assisted'),
        ('c_section', 'Caesarean Section'),
    ])
    delivery_number = models.CharField(max_length=20, editable=False)
    placenta_delivery_time = models.DateTimeField(blank=True, null=True)
    placenta_condition = models.CharField(max_length=30, blank=True, null=True)
    blood_loss_ml = models.IntegerField(blank=True, null=True)
    perineal_tear = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('none', 'None'),
        ('first_degree', 'First Degree'),
        ('second_degree', 'Second Degree'),
        ('third_degree', 'Third Degree'),
        ('fourth_degree', 'Fourth Degree'),
    ])
    episiotomy = models.BooleanField(default=False)
    oxytocin_given = models.BooleanField(default=False)
    medication_given = models.TextField(blank=True, null=True)
    complications = models.TextField(blank=True, null=True)
    provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_records')
    notes = models.TextField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'delivery_records'
        managed = True
        ordering = ['-delivery_time']

    def __str__(self):
        return f"{self.patient.mrn} - Delivery {self.delivery_number}"

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            prefix = f"DLV-{timezone.now().strftime('%Y%m%d')}-"
            count = DeliveryRecord.objects.filter(delivery_number__startswith=prefix).count()
            self.delivery_number = f"{prefix}{count + 1:04d}"
        super().save(*args, **kwargs)


class BirthRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_record = models.ForeignKey(DeliveryRecord, on_delete=models.CASCADE, related_name='birth_records')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='birth_records')
    birth_number = models.CharField(max_length=20, editable=False)
    baby_name = models.CharField(max_length=200, blank=True, null=True)
    sex = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    birth_weight_grams = models.IntegerField()
    birth_length_cm = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    apgar_score_1min = models.IntegerField(blank=True, null=True)
    apgar_score_5min = models.IntegerField(blank=True, null=True)
    apgar_score_10min = models.IntegerField(blank=True, null=True)
    cry_at_birth = models.BooleanField(default=True)
    congenital_anomalies = models.TextField(blank=True, null=True)
    feeding_method = models.CharField(max_length=30, blank=True, null=True, choices=[
        ('breast', 'Breastfeeding'),
        ('formula', 'Formula'),
        ('mixed', 'Mixed'),
        ('none', 'Not Feeding'),
    ])
    vitamin_k_given = models.BooleanField(default=False)
    eye_prophylaxis_given = models.BooleanField(default=False)
    hepatitis_b_vaccine_given = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='alive', choices=[
        ('alive', 'Alive'),
        ('stillbirth', 'Stillbirth'),
        ('neonatal_death', 'Neonatal Death'),
    ])
    notes = models.TextField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'birth_records'
        managed = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.birth_number} - {self.baby_name or 'Baby'} ({self.sex})"

    def save(self, *args, **kwargs):
        if not self.birth_number:
            prefix = f"BR-{timezone.now().strftime('%Y%m%d')}-"
            count = BirthRecord.objects.filter(birth_number__startswith=prefix).count()
            self.birth_number = f"{prefix}{count + 1:04d}"
        super().save(*args, **kwargs)


class PostnatalVisit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='postnatal_visits')
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='postnatal_visits', null=True, blank=True)
    delivery_record = models.ForeignKey(DeliveryRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='postnatal_visits')
    visit_number = models.CharField(max_length=20, editable=False)
    visit_day_postpartum = models.IntegerField(help_text='Days postpartum')
    blood_pressure_systolic = models.IntegerField(blank=True, null=True)
    blood_pressure_diastolic = models.IntegerField(blank=True, null=True)
    temperature = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    fundal_height = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    lochia_assessment = models.CharField(max_length=30, blank=True, null=True)
    perineal_assessment = models.TextField(blank=True, null=True)
    breast_assessment = models.TextField(blank=True, null=True)
    baby_weight_grams = models.IntegerField(blank=True, null=True)
    baby_condition = models.TextField(blank=True, null=True)
    feeding_method = models.CharField(max_length=30, blank=True, null=True)
    family_planning_counseling = models.BooleanField(default=False)
    family_planning_method = models.CharField(max_length=50, blank=True, null=True)
    hemoglobin = models.DecimalField(max_digits=4, decimal_places=1, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='postnatal_visits')
    next_visit_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, default='active')
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'postnatal_visits'
        managed = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.mrn} - PNC Visit {self.visit_number} (Day {self.visit_day_postpartum})"

    def save(self, *args, **kwargs):
        if not self.visit_number:
            prefix = f"PNC-{timezone.now().strftime('%Y%m%d')}-"
            count = PostnatalVisit.objects.filter(visit_number__startswith=prefix).count()
            self.visit_number = f"{prefix}{count + 1:04d}"
        super().save(*args, **kwargs)


class SurgicalCase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='surgical_cases')
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name='surgical_cases')
    admission = models.ForeignKey('Admission', on_delete=models.SET_NULL, null=True, blank=True, related_name='surgical_cases')
    case_number = models.CharField(max_length=20, editable=False)
    procedure_name = models.CharField(max_length=300)
    procedure_code = models.CharField(max_length=50, blank=True, null=True)
    procedure_description = models.TextField(blank=True, null=True)
    surgical_site = models.CharField(max_length=100, blank=True, null=True)
    laterality = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('left', 'Left'), ('right', 'Right'), ('bilateral', 'Bilateral'), ('midline', 'Midline'), ('na', 'N/A'),
    ])
    priority = models.CharField(max_length=20, default='elective', choices=[
        ('elective', 'Elective'), ('urgent', 'Urgent'), ('emergency', 'Emergency'),
    ])
    scheduled_date = models.DateTimeField(blank=True, null=True)
    surgeon = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='surgical_cases_as_surgeon')
    anesthesia_type = models.CharField(max_length=30, blank=True, null=True, choices=[
        ('general', 'General'), ('spinal', 'Spinal'), ('epidural', 'Epidural'),
        ('regional', 'Regional'), ('local', 'Local'), ('sedation', 'Sedation'),
    ])
    asa_class = models.CharField(max_length=5, blank=True, null=True)
    status = models.CharField(max_length=20, default='scheduled', choices=[
        ('scheduled', 'Scheduled'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('cancelled', 'Cancelled'),
    ])
    pre_op_diagnosis = models.TextField(blank=True, null=True)
    post_op_diagnosis = models.TextField(blank=True, null=True)
    complications = models.TextField(blank=True, null=True)
    specimen_sent = models.BooleanField(default=False)
    specimen_description = models.TextField(blank=True, null=True)
    estimated_blood_loss_ml = models.IntegerField(blank=True, null=True)
    duration_minutes = models.IntegerField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'surgical_cases'
        managed = True
        ordering = ['-scheduled_date']

    def __str__(self):
        return f"{self.case_number} - {self.procedure_name}"

    def save(self, *args, **kwargs):
        if not self.case_number:
            prefix = f"SG-{timezone.now().strftime('%Y%m%d')}-"
            count = SurgicalCase.objects.filter(case_number__startswith=prefix).count()
            self.case_number = f"{prefix}{count + 1:04d}"
        super().save(*args, **kwargs)


class Referral(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='referrals')
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    referral_number = models.CharField(max_length=20, editable=False)
    referral_type = models.CharField(max_length=20, choices=[
        ('internal', 'Internal'), ('external', 'External'),
    ])
    referral_date = models.DateTimeField(auto_now_add=True)
    referring_provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals_made')
    referring_department = models.ForeignKey('users_auth.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals_from')
    receiving_provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals_received')
    receiving_department = models.ForeignKey('users_auth.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals_to')
    receiving_facility = models.CharField(max_length=200, blank=True, null=True)
    clinical_reason = models.TextField()
    urgency = models.CharField(max_length=20, default='routine', choices=[
        ('routine', 'Routine'), ('urgent', 'Urgent'), ('emergency', 'Emergency'),
    ])
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'),
        ('completed', 'Completed'), ('cancelled', 'Cancelled'),
    ])
    acceptance_notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    transfer_notes = models.TextField(blank=True, null=True)
    referral_letter_url = models.CharField(max_length=500, blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'referrals'
        managed = True
        ordering = ['-referral_date']

    def __str__(self):
        return f"{self.referral_number} - {self.patient.mrn}"

    def save(self, *args, **kwargs):
        if not self.referral_number:
            prefix = f"REF-{timezone.now().strftime('%Y%m%d')}-"
            count = Referral.objects.filter(referral_number__startswith=prefix).count()
            self.referral_number = f"{prefix}{count + 1:04d}"
        super().save(*args, **kwargs)


class Appointment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='appointments')
    appointment_number = models.CharField(max_length=20, editable=False)
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    duration_minutes = models.IntegerField(default=30)
    appointment_type = models.CharField(max_length=30, choices=[
        ('consultation', 'Consultation'),
        ('follow_up', 'Follow-up'),
        ('procedure', 'Procedure'),
        ('lab_only', 'Lab Only'),
        ('imaging', 'Imaging'),
        ('vaccination', 'Vaccination'),
        ('antenatal', 'Antenatal'),
        ('postnatal', 'Postnatal'),
    ])
    department = models.ForeignKey('users_auth.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    provider = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='appointments')
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, default='scheduled', choices=[
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('rescheduled', 'Rescheduled'),
    ])
    notes = models.TextField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)
    linked_visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name='linked_appointments')
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name='appointment_visits')
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'appointments'
        managed = True
        ordering = ['appointment_date', 'appointment_time']

    def __str__(self):
        return f"{self.appointment_number} - {self.patient.mrn} on {self.appointment_date}"

    def save(self, *args, **kwargs):
        if not self.appointment_number:
            prefix = f"APT-{timezone.now().strftime('%Y%m%d')}-"
            count = Appointment.objects.filter(appointment_number__startswith=prefix).count()
            self.appointment_number = f"{prefix}{count + 1:04d}"
        super().save(*args, **kwargs)


class ERNurseEvaluation(models.Model):
    class ModeOfArrival(models.TextChoices):
        WALK_IN = 'walk_in', 'Walk-in'
        AMBULANCE = 'ambulance', 'Ambulance'
        REFERRED = 'referred', 'Referred'
        PRIVATE = 'private_vehicle', 'Private Vehicle'

    class AccompaniedBy(models.TextChoices):
        PARENT = 'parent', 'Parent'
        GUARDIAN = 'guardian', 'Guardian'
        LAW_ENFORCEMENT = 'law_enforcement', 'Law Enforcement'
        SOCIAL_WORKER = 'social_worker', 'Social Worker'
        FAMILY = 'family', 'Family Member'

    class TriageCategory(models.TextChoices):
        RED = 'red', 'RED'
        YELLOW = 'yellow', 'YELLOW'
        GREEN = 'green', 'GREEN'
        BLACK = 'black', 'BLACK'

    class DispositionChoice(models.TextChoices):
        ADMITTED = 'admitted', 'Admitted'
        DISCHARGED = 'discharged', 'Discharged'
        AMA = 'ama', 'AMA'
        REFERRED = 'referred', 'Referred'
        DECEASED = 'deceased', 'Deceased'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='er_evaluations')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='er_evaluations')

    mode_of_arrival = models.CharField(max_length=20, choices=ModeOfArrival.choices, blank=True)
    accompanied_by = models.CharField(max_length=20, choices=AccompaniedBy.choices, blank=True)

    chief_complaint = models.TextField()

    hpi_onset = models.CharField(max_length=200, blank=True)
    hpi_location = models.CharField(max_length=200, blank=True)
    hpi_character = models.CharField(max_length=200, blank=True)
    hpi_severity = models.CharField(max_length=50, blank=True)
    hpi_aggravating = models.CharField(max_length=200, blank=True)
    hpi_alleviating = models.CharField(max_length=200, blank=True)

    pmh_chronic_illness = models.CharField(max_length=200, blank=True)
    pmh_previous_surgery = models.CharField(max_length=200, blank=True)
    pmh_allergies = models.CharField(max_length=200, blank=True)
    pmh_medications = models.CharField(max_length=200, blank=True)

    ros_fever = models.BooleanField(default=False)
    ros_chest_pain = models.BooleanField(default=False)
    ros_cough = models.BooleanField(default=False)
    ros_wheeze = models.BooleanField(default=False)
    ros_bleeding = models.BooleanField(default=False)
    ros_shortness_of_breath = models.BooleanField(default=False)
    ros_vomiting = models.BooleanField(default=False)
    ros_rash = models.BooleanField(default=False)
    ros_diarrhea = models.BooleanField(default=False)
    ros_abdominal_pain = models.BooleanField(default=False)
    ros_trauma = models.BooleanField(default=False)

    bp_systolic = models.IntegerField(null=True, blank=True)
    bp_diastolic = models.IntegerField(null=True, blank=True)
    heart_rate = models.IntegerField(null=True, blank=True)
    sp_o2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)

    exam_heent = models.TextField(blank=True)
    exam_cvs = models.TextField(blank=True)
    exam_respiratory = models.TextField(blank=True)
    exam_abdomen = models.TextField(blank=True)
    exam_gus = models.TextField(blank=True)
    exam_musculoskeletal = models.TextField(blank=True)
    exam_cns = models.TextField(blank=True)

    triage_category = models.CharField(max_length=10, choices=TriageCategory.choices, blank=True)

    intervention_oxygen = models.BooleanField(default=False)
    intervention_iv_fluids = models.BooleanField(default=False)
    intervention_blood_transfusion = models.BooleanField(default=False)
    intervention_analgesics = models.BooleanField(default=False)
    intervention_suturing = models.BooleanField(default=False)
    intervention_antibiotics = models.BooleanField(default=False)
    intervention_antipyretics = models.BooleanField(default=False)
    intervention_specimen_collection = models.BooleanField(default=False)
    intervention_collect_results = models.BooleanField(default=False)

    physician_notified = models.BooleanField(default=False)
    physician_notified_time = models.TimeField(null=True, blank=True)
    physician_arrival_time = models.TimeField(null=True, blank=True)
    physicians_order = models.TextField(blank=True)
    pending_orders = models.TextField(blank=True)
    disposition = models.CharField(max_length=20, choices=DispositionChoice.choices, blank=True)
    remarks = models.TextField(blank=True)

    completed_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, related_name='er_evaluations')
    completed_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'er_nurse_evaluations'
        managed = True
        ordering = ['-completed_at']

    def __str__(self):
        return f"ER Eval: {self.patient.mrn} - {self.completed_at}"


class PediatricAssessment(models.Model):
    class VisitType(models.TextChoices):
        FIRST = 'first', 'First Visit'
        REPEAT = 'repeat', 'Repeat Visit'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.ForeignKey(Visit, on_delete=models.CASCADE, related_name='pediatric_assessments', null=True, blank=True)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='pediatric_assessments')

    visit_type = models.CharField(max_length=10, choices=VisitType.choices, blank=True)
    card_number = models.CharField(max_length=50, blank=True)
    child_problem = models.TextField(blank=True)

    pulse = models.IntegerField(null=True, blank=True)
    respiratory_rate = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    bp = models.CharField(max_length=20, blank=True)
    sao2 = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    head_circumference = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    lethargy_unconscious = models.BooleanField(default=False)
    convulsing_now = models.BooleanField(default=False)
    not_able_to_drink = models.BooleanField(default=False)
    vomits_everything = models.BooleanField(default=False)
    history_of_convulsion = models.BooleanField(default=False)

    has_diarrhea = models.BooleanField(default=False)
    blood_in_stool = models.BooleanField(default=False)
    dehydration_signs = models.BooleanField(default=False)
    dehydration_lethargy = models.BooleanField(default=False)
    sunken_eyes = models.BooleanField(default=False)
    delayed_capillary_refill = models.BooleanField(default=False)
    poor_skin_turgor = models.BooleanField(default=False)
    decreased_urine = models.BooleanField(default=False)

    cough_breath_difficulty = models.BooleanField(default=False)
    severe_respiratory_distress = models.BooleanField(default=False)
    audible_stridor = models.BooleanField(default=False)
    central_cyanosis = models.BooleanField(default=False)

    severe_pallor = models.BooleanField(default=False)
    fever_present = models.BooleanField(default=False)
    shock_present = models.BooleanField(default=False)
    cold_hands = models.BooleanField(default=False)
    shock_delayed_capillary_refill = models.BooleanField(default=False)
    rapid_weak_pulse = models.BooleanField(default=False)
    altered_mental_status = models.BooleanField(default=False)
    edema_both_feet = models.BooleanField(default=False)

    muac = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    wt_ht = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    heent_notes = models.TextField(blank=True)
    chest_notes = models.TextField(blank=True)
    cvs_notes = models.TextField(blank=True)
    abdomen_notes = models.TextField(blank=True)
    gu_notes = models.TextField(blank=True)
    musculoskeletal_notes = models.TextField(blank=True)
    integumentary_notes = models.TextField(blank=True)
    cns_notes = models.TextField(blank=True)
    sleeping_under_net = models.BooleanField(null=True, blank=True)

    laboratory_investigation = models.TextField(blank=True)
    provisional_diagnosis = models.TextField(blank=True)
    treatment = models.TextField(blank=True)

    vaccination_bcg = models.BooleanField(default=False)
    vaccination_opv_0 = models.BooleanField(default=False)
    vaccination_opv_1 = models.BooleanField(default=False)
    vaccination_opv_2 = models.BooleanField(default=False)
    vaccination_opv_3 = models.BooleanField(default=False)
    vaccination_penta_1 = models.BooleanField(default=False)
    vaccination_penta_2 = models.BooleanField(default=False)
    vaccination_penta_3 = models.BooleanField(default=False)
    vaccination_pcv_1 = models.BooleanField(default=False)
    vaccination_pcv_2 = models.BooleanField(default=False)
    vaccination_pcv_3 = models.BooleanField(default=False)
    vaccination_rota_1 = models.BooleanField(default=False)
    vaccination_rota_2 = models.BooleanField(default=False)
    vaccination_rota_3 = models.BooleanField(default=False)
    vaccination_measles = models.BooleanField(default=False)
    vaccination_yellow_fever = models.BooleanField(default=False)

    follow_up_notes = models.TextField(blank=True)
    discharge_diagnosis = models.TextField(blank=True)
    discharge_treatment_course = models.TextField(blank=True)
    counselling_danger_signs = models.BooleanField(default=False)
    counselling_nutrition = models.BooleanField(default=False)
    counselling_medication = models.BooleanField(default=False)
    counselling_follow_up = models.BooleanField(default=False)
    counselling_other = models.TextField(blank=True)

    completed_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, related_name='pediatric_assessments')
    completed_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pediatric_assessments'
        managed = True
        ordering = ['-completed_at']

    def __str__(self):
        return f"Pediatric: {self.patient.mrn} - {self.completed_at}"


class TriageCriteria(models.Model):
    """Admin-configurable triage acuity rules based on vital sign thresholds."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, help_text='Rule name, e.g. "Severe Hypotension"')
    vital_sign = models.CharField(max_length=30, choices=[
        ('temperature', 'Temperature'),
        ('heart_rate', 'Heart Rate'),
        ('respiratory_rate', 'Respiratory Rate'),
        ('blood_pressure_systolic', 'Systolic BP'),
        ('blood_pressure_diastolic', 'Diastolic BP'),
        ('oxygen_saturation', 'SpO2'),
        ('pain_scale', 'Pain Scale'),
        ('blood_glucose', 'Blood Glucose'),
    ])
    operator = models.CharField(max_length=10, choices=[
        ('lt', '<'),
        ('lte', '<='),
        ('gt', '>'),
        ('gte', '>='),
        ('eq', '='),
        ('between', 'Between'),
    ])
    threshold_low = models.DecimalField(max_digits=8, decimal_places=2, help_text='Primary threshold value')
    threshold_high = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text='Upper bound for "between" operator')
    suggested_acuity = models.IntegerField(choices=[(1, 'Resuscitation'), (2, 'Emergent'), (3, 'Urgent'), (4, 'Less Urgent'), (5, 'Non-Urgent')])
    suggested_department = models.CharField(max_length=20, choices=[
        ('ER', 'Emergency Room'),
        ('OPD', 'Outpatient Department'),
        ('IPD', 'Inpatient Department'),
        ('OBGYN', 'Obstetrics & Gynecology'),
    ], default='OPD')
    priority = models.IntegerField(default=100, help_text='Evaluation order (lower = checked first)')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'triage_criteria'
        managed = True
        ordering = ['priority', 'vital_sign']

    def __str__(self):
        return f"{self.name} ({self.get_vital_sign_display()} {self.get_operator_display()} {self.threshold_low})"


class WorkflowTransition(models.Model):
    """Audit trail for patient workflow state transitions."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.SET_NULL, null=True, blank=True, related_name='workflow_transitions')
    visit = models.ForeignKey(Visit, on_delete=models.SET_NULL, null=True, blank=True, related_name='workflow_transitions')
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    from_department = models.ForeignKey('users_auth.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='transitions_from')
    to_department = models.ForeignKey('users_auth.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='transitions_to')
    triggered_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='workflow_transitions')
    trigger_action = models.CharField(max_length=50, help_text='e.g. triage_submit, er_bypass, opd_to_er, admit_to_ipd')
    metadata = models.JSONField(blank=True, null=True, help_text='Stores override reasons, routing decisions, etc.')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workflow_transitions'
        managed = True
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.trigger_action}: {self.from_status} -> {self.to_status} at {self.created_at}"
