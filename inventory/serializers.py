from rest_framework import serializers
from .models import Category, Item, Store, Stock, StockMovement, StockCount, StockCountItem


class CategorySerializer(serializers.ModelSerializer):
    parent_category_name = serializers.CharField(source='parent_category.name', read_only=True, default=None)

    class Meta:
        model = Category
        fields = ['id', 'name', 'code', 'parent_category', 'parent_category_name',
                  'description', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)

    class Meta:
        model = Item
        fields = ['id', 'name', 'code', 'category', 'category_name', 'description',
                  'unit_of_measure', 'item_type', 'is_medication', 'medication',
                  'is_consumable', 'is_equipment', 'reorder_level', 'reorder_quantity',
                  'minimum_stock', 'maximum_stock', 'unit_cost', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class StoreSerializer(serializers.ModelSerializer):
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = Store
        fields = ['id', 'name', 'code', 'store_type', 'location',
                  'manager', 'manager_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_manager_name(self, obj):
        if obj.manager:
            return f"{obj.manager.first_name} {obj.manager.last_name}"
        return None


class StockSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_code = serializers.CharField(source='item.code', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    category_name = serializers.CharField(source='item.category.name', read_only=True, default=None)
    reorder_level = serializers.IntegerField(source='item.reorder_level', read_only=True, default=0)
    quantity_available = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Stock
        fields = ['id', 'item', 'item_name', 'item_code', 'store', 'store_name',
                  'category_name', 'reorder_level',
                  'batch_lot_number', 'expiry_date', 'quantity_on_hand',
                  'quantity_reserved', 'quantity_available', 'unit_cost',
                  'last_received_date', 'last_issued_date', 'created_at']
        read_only_fields = ['id', 'quantity_available', 'created_at']


class StockMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    performed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StockMovement
        fields = ['id', 'movement_number', 'item', 'item_name', 'store', 'store_name',
                  'movement_type', 'quantity', 'unit_cost', 'total_cost',
                  'batch_lot_number', 'expiry_date', 'reference_type', 'reference_id',
                  'from_store', 'to_store', 'notes', 'performed_by',
                  'performed_by_name', 'performed_at', 'created_at']
        read_only_fields = ['id', 'movement_number', 'performed_at', 'created_at']

    def get_performed_by_name(self, obj):
        if obj.performed_by:
            return f"{obj.performed_by.first_name} {obj.performed_by.last_name}"
        return None


class StockCountItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    variance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = StockCountItem
        fields = ['id', 'stock_count', 'item', 'item_name', 'batch_lot_number',
                  'system_quantity', 'counted_quantity', 'variance', 'notes', 'created_at']
        read_only_fields = ['id', 'variance', 'created_at']


class StockCountSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source='store.name', read_only=True)
    conducted_by_name = serializers.SerializerMethodField()
    items = StockCountItemSerializer(many=True, read_only=True)

    class Meta:
        model = StockCount
        fields = ['id', 'count_number', 'store', 'store_name', 'count_date',
                  'status', 'conducted_by', 'conducted_by_name', 'approved_by',
                  'notes', 'items', 'created_at']
        read_only_fields = ['id', 'count_number', 'count_date', 'created_at']

    def get_conducted_by_name(self, obj):
        if obj.conducted_by:
            return f"{obj.conducted_by.first_name} {obj.conducted_by.last_name}"
        return None
