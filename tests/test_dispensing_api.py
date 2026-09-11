"""
Tests for Pharmacy Dispensing: payment gate, stock deduction, waiver.
"""
import uuid
from decimal import Decimal
from datetime import date, timedelta

from rest_framework import status

from .base import BaseTestCase


class DispensingTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.patient = self._create_patient()
        self.visit = self._create_visit(self.patient)

        from billing.models import Invoice, InvoiceLineItem
        from billing.services import generate_invoice_number, recalculate_invoice_totals

        self.invoice = Invoice.objects.create(
            invoice_number=generate_invoice_number(),
            patient=self.patient,
            visit=self.visit,
            payer_type='self_pay',
            status='pending',
        )
        self.line_item = InvoiceLineItem.objects.create(
            invoice=self.invoice,
            service_item=self.svc_pharm,
            description='Paracetamol 500mg',
            quantity=Decimal('15'),
            unit_price=Decimal('500.00'),
            total_amount=Decimal('7500.00'),
            payment_status='pending',
            paid_amount=Decimal('0.00'),
        )
        recalculate_invoice_totals(self.invoice)

        from pharmacy.models import Prescription, PrescriptionItem
        self.prescription = Prescription.objects.create(
            visit=self.visit,
            patient=self.patient,
            prescription_number=f'RX-{uuid.uuid4().hex[:10].upper()}',
            prescribed_by=self.user_doctor,
            status='pending',
        )
        self.prescription_item = PrescriptionItem.objects.create(
            prescription=self.prescription,
            medication=self.med_paracetamol,
            dosage='500mg',
            frequency='TDS',
            quantity_prescribed=Decimal('15'),
            quantity_dispensed=Decimal('0'),
            route='oral',
            status='pending',
        )
        self.line_item.prescription_item = self.prescription_item
        self.line_item.save()

    def _pay_invoice(self):
        from billing.services import recalculate_invoice_totals
        self.line_item.payment_status = 'paid'
        self.line_item.paid_amount = self.line_item.total_amount
        self.line_item.save()
        recalculate_invoice_totals(self.invoice)

    def test_dispense_blocked_without_payment(self):
        data = {
            'prescription_item_id': str(self.prescription_item.id),
            'quantity': 15,
            'batch_lot_number': 'BATCH-001',
            'store_id': str(self.store_main.id),
        }
        response = self.client.post('/api/pharmacy/dispense/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dispense_with_paid_prescription(self):
        self._pay_invoice()

        self.stock_paracetamol.refresh_from_db()
        stock_before = self.stock_paracetamol.quantity_on_hand

        data = {
            'prescription_item_id': str(self.prescription_item.id),
            'quantity': 15,
            'batch_lot_number': 'BATCH-001',
            'store_id': str(self.store_main.id),
        }
        response = self.client.post('/api/pharmacy/dispense/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        self.stock_paracetamol.refresh_from_db()
        self.assertEqual(stock_before - self.stock_paracetamol.quantity_on_hand, Decimal('15'))

    def test_stock_decremented_on_dispensing(self):
        self._pay_invoice()

        self.stock_paracetamol.refresh_from_db()
        initial_qty = self.stock_paracetamol.quantity_on_hand

        data = {
            'prescription_item_id': str(self.prescription_item.id),
            'quantity': 10,
            'batch_lot_number': 'BATCH-001',
            'store_id': str(self.store_main.id),
        }
        self.client.post('/api/pharmacy/dispense/', data, format='json')

        from inventory.models import StockMovement
        movement = StockMovement.objects.filter(
            item=self.item_paracetamol,
            movement_type='dispensed',
        ).latest('performed_at')
        self.assertEqual(movement.quantity, Decimal('10'))

        self.stock_paracetamol.refresh_from_db()
        self.assertEqual(self.stock_paracetamol.quantity_on_hand, initial_qty - Decimal('10'))

    def test_low_stock_warning_triggered(self):
        self._pay_invoice()

        self.stock_paracetamol.quantity_on_hand = Decimal('110')
        self.stock_paracetamol.save()

        data = {
            'prescription_item_id': str(self.prescription_item.id),
            'quantity': 15,
            'batch_lot_number': 'BATCH-001',
            'store_id': str(self.store_main.id),
        }
        response = self.client.post('/api/pharmacy/dispense/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('low_stock_warning', response.data)

    def test_dispense_expired_batch_rejected(self):
        self._pay_invoice()

        self.stock_paracetamol.expiry_date = date.today() - timedelta(days=1)
        self.stock_paracetamol.save()

        data = {
            'prescription_item_id': str(self.prescription_item.id),
            'quantity': 5,
            'batch_lot_number': 'BATCH-001',
            'store_id': str(self.store_main.id),
        }
        response = self.client.post('/api/pharmacy/dispense/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('expired', str(response.data).lower())

    def test_dispense_quantity_exceeds_prescribed(self):
        self._pay_invoice()

        data = {
            'prescription_item_id': str(self.prescription_item.id),
            'quantity': 20,
            'batch_lot_number': 'BATCH-001',
            'store_id': str(self.store_main.id),
        }
        response = self.client.post('/api/pharmacy/dispense/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
