from rest_framework import serializers
from .models import (
    PriceList, ServiceItem, ServicePrice, Invoice,
    InvoiceLineItem, Payment, Refund, CreditAdjustment, CashierShift
)


class PriceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceList
        fields = ['id', 'name', 'code', 'description', 'is_default', 'is_active',
                  'effective_date', 'expiry_date', 'created_at']
        read_only_fields = ['id', 'created_at']


class ServiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceItem
        fields = ['id', 'name', 'code', 'category', 'subcategory', 'description',
                  'unit_of_measure', 'is_billable', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class ServicePriceSerializer(serializers.ModelSerializer):
    service_item_name = serializers.CharField(source='service_item.name', read_only=True)
    price_list_name = serializers.CharField(source='price_list.name', read_only=True)

    class Meta:
        model = ServicePrice
        fields = ['id', 'service_item', 'service_item_name', 'price_list', 'price_list_name',
                  'price', 'payer_category', 'effective_date', 'expiry_date', 'created_at']
        read_only_fields = ['id', 'created_at']


class InvoiceLineItemSerializer(serializers.ModelSerializer):
    service_item_name = serializers.CharField(source='service_item.name', read_only=True)
    balance_due = serializers.SerializerMethodField()

    class Meta:
        model = InvoiceLineItem
        fields = ['id', 'invoice', 'service_item', 'service_item_name', 'description',
                  'quantity', 'unit_price', 'discount_amount', 'tax_amount',
                  'total_amount', 'payment_status', 'paid_amount', 'balance_due',
                  'order', 'prescription_item', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_balance_due(self, obj):
        return obj.total_amount - obj.paid_amount


class PaymentSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    received_by_name = serializers.SerializerMethodField()
    cashier_shift_number = serializers.CharField(source='cashier_shift.shift_number', read_only=True, default=None)

    class Meta:
        model = Payment
        fields = ['id', 'payment_number', 'receipt_number', 'invoice', 'patient', 'patient_mrn',
                  'amount', 'payment_method', 'payment_date', 'reference_number',
                  'bank_name', 'check_number', 'mobile_money_number',
                  'insurance_claim_number', 'cashier_shift', 'cashier_shift_number',
                  'notes', 'received_by', 'received_by_name', 'created_at']
        read_only_fields = ['id', 'payment_number', 'receipt_number', 'payment_date', 'created_at']

    def get_received_by_name(self, obj):
        if obj.received_by:
            return f"{obj.received_by.first_name} {obj.received_by.last_name}"
        return None


class InvoiceSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()
    line_items = InvoiceLineItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = ['id', 'invoice_number', 'patient', 'patient_mrn', 'patient_name',
                  'visit', 'admission', 'invoice_date', 'due_date', 'subtotal',
                  'tax_amount', 'discount_amount', 'total_amount', 'amount_paid',
                  'balance_due', 'status', 'payer_type', 'insurance_authorization_number',
                  'notes', 'line_items', 'payments', 'created_at']
        read_only_fields = ['id', 'invoice_number', 'invoice_date', 'created_at']

    def get_patient_name(self, obj):
        if obj.patient.middle_name:
            return f"{obj.patient.first_name} {obj.patient.middle_name} {obj.patient.last_name}"
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class RefundSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    approved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Refund
        fields = ['id', 'refund_number', 'payment', 'invoice', 'patient',
                  'patient_mrn', 'amount', 'reason', 'refund_method',
                  'refund_date', 'approved_by', 'approved_by_name',
                  'approved_at', 'processed_by', 'created_at']
        read_only_fields = ['id', 'refund_number', 'refund_date', 'created_at']

    def get_approved_by_name(self, obj):
        if obj.approved_by:
            return f"{obj.approved_by.first_name} {obj.approved_by.last_name}"
        return None


class CashierShiftSerializer(serializers.ModelSerializer):
    cashier_name = serializers.SerializerMethodField()

    class Meta:
        model = CashierShift
        fields = ['id', 'shift_number', 'cashier', 'cashier_name', 'shift_start',
                  'shift_end', 'opening_balance', 'closing_balance', 'total_cash',
                  'total_mobile_money', 'total_bank_transfer', 'total_insurance',
                  'total_credit', 'status', 'notes', 'created_at']
        read_only_fields = ['id', 'shift_number', 'shift_start', 'created_at']

    def get_cashier_name(self, obj):
        if obj.cashier:
            return f"{obj.cashier.first_name} {obj.cashier.last_name}"
        return None
