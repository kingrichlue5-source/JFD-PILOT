from django.db.models import Q, Sum, Count, F
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    PriceList, ServiceItem, ServicePrice, Invoice,
    InvoiceLineItem, Payment, Refund, CreditAdjustment, CashierShift
)
from .serializers import (
    PriceListSerializer, ServiceItemSerializer, ServicePriceSerializer,
    InvoiceSerializer, InvoiceLineItemSerializer,
    PaymentSerializer, RefundSerializer, CashierShiftSerializer
)
from jfd_hms.permissions import require_permission, make_permission_class


class PriceListView(generics.ListCreateAPIView):
    queryset = PriceList.objects.filter(is_active=True)
    serializer_class = PriceListSerializer
    permission_classes = [make_permission_class('INVOICE_VIEW')]


class PriceListDetailView(generics.RetrieveUpdateAPIView):
    queryset = PriceList.objects.all()
    serializer_class = PriceListSerializer
    permission_classes = [make_permission_class('INVOICE_CREATE')]


class ServiceItemListView(generics.ListCreateAPIView):
    queryset = ServiceItem.objects.filter(is_active=True)
    serializer_class = ServiceItemSerializer
    permission_classes = [make_permission_class('INVOICE_VIEW')]

    def get_queryset(self):
        queryset = ServiceItem.objects.filter(is_active=True)
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search)
            )

        if category:
            queryset = queryset.filter(category=category)

        return queryset


class ServiceItemDetailView(generics.RetrieveUpdateAPIView):
    queryset = ServiceItem.objects.all()
    serializer_class = ServiceItemSerializer
    permission_classes = [make_permission_class('INVOICE_CREATE')]


class ServicePriceListView(generics.ListCreateAPIView):
    serializer_class = ServicePriceSerializer
    permission_classes = [make_permission_class('INVOICE_VIEW')]

    def get_queryset(self):
        return ServicePrice.objects.filter(service_item_id=self.kwargs['service_id'])


