"""
Tests for Order placement and auto fee posting.
"""
from decimal import Decimal

from rest_framework import status

from .base import BaseTestCase


class OrderAndBillingTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.patient = self._create_patient()
        self.visit = self._create_visit(self.patient, status='in_triage')

    def test_place_lab_order_creates_invoice_line(self):
        data = {
            'order_type': 'laboratory',
            'items': [{'description': 'Full Blood Count'}],
            'priority': 'routine',
        }
        response = self.client.post(
            f'/api/clinical/visits/{self.visit.id}/place-order/',
            data, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['total_orders'], 1)
        self.assertGreater(len(response.data['billing_items']), 0)

        from billing.models import InvoiceLineItem
        line_item_id = response.data['billing_items'][0]['line_item_id']
        line_item = InvoiceLineItem.objects.get(id=line_item_id)
        self.assertGreater(line_item.total_amount, Decimal('0.00'))
        self.assertEqual(line_item.payment_status, 'pending')

    def test_place_radiology_order_creates_invoice_line(self):
        data = {
            'order_type': 'radiology',
            'items': [{'description': 'Chest X-Ray'}],
            'priority': 'routine',
        }
        response = self.client.post(
            f'/api/clinical/visits/{self.visit.id}/place-order/',
            data, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertGreater(len(response.data['billing_items']), 0)

    def test_order_auto_fee_posting(self):
        data = {
            'order_type': 'laboratory',
            'items': [{'description': 'Malaria Test'}],
        }
        response = self.client.post(
            f'/api/clinical/visits/{self.visit.id}/place-order/',
            data, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        from billing.models import Invoice
        invoice = Invoice.objects.get(patient=self.patient, visit=self.visit, is_deleted=False)
        self.assertGreater(invoice.total_amount, Decimal('0.00'))
        self.assertEqual(invoice.status, 'pending')

    def test_visit_orders_summary(self):
        data = {
            'order_type': 'laboratory',
            'items': [
                {'description': 'Test A'},
                {'description': 'Test B'},
            ],
        }
        self.client.post(
            f'/api/clinical/visits/{self.visit.id}/place-order/',
            data, format='json',
        )

        response = self.client.get(
            f'/api/clinical/visits/{self.visit.id}/orders-summary/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_orders'], 2)

    def test_order_missing_fields_rejected(self):
        response = self.client.post(
            f'/api/clinical/visits/{self.visit.id}/place-order/',
            {'order_type': 'laboratory'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
