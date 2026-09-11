import uuid
from django.db import models


class SyncStatus(models.TextChoices):
    LOCAL = 'local', 'Local'
    SYNCED = 'synced', 'Synced'


class OrderStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    IN_PROGRESS = 'in_progress', 'In Progress'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'
    FAILED = 'failed', 'Failed'


class Medication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    brand_name = models.CharField(max_length=200, blank=True, null=True)
    medication_code = models.CharField(max_length=50, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    dosage_form = models.CharField(max_length=50, blank=True, null=True)
    strength = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=50, blank=True, null=True)
    route = models.CharField(max_length=50, blank=True, null=True)
    manufacturer = models.CharField(max_length=200, blank=True, null=True)
    is_controlled = models.BooleanField(default=False)
    controlled_schedule = models.IntegerField(blank=True, null=True)
    requires_prescription = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'medications'
        managed = True
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.strength}"


class Prescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    visit = models.ForeignKey('clinical.Visit', on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='prescriptions')
    encounter = models.ForeignKey('clinical.Encounter', on_delete=models.SET_NULL, null=True, blank=True, related_name='prescriptions')
    prescription_number = models.CharField(max_length=20, unique=True, editable=False)
    prescribed_by = models.ForeignKey('users_auth.User', on_delete=models.CASCADE, related_name='prescriptions')
    prescribed_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    notes = models.TextField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prescriptions'
        managed = True
        ordering = ['-prescribed_at']

    def save(self, *args, **kwargs):
        if not self.prescription_number:
            from datetime import date
            today = date.today()
            prefix = f"RX-{today.strftime('%Y%m%d')}-"
            from jfd_hms.utils import generate_sequence_number
            self.prescription_number = generate_sequence_number(prefix, Prescription, 'prescription_number')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.prescription_number} - {self.patient.mrn}"


class PrescriptionItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='prescription_items')
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=100)
    duration = models.CharField(max_length=100, blank=True, null=True)
    quantity_prescribed = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_dispensed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    route = models.CharField(max_length=50, blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    refills_allowed = models.IntegerField(default=0)
    refills_used = models.IntegerField(default=0)
    status = models.CharField(max_length=15, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    dispensed_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='dispensed_items')
    dispensed_at = models.DateTimeField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'prescription_items'
        managed = True
        ordering = ['medication__name']

    def __str__(self):
        return f"{self.medication.name} - {self.dosage}"


class MedicationDispensing(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.CASCADE, related_name='dispensing_records')
    medication = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='dispensing_records')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='dispensing_records')
    quantity_dispensed = models.DecimalField(max_digits=10, decimal_places=2)
    batch_lot_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    inventory_stock = models.ForeignKey('inventory.Stock', on_delete=models.SET_NULL, null=True, blank=True, related_name='dispensing_records')
    dispensed_by = models.ForeignKey('users_auth.User', on_delete=models.CASCADE, related_name='dispensing_records')
    dispensed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'medication_dispensing'
        managed = True
        ordering = ['-dispensed_at']

    def __str__(self):
        return f"{self.medication.name} - {self.quantity_dispensed} dispensed"


class DrugInteraction(models.Model):
    SEVERITY_CHOICES = [
        ('severe', 'Severe - Avoid combination'),
        ('moderate', 'Moderate - Monitor closely'),
        ('mild', 'Mild - Be aware'),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drug_a = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='interactions_as_a')
    drug_b = models.ForeignKey(Medication, on_delete=models.CASCADE, related_name='interactions_as_b')
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    description = models.TextField()
    recommendation = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'drug_interactions'
        managed = True
        unique_together = ['drug_a', 'drug_b']

    def __str__(self):
        return f"{self.drug_a.name} + {self.drug_b.name} ({self.severity})"
