from django.contrib import admin
from .models import Category, Item, Store, Stock, StockMovement, StockCount, StockCountItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'parent_category', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'unit_of_measure', 'is_medication', 'is_consumable', 'is_equipment', 'is_active']
    list_filter = ['category', 'is_medication', 'is_consumable', 'is_equipment', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'store_type', 'location', 'manager', 'is_active']
    list_filter = ['store_type', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ['item', 'store', 'batch_lot_number', 'quantity_on_hand', 'expiry_date', 'unit_cost']
    list_filter = ['store', 'item__category']
    search_fields = ['item__name', 'item__code', 'batch_lot_number']
    date_hierarchy = 'expiry_date'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['movement_number', 'item', 'store', 'movement_type', 'quantity', 'performed_by', 'performed_at']
    list_filter = ['movement_type', 'store']
    search_fields = ['movement_number', 'item__name', 'item__code']
    readonly_fields = ['movement_number', 'created_at']
    date_hierarchy = 'performed_at'


@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    list_display = ['count_number', 'store', 'count_date', 'status', 'conducted_by']
    list_filter = ['status', 'store']
    search_fields = ['count_number']
    readonly_fields = ['count_number', 'created_at']
    date_hierarchy = 'count_date'


@admin.register(StockCountItem)
class StockCountItemAdmin(admin.ModelAdmin):
    list_display = ['stock_count', 'item', 'batch_lot_number', 'system_quantity', 'counted_quantity', 'variance']
    list_filter = ['stock_count__store']
    search_fields = ['item__name', 'item__code']
