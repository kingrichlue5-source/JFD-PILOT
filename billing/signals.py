"""
Billing signals: immutable audit logging and deletion blocking.

Prevents deletion/modification of financial records (InvoiceLineItem, Payment)
and logs all changes to the AuditLog.
"""
import threading
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from .models import InvoiceLineItem, Payment
from audit.models import AuditLog

_thread_locals = threading.local()


def set_request_user(user):
    """Set the current request user on the thread local."""
    _thread_locals.user = user


def set_request_ip(ip):
    """Set the current request IP on the thread local."""
    _thread_locals.ip = ip


def get_request_user():
    """Get the current request user from thread local."""
    return getattr(_thread_locals, 'user', None)


def get_request_ip():
    """Get the current request IP from thread local."""
    return getattr(_thread_locals, 'ip', '127.0.0.1')


def _get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@receiver(pre_delete, sender=InvoiceLineItem)
def block_invoice_line_item_deletion(sender, instance, **kwargs):
    """Block deletion of invoice line items — financial records are immutable."""
    raise ValidationError(
        'Deletion of invoice line items is not permitted. '
        'Financial records are immutable for audit compliance.'
    )


@receiver(pre_delete, sender=Payment)
def block_payment_deletion(sender, instance, **kwargs):
    """Block deletion of payment records — financial records are immutable."""
    raise ValidationError(
        'Deletion of payment records is not permitted. '
        'Financial records are immutable for audit compliance.'
    )


@receiver(post_save, sender=InvoiceLineItem)
def log_invoice_line_item_changes(sender, instance, created, **kwargs):
    """Log all InvoiceLineItem changes to AuditLog."""
    user = get_request_user()
    action = 'CREATE' if created else 'UPDATE'
    AuditLog.objects.create(
        schema_name='billing',
        table_name='invoice_line_items',
        record_id=str(instance.id),
        action=action,
        old_values={},
        new_values={
            'invoice_id': str(instance.invoice_id),
            'service_item_id': str(instance.service_item_id),
            'description': instance.description,
            'quantity': str(instance.quantity),
            'unit_price': str(instance.unit_price),
            'total_amount': str(instance.total_amount),
            'payment_status': instance.payment_status,
            'paid_amount': str(instance.paid_amount),
        },
        user_id=str(user.id) if user else None,
        user_name=user.full_name if user else 'system',
        user_ip=get_request_ip(),
    )


@receiver(post_save, sender=Payment)
def log_payment_changes(sender, instance, created, **kwargs):
    """Log all Payment changes to AuditLog."""
    user = get_request_user()
    action = 'CREATE' if created else 'UPDATE'
    AuditLog.objects.create(
        schema_name='billing',
        table_name='payments',
        record_id=str(instance.id),
        action=action,
        old_values={},
        new_values={
            'invoice_id': str(instance.invoice_id),
            'patient_id': str(instance.patient_id),
            'amount': str(instance.amount),
            'payment_method': instance.payment_method,
            'receipt_number': instance.receipt_number,
        },
        user_id=str(user.id) if user else None,
        user_name=user.full_name if user else 'system',
        user_ip=get_request_ip(),
    )
