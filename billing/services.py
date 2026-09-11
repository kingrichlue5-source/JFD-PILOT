from datetime import date
from decimal import Decimal
from django.db.models import Q, Count, Sum
from django.utils import timezone

from .models import (
    Invoice, InvoiceLineItem, ServiceItem, ServicePrice, PriceList,
    PaymentStatus as LinePaymentStatus
)


def generate_invoice_number():
    from jfd_hms.utils import generate_sequence_number
    today = date.today()
    prefix = f"JFD-INV-{today.strftime('%Y%m%d')}-"
    return generate_sequence_number(prefix, Invoice, 'invoice_number')


def generate_receipt_number():
    from jfd_hms.utils import generate_sequence_number
    today = date.today()
    prefix = f"REC-{today.strftime('%Y%m%d')}-"
    from .models import Payment
    return generate_sequence_number(prefix, Payment, 'receipt_number')


def get_or_create_active_invoice(patient, visit):
    invoice = Invoice.objects.filter(
        patient=patient,
        visit=visit,
        is_deleted=False,
        status__in=['pending', 'partial']
    ).first()

    if invoice:
        return invoice

    invoice = Invoice.objects.create(
        invoice_number=generate_invoice_number(),
        patient=patient,
        visit=visit,
        payer_type=getattr(patient, 'payer_category', None) or 'self_pay',
        status='pending'
    )
    return invoice


def post_registration_fee_to_invoice(patient, visit):
    from users_auth.models import HospitalSetting
    setting = HospitalSetting.get_settings()
    fee = setting.registration_fee
    if fee <= 0:
        return None
    reg_item = ServiceItem.objects.filter(code='REG', is_active=True).first()
    if not reg_item:
        return None
    invoice = get_or_create_active_invoice(patient, visit)
    already_charged = InvoiceLineItem.objects.filter(
        invoice=invoice, service_item=reg_item
    ).exists()
    if already_charged:
        return None
    line = InvoiceLineItem.objects.create(
        invoice=invoice,
        service_item=reg_item,
        description='Registration Fee',
        quantity=1,
        unit_price=fee,
        total_amount=fee,
        payment_status='pending'
    )
    invoice.subtotal = sum(li.total_amount for li in InvoiceLineItem.objects.filter(invoice=invoice))
    invoice.total_amount = invoice.subtotal - invoice.discount_amount + invoice.tax_amount
    invoice.balance_due = invoice.total_amount - invoice.amount_paid
    invoice.save()
    return line


def lookup_service_price(service_item, payer_category=None):
    today = timezone.now().date()

    price_query = ServicePrice.objects.filter(
        service_item=service_item,
        effective_date__lte=today
    ).filter(
        Q(expiry_date__isnull=True) | Q(expiry_date__gte=today)
    )

    if payer_category:
        specific_price = price_query.filter(
            payer_category=payer_category
        ).order_by('-effective_date').first()
        if specific_price:
            return specific_price.price

    default_price = price_query.filter(
        Q(payer_category__isnull=True) | Q(payer_category='')
    ).order_by('-effective_date').first()
    if default_price:
        return default_price.price

    any_price = price_query.order_by('-effective_date').first()
    if any_price:
        return any_price.price

    return Decimal('0.00')


def find_service_item_for_order(order):
    order_type = order.order_type
    description = (order.order_description or '').upper()

    if order_type in ('laboratory', 'lab'):
        item = ServiceItem.objects.filter(
            code__startswith='LAB_',
            is_active=True
        ).filter(
            Q(name__icontains=description[:30]) | Q(code__icontains=description[:20])
        ).first()
        if item:
            return item
        return ServiceItem.objects.filter(code='LAB_TEST', is_active=True).first() or \
               ServiceItem.objects.filter(category='Laboratory', is_active=True).first()

    elif order_type == 'radiology':
        item = ServiceItem.objects.filter(
            code__startswith='RAD_',
            is_active=True
        ).filter(
            Q(name__icontains=description[:30]) | Q(code__icontains=description[:20])
        ).first()
        if item:
            return item
        return ServiceItem.objects.filter(code='RAD_TEST', is_active=True).first() or \
               ServiceItem.objects.filter(category='Radiology', is_active=True).first()

    elif order_type == 'consultation':
        return ServiceItem.objects.filter(code='CONSULT', is_active=True).first()

    elif order_type == 'pharmacy':
        return ServiceItem.objects.filter(code__startswith='PHARM_', is_active=True).first() or \
               ServiceItem.objects.filter(code='PHARM', is_active=True).first()

    return ServiceItem.objects.filter(code='SERVICE', is_active=True).first() or \
           ServiceItem.objects.filter(is_billable=True, is_active=True).first()


