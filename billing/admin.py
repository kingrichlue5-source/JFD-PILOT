from django.contrib import admin
from .models import (
    PriceList, ServiceItem, ServicePrice, Invoice,
    InvoiceLineItem, Payment, Refund, CreditAdjustment, CashierShift
)


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_default', 'is_active', 'effective_date', 'expiry_date']
    list_filter = ['is_default', 'is_active']
    search_fields = ['name', 'code']


@admin.register(ServiceItem)
class ServiceItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'subcategory', 'is_billable', 'is_active']
    list_filter = ['category', 'is_billable', 'is_active']
    search_fields = ['name', 'code']


@admin.register(ServicePrice)
class ServicePriceAdmin(admin.ModelAdmin):
    list_display = ['service_item', 'price_list', 'price', 'payer_category', 'effective_date']
    list_filter = ['price_list', 'payer_category']
    search_fields = ['service_item__name', 'service_item__code']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'patient', 'total_amount', 'amount_paid', 'balance_due', 'status', 'invoice_date']
    list_filter = ['status', 'payer_type', 'invoice_date']
    search_fields = ['invoice_number', 'patient__mrn']
    readonly_fields = ['invoice_number', 'created_at']
    date_hierarchy = 'invoice_date'


@admin.register(InvoiceLineItem)
class InvoiceLineItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'service_item', 'quantity', 'unit_price', 'total_amount']
    list_filter = ['service_item__category']
    search_fields = ['invoice__invoice_number', 'service_item__name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_number', 'invoice', 'patient', 'amount', 'payment_method', 'payment_date']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['payment_number', 'invoice__invoice_number', 'patient__mrn']
    readonly_fields = ['payment_number', 'created_at']
    date_hierarchy = 'payment_date'


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['refund_number', 'payment', 'invoice', 'amount', 'reason', 'refund_date']
    list_filter = ['refund_method', 'refund_date']
    search_fields = ['refund_number', 'invoice__invoice_number', 'patient__mrn']
    readonly_fields = ['refund_number', 'created_at']
    date_hierarchy = 'refund_date'


@admin.register(CreditAdjustment)
class CreditAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['adjustment_number', 'invoice', 'adjustment_type', 'amount', 'adjusted_at']
    list_filter = ['adjustment_type']
    search_fields = ['adjustment_number', 'invoice__invoice_number']
    readonly_fields = ['adjustment_number', 'created_at']
    date_hierarchy = 'adjusted_at'


@admin.register(CashierShift)
class CashierShiftAdmin(admin.ModelAdmin):
    list_display = ['shift_number', 'cashier', 'shift_start', 'shift_end', 'opening_balance', 'closing_balance', 'status']
    list_filter = ['status']
    search_fields = ['shift_number', 'cashier__username']
    readonly_fields = ['shift_number', 'created_at']
    date_hierarchy = 'shift_start'
