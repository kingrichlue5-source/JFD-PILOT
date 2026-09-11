import uuid
from django.db import models


class SyncStatus(models.TextChoices):
    LOCAL = 'local', 'Local'
    SYNCED = 'synced', 'Synced'


class PaymentMethod(models.TextChoices):
    CASH = 'cash', 'Cash'
    BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
    MOBILE_MONEY = 'mobile_money', 'Mobile Money'
    INSURANCE = 'insurance', 'Insurance'
    CREDIT = 'credit', 'Credit'
    OTHER = 'other', 'Other'


class PriceList(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    effective_date = models.DateField(blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'price_lists'
        managed = True

    def __str__(self):
        return f"{self.code} - {self.name}"


class ServiceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    subcategory = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50, blank=True, null=True)
    is_billable = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_items'
        managed = True

    def __str__(self):
        return f"{self.code} - {self.name}"


class ServicePrice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    service_item = models.ForeignKey(ServiceItem, on_delete=models.CASCADE, related_name='prices')
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name='prices')
    price = models.DecimalField(max_digits=12, decimal_places=2)
    payer_category = models.CharField(max_length=50, blank=True, null=True)
    effective_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_prices'
        managed = True
        unique_together = ('service_item', 'price_list', 'payer_category', 'effective_date')

    def __str__(self):
        return f"{self.service_item.name} - {self.price}"


class PaymentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PARTIAL = 'partial', 'Partial'
    PAID = 'paid', 'Paid'
    WAIVED = 'waived', 'Waived'
    REFUNDED = 'refunded', 'Refunded'
    VOIDED = 'voided', 'Voided'


class Invoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='invoices')
    visit = models.ForeignKey('clinical.Visit', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    admission = models.ForeignKey('clinical.Admission', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    invoice_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payer_type = models.CharField(max_length=50, blank=True, null=True)
    insurance_authorization_number = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'invoices'
        managed = True
        ordering = ['-invoice_date', '-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.patient.mrn}"


class InvoiceLineItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='line_items')
    service_item = models.ForeignKey(ServiceItem, on_delete=models.CASCADE, related_name='line_items')
    description = models.CharField(max_length=200, blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    order = models.ForeignKey('clinical.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='line_items')
    prescription_item = models.ForeignKey('pharmacy.PrescriptionItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='line_items')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'invoice_line_items'
        managed = True
        ordering = ['created_at']

    def __str__(self):
        return f"{self.service_item.name} - {self.total_amount}"


class Payment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_number = models.CharField(max_length=20, unique=True, editable=False)
    receipt_number = models.CharField(max_length=20, unique=True, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    payment_date = models.DateTimeField(auto_now_add=True)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    check_number = models.CharField(max_length=50, blank=True, null=True)
    mobile_money_number = models.CharField(max_length=50, blank=True, null=True)
    insurance_claim_number = models.CharField(max_length=100, blank=True, null=True)
    cashier_shift = models.ForeignKey('CashierShift', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    notes = models.TextField(blank=True, null=True)
    received_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.payment_number:
            from datetime import date
            today = date.today()
            prefix = f"PAY-{today.strftime('%Y%m%d')}-"
            from jfd_hms.utils import generate_sequence_number
            self.payment_number = generate_sequence_number(prefix, Payment, 'payment_number')
        if not self.receipt_number:
            from .services import generate_receipt_number
            self.receipt_number = generate_receipt_number()
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'payments'
        managed = True
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.payment_number} - {self.amount}"


class Refund(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    refund_number = models.CharField(max_length=20, unique=True, editable=False)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='refunds')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='refunds')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    refund_method = models.CharField(max_length=20, choices=PaymentMethod.choices, blank=True, null=True)
    refund_date = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='refunds_approved')
    approved_at = models.DateTimeField(blank=True, null=True)
    processed_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='refunds_processed')
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'refunds'
        managed = True
        ordering = ['-refund_date']

    def __str__(self):
        return f"{self.refund_number} - {self.amount}"


class CreditAdjustment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    adjustment_number = models.CharField(max_length=20, unique=True, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='adjustments')
    patient = models.ForeignKey('patients.Patient', on_delete=models.CASCADE, related_name='adjustments')
    adjustment_type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField()
    adjusted_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='adjustments_made')
    approved_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='adjustments_approved')
    adjusted_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'credit_adjustments'
        managed = True
        ordering = ['-adjusted_at']

    def __str__(self):
        return f"{self.adjustment_number} - {self.adjustment_type} - {self.amount}"


class CashierShift(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shift_number = models.CharField(max_length=20, unique=True, editable=False)
    cashier = models.ForeignKey('users_auth.User', on_delete=models.CASCADE, related_name='cashier_shifts')
    shift_start = models.DateTimeField(auto_now_add=True)
    shift_end = models.DateTimeField(blank=True, null=True)
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closing_balance = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_mobile_money = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_bank_transfer = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_insurance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default='open')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cashier_shifts'
        managed = True
        ordering = ['-shift_start']

    def save(self, *args, **kwargs):
        if not self.shift_number:
            from django.utils import timezone
            today = timezone.localdate().strftime('%Y%m%d')
            prefix = f"SH-{today}-"
            from jfd_hms.utils import generate_sequence_number
            self.shift_number = generate_sequence_number(prefix, CashierShift, 'shift_number')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Shift {self.shift_number} - {self.cashier.username}"
