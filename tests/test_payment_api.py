"""
Tests for Payment processing and receipt generation.
"""
import uuid
from decimal import Decimal

from rest_framework import status

from .base import BaseTestCase


class PaymentProcessTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.patient = self._create_patient()
        self.visit = self._create_visit(self.patient)
        self.invoice = self._create_invoice(self.patient, self.visit)

        from billing.models import InvoiceLineItem
        self.line_item = InvoiceLineItem.objects.create(
            invoice=self.invoice,
            service_item=self.svc_lab,
            description='Lab Test',
            quantity=Decimal('1'),
            unit_price=Decimal('500.00'),
            total_amount=Decimal('500.00'),
            payment_status='pending',
            paid_amount=Decimal('0.00'),
        )
        from billing.services import recalculate_invoice_totals
        recalculate_invoice_totals(self.invoice)

    def test_process_payment_creates_receipt(self):
        data = {
            'invoice_id': str(self.invoice.id),
            'amount': str(self.invoice.total_amount),
            'payment_method': 'cash',
        }
        response = self.client.post('/api/billing/pay/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIn('receipt_number', response.data)
        self.assertTrue(response.data['receipt_number'].startswith('REC-'))

    def test_payment_marks_line_items_paid(self):
        data = {
            'invoice_id': str(self.invoice.id),
            'amount': str(self.invoice.total_amount),
            'payment_method': 'cash',
        }
        self.client.post('/api/billing/pay/', data, format='json')

        self.line_item.refresh_from_db()
        self.assertEqual(self.line_item.payment_status, 'paid')
        self.assertEqual(self.line_item.paid_amount, self.line_item.total_amount)

    def test_payment_updates_invoice_status(self):
        data = {
            'invoice_id': str(self.invoice.id),
            'amount': str(self.invoice.total_amount),
            'payment_method': 'cash',
        }
        self.client.post('/api/billing/pay/', data, format='json')

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'paid')
        self.assertEqual(self.invoice.balance_due, Decimal('0.00'))

    def test_partial_payment(self):
        data = {
            'invoice_id': str(self.invoice.id),
            'amount': '250.00',
            'payment_method': 'cash',
        }
        response = self.client.post('/api/billing/pay/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.status, 'partial')
        self.assertEqual(self.invoice.balance_due, Decimal('250.00'))

        self.line_item.refresh_from_db()
        self.assertEqual(self.line_item.payment_status, 'partial')

    def test_receipt_detail_endpoint(self):
        data = {
            'invoice_id': str(self.invoice.id),
            'amount': str(self.invoice.total_amount),
            'payment_method': 'cash',
        }
        response = self.client.post('/api/billing/pay/', data, format='json')
        receipt_number = response.data['receipt_number']

        response = self.client.get(f'/api/billing/receipts/{receipt_number}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['invoice']['status'], 'paid')

    def test_payment_missing_fields_rejected(self):
        response = self.client.post('/api/billing/pay/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_payment_nonexistent_invoice(self):
        data = {
            'invoice_id': str(uuid.uuid4()),
            'amount': '100.00',
            'payment_method': 'cash',
        }
        response = self.client.post('/api/billing/pay/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_payment_negative_amount_rejected(self):
        data = {
            'invoice_id': str(self.invoice.id),
            'amount': '-100.00',
            'payment_method': 'cash',
        }
        response = self.client.post('/api/billing/pay/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
