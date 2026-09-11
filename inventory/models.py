import uuid
from django.db import models


class SyncStatus(models.TextChoices):
    LOCAL = 'local', 'Local'
    SYNCED = 'synced', 'Synced'


class StockMovementType(models.TextChoices):
    RECEIPT = 'receipt', 'Receipt'
    ISSUE = 'issue', 'Issue'
    TRANSFER = 'transfer', 'Transfer'
    ADJUSTMENT = 'adjustment', 'Adjustment'
    RETURN = 'return', 'Return'
    DISPENSED = 'dispensed', 'Dispensed'
    EXPIRED = 'expired', 'Expired'
    DAMAGED = 'damaged', 'Damaged'


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    parent_category = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subcategories')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        managed = True
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Item(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    description = models.TextField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50)
    item_type = models.CharField(max_length=50, blank=True, null=True)
    is_medication = models.BooleanField(default=False)
    medication = models.ForeignKey('pharmacy.Medication', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_items')
    is_consumable = models.BooleanField(default=False)
    is_equipment = models.BooleanField(default=False)
    reorder_level = models.IntegerField(default=0)
    reorder_quantity = models.IntegerField(default=0)
    minimum_stock = models.IntegerField(default=0)
    maximum_stock = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'items'
        managed = True
        ordering = ['name']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Store(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True)
    store_type = models.CharField(max_length=50, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    manager = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_stores')
    is_active = models.BooleanField(default=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stores'
        managed = True

    def __str__(self):
        return f"{self.code} - {self.name}"


class Stock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='stock')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stock')
    batch_lot_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_reserved = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    last_received_date = models.DateField(blank=True, null=True)
    last_issued_date = models.DateField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock'
        managed = True
        unique_together = ('item', 'store', 'batch_lot_number')
        ordering = ['item__name', 'store__name']

    @property
    def quantity_available(self):
        return self.quantity_on_hand - self.quantity_reserved

    def __str__(self):
        return f"{self.item.name} - {self.store.name} - {self.quantity_on_hand}"


class StockMovement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    movement_number = models.CharField(max_length=20, unique=True, editable=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='movements')
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=15, choices=StockMovementType.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    batch_lot_number = models.CharField(max_length=100, blank=True, null=True)
    expiry_date = models.DateField(blank=True, null=True)
    reference_type = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.UUIDField(blank=True, null=True)
    from_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_from')
    to_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='movements_to')
    notes = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_movements')
    performed_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_movements'
        managed = True
        ordering = ['-performed_at']

    def save(self, *args, **kwargs):
        if not self.movement_number:
            from datetime import date
            today = date.today()
            prefix = f"STM-{today.strftime('%Y%m%d')}-"
            from jfd_hms.utils import generate_sequence_number
            self.movement_number = generate_sequence_number(prefix, StockMovement, 'movement_number')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.movement_number} - {self.item.name} - {self.movement_type}"


class StockCount(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    count_number = models.CharField(max_length=20, unique=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stock_counts')
    count_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, default='in_progress')
    conducted_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_counts_conducted')
    approved_by = models.ForeignKey('users_auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='stock_counts_approved')
    notes = models.TextField(blank=True, null=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices, default=SyncStatus.SYNCED)
    last_modified = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock_counts'
        managed = True
        ordering = ['-count_date']

    def save(self, *args, **kwargs):
        if not self.count_number:
            from datetime import date
            today = date.today()
            prefix = f"SC-{today.strftime('%Y%m%d')}-"
            from jfd_hms.utils import generate_sequence_number
            self.count_number = generate_sequence_number(prefix, StockCount, 'count_number')
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.count_number} - {self.store.name}"


class StockCountItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stock_count = models.ForeignKey(StockCount, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='count_items')
    batch_lot_number = models.CharField(max_length=100, blank=True, null=True)
    system_quantity = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    counted_quantity = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_count_items'
        managed = True

    @property
    def variance(self):
        if self.system_quantity is not None and self.counted_quantity is not None:
            return self.counted_quantity - self.system_quantity
        return None

    def __str__(self):
        return f"{self.stock_count.count_number} - {self.item.name}"
