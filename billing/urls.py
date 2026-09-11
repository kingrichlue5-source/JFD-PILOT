from django.urls import path
from . import views

app_name = 'billing'

urlpatterns = [
    # Price Lists
    path('price-lists/', views.PriceListView.as_view(), name='price-list-list'),
    path('price-lists/<uuid:pk>/', views.PriceListDetailView.as_view(), name='price-list-detail'),

    # Service Items
    path('services/', views.ServiceItemListView.as_view(), name='service-list'),
    path('services/<uuid:pk>/', views.ServiceItemDetailView.as_view(), name='service-detail'),
    path('services/<uuid:service_id>/prices/', views.ServicePriceListView.as_view(), name='service-price-list'),

    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<uuid:pk>/', views.InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/<uuid:invoice_id>/items/', views.InvoiceLineItemListView.as_view(), name='invoice-item-list'),
    path('invoices/<uuid:invoice_id>/ledger/', views.invoice_ledger, name='invoice-ledger'),

    # Payments
    path('payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('payments/<uuid:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('pay/', views.process_payment, name='process-payment'),
    path('post-charge/', views.post_charge, name='post-charge'),
    path('receipts/<str:receipt_number>/', views.receipt_detail, name='receipt-detail'),

    # Refunds
    path('refunds/', views.RefundListView.as_view(), name='refund-list'),
    path('refunds/<uuid:pk>/', views.RefundDetailView.as_view(), name='refund-detail'),

    # Reports & Shifts
    path('daily-revenue/', views.daily_revenue, name='daily-revenue'),
    path('revenue-summary/', views.revenue_summary, name='revenue-summary'),
    path('cashier-shifts/', views.CashierShiftListView.as_view(), name='cashier-shift-list'),
    path('cashier-shifts/<uuid:shift_id>/summary/', views.cashier_shift_summary, name='cashier-shift-summary'),
    path('cashier-shifts/<uuid:shift_id>/close/', views.close_cashier_shift, name='cashier-shift-close'),

    # Deposit, Waiver, Credit
    path('deposit/', views.process_deposit, name='process-deposit'),
    path('waive/', views.waive_payment, name='waive-payment'),
    path('credit-adjustment/', views.create_credit_adjustment, name='credit-adjustment'),
]
