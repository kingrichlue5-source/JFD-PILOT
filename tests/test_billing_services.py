"""
Unit tests for billing/services.py functions.
"""
import uuid
from decimal import Decimal
from datetime import date

from .base import BaseTestCase


class BillingServicesTest(BaseTestCase):

    def test_generate_invoice_number_format(self):
        from billing.services import generate_invoice_number
        inv_num = generate_invoice_number()
        today_str = date.today().strftime('%Y%m%d')
        self.assertTrue(inv_num.startswith(f'JFD-INV-{today_str}-'))
        self.assertEqual(len(inv_num), len(f'JFD-INV-{today_str}-00001'))

    def test_generate_receipt_number_format(self):
        from billing.services import generate_receipt_number
        rec_num = generate_receipt_number()
        today_str = date.today().strftime('%Y%m%d')
        self.assertTrue(rec_num.startswith(f'REC-{today_str}-'))

    def test_lookup_service_price_self_pay(self):
        from billing.services import lookup_service_price
        price = lookup_service_price(self.svc_consult, 'self_pay')
        self.assertEqual(price, Decimal('500.00'))

    def test_lookup_service_price_unknown_category_falls_back(self):
        from billing.services import lookup_service_price
        price = lookup_service_price(self.svc_consult, 'nonexistent_category')
        self.assertEqual(price, Decimal('500.00'))

    def test_recalculate_invoice_totals(self):
        from billing.models import Invoice, InvoiceLineItem
        from billing.services import generate_invoice_number, recalculate_invoice_totals

        patient = self._create_patient()
        visit = self._create_visit(patient)

        invoice = Invoice.objects.create(
            invoice_number=generate_invoice_number(),
            patient=patient,
            visit=visit,
            payer_type='self_pay',
            status='pending',
        )

        InvoiceLineItem.objects.create(
            invoice=invoice,
            service_item=self.svc_consult,
            description='Consultation',
            quantity=Decimal('1'),
            unit_price=Decimal('500.00'),
            total_amount=Decimal('500.00'),
            payment_status='pending',
            paid_amount=Decimal('0.00'),
        )
        InvoiceLineItem.objects.create(
            invoice=invoice,
            service_item=self.svc_lab,
            description='Lab Test',
            quantity=Decimal('2'),
            unit_price=Decimal('250.00'),
            total_amount=Decimal('500.00'),
            payment_status='pending',
            paid_amount=Decimal('0.00'),
        )

        recalculate_invoice_totals(invoice)

        invoice.refresh_from_db()
        self.assertEqual(invoice.subtotal, Decimal('1000.00'))
        self.assertEqual(invoice.total_amount, Decimal('1000.00'))
        self.assertEqual(invoice.balance_due, Decimal('1000.00'))
        self.assertEqual(invoice.status, 'pending')

    def test_post_order_to_invoice_creates_line_item(self):
        from billing.services import post_order_to_invoice
        from billing.models import InvoiceLineItem

        patient = self._create_patient()
        visit = self._create_visit(patient)

        from clinical.models import Order
        order = Order.objects.create(
            visit=visit,
            patient=patient,
            order_type='laboratory',
            order_description='Malaria Test',
            priority='routine',
            ordering_provider=self.user_doctor,
            status='pending',
        )

        line_item = post_order_to_invoice(order, visit, patient)
        self.assertIsNotNone(line_item)
        self.assertIsInstance(line_item, InvoiceLineItem)
        self.assertGreater(line_item.total_amount, Decimal('0.00'))
        self.assertEqual(line_item.payment_status, 'pending')

    def test_post_prescription_item_to_invoice(self):
        from billing.services import post_prescription_item_to_invoice
        from billing.models import InvoiceLineItem
        from pharmacy.models import Prescription, PrescriptionItem

        patient = self._create_patient()
        visit = self._create_visit(patient)

        prescription = Prescription.objects.create(
            visit=visit,
            patient=patient,
            prescription_number=f'RX-TEST-{uuid.uuid4().hex[:6].upper()}',
            prescribed_by=self.user_doctor,
            status='pending',
        )

        prescription_item = PrescriptionItem.objects.create(
            prescription=prescription,
            medication=self.med_paracetamol,
            dosage='500mg',
            frequency='TDS',
            quantity_prescribed=Decimal('30'),
            quantity_dispensed=Decimal('0'),
        )

        line_item = post_prescription_item_to_invoice(prescription_item, visit, patient)
        self.assertIsNotNone(line_item)
        self.assertIsInstance(line_item, InvoiceLineItem)
        self.assertGreater(line_item.total_amount, Decimal('0.00'))