class InvoiceListView(generics.ListCreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [make_permission_class('INVOICE_VIEW')]

    def get_queryset(self):
        queryset = Invoice.objects.filter(is_deleted=False)
        patient = self.request.query_params.get('patient', None)
        status_filter = self.request.query_params.get('status', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)

        if patient:
            queryset = queryset.filter(patient_id=patient)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_from:
            queryset = queryset.filter(invoice_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(invoice_date__lte=date_to)

        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class InvoiceDetailView(generics.RetrieveUpdateAPIView):
    queryset = Invoice.objects.filter(is_deleted=False)
    serializer_class = InvoiceSerializer
    permission_classes = [make_permission_class('INVOICE_CREATE')]


class InvoiceLineItemListView(generics.ListCreateAPIView):
    serializer_class = InvoiceLineItemSerializer
    permission_classes = [make_permission_class('INVOICE_VIEW')]

    def get_queryset(self):
        return InvoiceLineItem.objects.filter(invoice_id=self.kwargs['invoice_id'])


class PaymentListView(generics.ListAPIView):
    serializer_class = PaymentSerializer
    permission_classes = [make_permission_class('INVOICE_VIEW')]

    def get_queryset(self):
        queryset = Payment.objects.filter(is_deleted=False)
        patient = self.request.query_params.get('patient', None)
        invoice = self.request.query_params.get('invoice', None)
        method = self.request.query_params.get('method', None)

        if patient:
            queryset = queryset.filter(patient_id=patient)
        if invoice:
            queryset = queryset.filter(invoice_id=invoice)
        if method:
            queryset = queryset.filter(payment_method=method)

        return queryset


class PaymentDetailView(generics.RetrieveAPIView):
    queryset = Payment.objects.filter(is_deleted=False)
    serializer_class = PaymentSerializer
    permission_classes = [make_permission_class('INVOICE_VIEW')]


@api_view(['POST'])
@permission_classes([make_permission_class('PAYMENT_PROCESS')])
def process_payment(request):
    from decimal import Decimal
    from .services import generate_receipt_number, recalculate_invoice_totals

    invoice_id = request.data.get('invoice_id')
    amount = request.data.get('amount')
    payment_method = request.data.get('payment_method')
    line_item_ids = request.data.get('line_item_ids', [])
    cashier_shift_id = request.data.get('cashier_shift_id', None)
    reference_number = request.data.get('reference_number', '')
    bank_name = request.data.get('bank_name', '')
    check_number = request.data.get('check_number', '')
    mobile_money_number = request.data.get('mobile_money_number', '')
    insurance_claim_number = request.data.get('insurance_claim_number', '')
    notes = request.data.get('notes', '')

    if not invoice_id or not amount or not payment_method:
        return Response(
            {'error': 'invoice_id, amount, and payment_method are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    valid_methods = ['cash', 'bank_transfer', 'mobile_money', 'insurance', 'credit', 'other']
    if payment_method not in valid_methods:
        return Response({'error': f'payment_method must be one of: {", ".join(valid_methods)}'},
                        status=status.HTTP_400_BAD_REQUEST)

    try:
        invoice = Invoice.objects.get(id=invoice_id, is_deleted=False)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

    amount = Decimal(str(amount))
    if amount <= 0:
        return Response({'error': 'Amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    receipt_number = generate_receipt_number()

    cashier_shift = None
    if cashier_shift_id:
        try:
            cashier_shift = CashierShift.objects.get(id=cashier_shift_id, status='open')
        except CashierShift.DoesNotExist:
            return Response({'error': 'Cashier shift not found or not open'}, status=status.HTTP_400_BAD_REQUEST)

    payment = Payment.objects.create(
        invoice=invoice,
        patient=invoice.patient,
        amount=amount,
        payment_method=payment_method,
        receipt_number=receipt_number,
        reference_number=reference_number,
        bank_name=bank_name,
        check_number=check_number,
        mobile_money_number=mobile_money_number,
        insurance_claim_number=insurance_claim_number,
        cashier_shift=cashier_shift,
        notes=notes,
        received_by=request.user if request.user.is_authenticated else None
    )

    remaining = amount

    if line_item_ids:
        line_items = InvoiceLineItem.objects.filter(
            id__in=line_item_ids,
            invoice=invoice
        )
    else:
        line_items = InvoiceLineItem.objects.filter(
            invoice=invoice,
            payment_status__in=['pending', 'partial']
        ).order_by('created_at')

    for item in line_items:
        if remaining <= 0:
            break

        item_balance = item.total_amount - item.paid_amount
        if item_balance <= 0:
            continue

        payment_to_apply = min(remaining, item_balance)
        item.paid_amount += payment_to_apply
        remaining -= payment_to_apply

        if item.paid_amount >= item.total_amount:
            item.payment_status = 'paid'
        else:
            item.payment_status = 'partial'

        item.save()

    recalculate_invoice_totals(invoice)

    if cashier_shift:
        method = payment.payment_method
        if method == 'cash':
            cashier_shift.total_cash += amount
        elif method == 'mobile_money':
            cashier_shift.total_mobile_money += amount
        elif method == 'bank_transfer':
            cashier_shift.total_bank_transfer += amount
        elif method == 'insurance':
            cashier_shift.total_insurance += amount
        elif method == 'credit':
            cashier_shift.total_credit += amount
        cashier_shift.save()

    from audit.utils import log_audit
    log_audit('billing', 'payments', payment.id, 'CREATE',
              new_values={
                  'invoice_number': invoice.invoice_number,
                  'amount': str(amount),
                  'payment_method': payment_method,
                  'receipt_number': receipt_number,
              },
              request=request)

    return Response({
        'payment': PaymentSerializer(payment).data,
        'receipt_number': receipt_number,
        'invoice_status': invoice.status,
        'balance_due': str(invoice.balance_due),
        'remaining_payment': str(remaining)
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([make_permission_class('INVOICE_VIEW')])
def receipt_detail(request, receipt_number):
    try:
        payment = Payment.objects.get(receipt_number=receipt_number, is_deleted=False)
    except Payment.DoesNotExist:
        return Response({'error': 'Receipt not found'}, status=status.HTTP_404_NOT_FOUND)

    invoice = payment.invoice
    line_items = InvoiceLineItem.objects.filter(invoice=invoice)
    all_payments = Payment.objects.filter(invoice=invoice, is_deleted=False).order_by('payment_date')

    return Response({
        'receipt': PaymentSerializer(payment).data,
        'invoice': {
            'invoice_number': invoice.invoice_number,
            'patient_mrn': invoice.patient.mrn,
            'patient_name': f"{invoice.patient.first_name} {invoice.patient.last_name}",
            'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
            'total_amount': str(invoice.total_amount),
            'amount_paid': str(invoice.amount_paid),
            'balance_due': str(invoice.balance_due),
            'status': invoice.status,
            'payer_type': invoice.payer_type,
        },
        'line_items': InvoiceLineItemSerializer(line_items, many=True).data,
        'payments': PaymentSerializer(all_payments, many=True).data,
    })


@api_view(['GET'])
@permission_classes([make_permission_class('INVOICE_VIEW')])
def invoice_ledger(request, invoice_id):
    try:
        invoice = Invoice.objects.get(id=invoice_id, is_deleted=False)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

    line_items = InvoiceLineItem.objects.filter(invoice=invoice)
    payments = Payment.objects.filter(invoice=invoice, is_deleted=False).order_by('payment_date')

    charges = []
    for item in line_items:
        charges.append({
            'id': str(item.id),
            'description': item.description,
            'service_item': item.service_item.name,
            'quantity': str(item.quantity),
            'unit_price': str(item.unit_price),
            'total_amount': str(item.total_amount),
            'payment_status': item.payment_status,
            'paid_amount': str(item.paid_amount),
            'balance_due': str(item.total_amount - item.paid_amount),
            'created_at': item.created_at.isoformat() if item.created_at else None,
        })

    payment_history = []
    for p in payments:
        payment_history.append({
            'id': str(p.id),
            'receipt_number': p.receipt_number,
            'amount': str(p.amount),
            'payment_method': p.payment_method,
            'payment_date': p.payment_date.isoformat() if p.payment_date else None,
            'reference_number': p.reference_number,
            'received_by_name': f"{p.received_by.first_name} {p.received_by.last_name}" if p.received_by else None,
        })

    return Response({
        'invoice': InvoiceSerializer(invoice).data,
        'charges': charges,
        'payments': payment_history,
        'summary': {
            'total_charges': str(invoice.subtotal),
            'total_paid': str(invoice.amount_paid),
            'balance_due': str(invoice.balance_due),
            'status': invoice.status,
        }
    })


class RefundListView(generics.ListCreateAPIView):
    serializer_class = RefundSerializer
    permission_classes = [make_permission_class('INVOICE_VIEW')]

    def get_queryset(self):
        queryset = Refund.objects.all()
        patient = self.request.query_params.get('patient', None)
        invoice = self.request.query_params.get('invoice', None)

        if patient:
            queryset = queryset.filter(patient_id=patient)
        if invoice:
            queryset = queryset.filter(invoice_id=invoice)

        return queryset


class RefundDetailView(generics.RetrieveUpdateAPIView):
    queryset = Refund.objects.all()
    serializer_class = RefundSerializer
    permission_classes = [make_permission_class('INVOICE_VIEW')]


class CashierShiftListView(generics.ListCreateAPIView):
    serializer_class = CashierShiftSerializer
    permission_classes = [make_permission_class('INVOICE_VIEW')]

    def get_queryset(self):
        queryset = CashierShift.objects.all()
        cashier = self.request.query_params.get('cashier', None)
        status_filter = self.request.query_params.get('status', None)

        if cashier:
            queryset = queryset.filter(cashier_id=cashier)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


@api_view(['POST'])
@permission_classes([make_permission_class('INVOICE_CREATE')])
def post_charge(request):
    """
    Automated Fee Posting API: /api/billing/post-charge/

    When called by an authorized clinician, verifies the patient's payer category,
    pulls the correct amount from the PriceList catalog, and injects an unpaid
    record into the patient's billing file.
    """
    from decimal import Decimal
    from clinical.models import Order, Visit
    from .services import post_order_to_invoice

    order_id = request.data.get('order_id')
    visit_id = request.data.get('visit_id')

    if not order_id or not visit_id:
        return Response(
            {'error': 'order_id and visit_id are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        visit = Visit.objects.get(id=visit_id, is_deleted=False)
    except Visit.DoesNotExist:
        return Response({'error': 'Visit not found'}, status=status.HTTP_404_NOT_FOUND)

    patient = visit.patient
    line_item = post_order_to_invoice(order, visit, patient)

    if not line_item:
        return Response(
            {'error': 'No billable service found for this order, or price is zero'},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        'line_item_id': str(line_item.id),
        'invoice_id': str(line_item.invoice_id),
        'description': line_item.description,
        'amount': str(line_item.total_amount),
        'payment_status': line_item.payment_status,
        'patient_mrn': patient.mrn,
        'invoice_number': line_item.invoice.invoice_number,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([make_permission_class('INVOICE_VIEW')])
def daily_revenue(request):
    from django.utils import timezone as tz
    today = tz.localdate()

    payments = Payment.objects.filter(
        is_deleted=False,
        payment_date__date=today
    )

    cash_total = payments.filter(payment_method='cash').aggregate(total=Sum('amount'))['total'] or 0
    mobile_total = payments.filter(payment_method='mobile_money').aggregate(total=Sum('amount'))['total'] or 0
    insurance_total = payments.filter(payment_method='insurance').aggregate(total=Sum('amount'))['total'] or 0
    credit_total = payments.filter(payment_method='credit').aggregate(total=Sum('amount'))['total'] or 0
    total = payments.aggregate(total=Sum('amount'))['total'] or 0
    count = payments.count()

    return Response({
        'date': str(today),
        'cash_total': str(cash_total),
        'mobile_total': str(mobile_total),
        'insurance_total': str(insurance_total),
        'credit_total': str(credit_total),
        'total': str(total),
        'transaction_count': count,
    })


@api_view(['GET'])
@permission_classes([make_permission_class('INVOICE_VIEW')])
def cashier_shift_summary(request, shift_id):
    from django.db.models import Count, Sum

    try:
        shift = CashierShift.objects.get(id=shift_id)
    except CashierShift.DoesNotExist:
        return Response({'error': 'Cashier shift not found'}, status=status.HTTP_404_NOT_FOUND)

    payments = Payment.objects.filter(
        cashier_shift=shift,
        is_deleted=False
    )

    summary = {
        'shift_number': shift.shift_number,
        'cashier': f"{shift.cashier.first_name} {shift.cashier.last_name}" if shift.cashier else None,
        'shift_start': shift.shift_start.isoformat() if shift.shift_start else None,
        'shift_end': shift.shift_end.isoformat() if shift.shift_end else None,
        'status': shift.status,
        'opening_balance': str(shift.opening_balance),
        'closing_balance': str(shift.closing_balance) if shift.closing_balance else None,
        'total_cash': str(shift.total_cash),
        'total_mobile_money': str(shift.total_mobile_money),
        'total_bank_transfer': str(shift.total_bank_transfer),
        'total_insurance': str(shift.total_insurance),
        'total_credit': str(shift.total_credit),
        'transaction_count': payments.count(),
        'total_collected': str(payments.aggregate(total=Sum('amount'))['total'] or 0),
        'transactions_by_method': {},
    }

    for method in ['cash', 'mobile_money', 'bank_transfer', 'insurance', 'credit']:
        method_payments = payments.filter(payment_method=method)
        summary['transactions_by_method'][method] = {
            'count': method_payments.count(),
            'total': str(method_payments.aggregate(total=Sum('amount'))['total'] or 0),
        }

    return Response(summary)


@api_view(['POST'])
@permission_classes([make_permission_class('PAYMENT_PROCESS')])
def process_deposit(request):
    from decimal import Decimal
    from .services import generate_receipt_number, recalculate_invoice_totals

    invoice_id = request.data.get('invoice_id')
    amount = request.data.get('amount')
    payment_method = request.data.get('payment_method', 'cash')

    if not invoice_id or not amount:
        return Response({'error': 'invoice_id and amount are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        invoice = Invoice.objects.get(id=invoice_id, is_deleted=False)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

    amount = Decimal(str(amount))
    if amount <= 0:
        return Response({'error': 'Amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)

    receipt_number = generate_receipt_number()
    payment = Payment.objects.create(
        invoice=invoice,
        patient=invoice.patient,
        amount=amount,
        payment_method=payment_method,
        receipt_number=receipt_number,
        notes='Deposit',
        received_by=request.user if request.user.is_authenticated else None
    )

    remaining = amount
    line_items = InvoiceLineItem.objects.filter(
        invoice=invoice, payment_status__in=['pending', 'partial']
    ).order_by('created_at')

    for item in line_items:
        if remaining <= 0:
            break
        item_balance = item.total_amount - item.paid_amount
        if item_balance <= 0:
            continue
        payment_to_apply = min(remaining, item_balance)
        item.paid_amount += payment_to_apply
        remaining -= payment_to_apply
        item.payment_status = 'paid' if item.paid_amount >= item.total_amount else 'partial'
        item.save()

    recalculate_invoice_totals(invoice)

    return Response({
        'receipt_number': receipt_number,
        'deposit_amount': str(amount),
        'applied_amount': str(amount - remaining),
        'remaining_deposit': str(remaining),
        'invoice_status': invoice.status,
        'balance_due': str(invoice.balance_due),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([make_permission_class('PAYMENT_PROCESS')])
def waive_payment(request):
    from .services import recalculate_invoice_totals
    from audit.utils import log_audit

    line_item_id = request.data.get('line_item_id')
    invoice_id = request.data.get('invoice_id')
    reason = request.data.get('reason', '')

    if not line_item_id and not invoice_id:
        return Response({'error': 'line_item_id or invoice_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    if line_item_id:
        try:
            item = InvoiceLineItem.objects.get(id=line_item_id)
        except InvoiceLineItem.DoesNotExist:
            return Response({'error': 'Line item not found'}, status=status.HTTP_404_NOT_FOUND)
        old_status = item.payment_status
        item.payment_status = 'waived'
        item.paid_amount = item.total_amount
        item.save()
        recalculate_invoice_totals(item.invoice)
        log_audit('billing', 'invoice_line_items', item.id, 'UPDATE',
                  old_values={'payment_status': old_status, 'paid_amount': str(item.paid_amount - item.total_amount)},
                  new_values={'payment_status': 'waived', 'paid_amount': str(item.paid_amount), 'reason': reason},
                  request=request)
        return Response({'status': 'waived', 'invoice_status': item.invoice.status})

    if invoice_id:
        try:
            invoice = Invoice.objects.get(id=invoice_id, is_deleted=False)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)
        InvoiceLineItem.objects.filter(invoice=invoice).update(
            payment_status='waived',
            paid_amount=F('total_amount')
        )
        recalculate_invoice_totals(invoice)
        log_audit('billing', 'invoices', invoice.id, 'UPDATE',
                  old_values={'status': invoice.status},
                  new_values={'status': 'waived', 'reason': reason},
                  request=request)
        return Response({'status': 'waived', 'invoice_status': invoice.status})


@api_view(['POST'])
@permission_classes([make_permission_class('INVOICE_CREATE')])
def create_credit_adjustment(request):
    from decimal import Decimal
    from .services import recalculate_invoice_totals
    from audit.utils import log_audit

    invoice_id = request.data.get('invoice_id')
    adjustment_type = request.data.get('adjustment_type', 'credit')
    amount = request.data.get('amount')
    reason = request.data.get('reason', '')
    approved_by_id = request.data.get('approved_by')

    if not invoice_id or not amount:
        return Response({'error': 'invoice_id and amount are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        invoice = Invoice.objects.get(id=invoice_id, is_deleted=False)
    except Invoice.DoesNotExist:
        return Response({'error': 'Invoice not found'}, status=status.HTTP_404_NOT_FOUND)

    amount = Decimal(str(amount))

    prefix = f"CADJ-{timezone.now().strftime('%Y%m%d')}-"
    from jfd_hms.utils import generate_sequence_number
    adjustment_number = generate_sequence_number(prefix, CreditAdjustment, 'adjustment_number')

    from users_auth.models import User
    adjusted_by = request.user if request.user.is_authenticated else None
    approved_by = None
    if approved_by_id:
        try:
            approved_by = User.objects.get(id=approved_by_id)
        except User.DoesNotExist:
            return Response({'error': 'Approving user not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        approved_by = adjusted_by

    adjustment = CreditAdjustment.objects.create(
        adjustment_number=adjustment_number,
        invoice=invoice,
        patient=invoice.patient,
        adjustment_type=adjustment_type,
        amount=amount,
        reason=reason,
        adjusted_by=adjusted_by,
        approved_by=approved_by,
    )

    if adjustment_type == 'discount':
        invoice.discount_amount += amount
        invoice.save(update_fields=['discount_amount'])
    elif adjustment_type == 'waive':
        invoice.balance_due = Decimal('0')
        invoice.status = 'waived'
        invoice.save(update_fields=['balance_due', 'status'])
    elif adjustment_type == 'write_off':
        invoice.balance_due -= amount
        if invoice.balance_due <= 0:
            invoice.balance_due = Decimal('0')
            invoice.status = 'paid'
        invoice.save(update_fields=['balance_due', 'status'])

    recalculate_invoice_totals(invoice)

    log_audit('billing', 'credit_adjustments', adjustment.id, 'CREATE',
              new_values={
                  'adjustment_type': adjustment_type,
                  'amount': str(amount),
                  'reason': reason,
                  'invoice': str(invoice.invoice_number),
              },
              request=request)

    return Response({
        'adjustment_number': adjustment.adjustment_number,
        'adjustment_type': adjustment_type,
        'amount': str(amount),
        'invoice_status': invoice.status,
        'balance_due': str(invoice.balance_due),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([make_permission_class('PAYMENT_PROCESS')])
def close_cashier_shift(request, shift_id):
    from decimal import Decimal
    from audit.utils import log_audit

    try:
        shift = CashierShift.objects.get(id=shift_id, status='open')
    except CashierShift.DoesNotExist:
        return Response({'error': 'Open shift not found'}, status=status.HTTP_404_NOT_FOUND)

    closing_balance = Decimal(str(request.data.get('closing_balance', '0')))
    shift.closing_balance = closing_balance
    shift.shift_end = timezone.now()
    shift.status = 'closed'
    shift.save()

    payments = Payment.objects.filter(cashier_shift=shift, is_deleted=False)
    total_payments = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
    expected_total = shift.opening_balance + total_payments

    log_audit('billing', 'cashier_shifts', shift.id, 'UPDATE',
              old_values={'status': 'open'},
              new_values={
                  'status': 'closed',
                  'closing_balance': str(closing_balance),
                  'expected_total': str(expected_total),
                  'variance': str(closing_balance - expected_total),
              },
              request=request)

    return Response({
        'shift_number': shift.shift_number,
        'status': 'closed',
        'opening_balance': str(shift.opening_balance),
        'closing_balance': str(closing_balance),
        'expected_total': str(expected_total),
        'variance': str(closing_balance - expected_total),
        'total_payments': str(total_payments),
    })


@api_view(['GET'])
@permission_classes([make_permission_class('INVOICE_VIEW')])
def revenue_summary(request):
    date_from = request.query_params.get('date_from')
    date_to = request.query_params.get('date_to')

    payments = Payment.objects.filter(is_deleted=False)
    if date_from:
        payments = payments.filter(payment_date__date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__date__lte=date_to)

    total = payments.aggregate(total=Sum('amount'))['total'] or 0
    by_method = {}
    for method in ['cash', 'mobile_money', 'bank_transfer', 'insurance', 'credit']:
        by_method[method] = str(payments.filter(payment_method=method).aggregate(total=Sum('amount'))['total'] or 0)

    invoices = Invoice.objects.filter(is_deleted=False)
    if date_from:
        invoices = invoices.filter(invoice_date__gte=date_from)
    if date_to:
        invoices = invoices.filter(invoice_date__lte=date_to)

    return Response({
        'total_revenue': str(total),
        'revenue_by_method': by_method,
        'total_invoices': invoices.count(),
        'pending_invoices': invoices.filter(status='pending').count(),
        'paid_invoices': invoices.filter(status='paid').count(),
        'partial_invoices': invoices.filter(status='partial').count(),
    })