def find_service_item_for_medication(medication):
    if medication.medication_code:
        item = ServiceItem.objects.filter(
            code=f"PHARM_{medication.medication_code}",
            is_active=True
        ).first()
        if item:
            return item

    item = ServiceItem.objects.filter(
        code__startswith='PHARM_',
        is_active=True
    ).filter(
        Q(name__icontains=medication.name[:30])
    ).first()
    if item:
        return item

    return ServiceItem.objects.filter(code='PHARM', is_active=True).first()


def post_order_to_invoice(order, visit, patient):
    service_item = find_service_item_for_order(order)
    if not service_item:
        return None

    payer_category = getattr(patient, 'payer_category', None) or 'self_pay'
    unit_price = lookup_service_price(service_item, payer_category)

    if unit_price <= 0:
        return None

    invoice = get_or_create_active_invoice(patient, visit)

    existing = InvoiceLineItem.objects.filter(
        invoice=invoice,
        order=order
    ).first()
    if existing:
        return existing

    quantity = Decimal('1.00')
    total_amount = unit_price * quantity

    line_item = InvoiceLineItem.objects.create(
        invoice=invoice,
        service_item=service_item,
        description=order.order_description or f"{order.order_type} order",
        quantity=quantity,
        unit_price=unit_price,
        total_amount=total_amount,
        payment_status='pending',
        paid_amount=Decimal('0.00'),
        order=order
    )

    recalculate_invoice_totals(invoice)

    return line_item


def post_prescription_item_to_invoice(prescription_item, visit, patient):
    medication = prescription_item.medication
    service_item = find_service_item_for_medication(medication)
    if not service_item:
        return None

    payer_category = getattr(patient, 'payer_category', None) or 'self_pay'
    unit_price = lookup_service_price(service_item, payer_category)

    if unit_price <= 0:
        return None

    invoice = get_or_create_active_invoice(patient, visit)

    existing = InvoiceLineItem.objects.filter(
        invoice=invoice,
        prescription_item=prescription_item
    ).first()
    if existing:
        return existing

    quantity = Decimal(str(prescription_item.quantity_prescribed))
    total_amount = unit_price * quantity

    line_item = InvoiceLineItem.objects.create(
        invoice=invoice,
        service_item=service_item,
        description=f"{medication.name} {medication.strength or ''} {medication.dosage_form or ''}".strip(),
        quantity=quantity,
        unit_price=unit_price,
        total_amount=total_amount,
        payment_status='pending',
        paid_amount=Decimal('0.00'),
        prescription_item=prescription_item
    )

    recalculate_invoice_totals(invoice)

    return line_item


def recalculate_invoice_totals(invoice):
    from .models import Payment
    line_items = InvoiceLineItem.objects.filter(invoice=invoice)

    subtotal = sum(item.total_amount for item in line_items)
    amount_paid = Payment.objects.filter(
        invoice=invoice, is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    invoice.subtotal = subtotal
    invoice.tax_amount = Decimal('0.00')
    invoice.total_amount = subtotal
    invoice.amount_paid = amount_paid
    invoice.balance_due = invoice.total_amount - invoice.amount_paid

    if invoice.balance_due <= 0:
        invoice.status = 'paid'
    elif invoice.amount_paid > 0:
        invoice.status = 'partial'
    else:
        invoice.status = 'pending'

    invoice.save()
