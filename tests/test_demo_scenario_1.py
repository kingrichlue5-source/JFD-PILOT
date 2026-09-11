"""
Full integration test: Patient -> Triage -> Order -> Billing -> Payment -> Dispensing

Validates the complete Recommended Demonstration Scenario 1.
"""
import uuid
from decimal import Decimal
from datetime import date

from rest_framework import status

from .base import BaseTestCase


class DemonstrationScenario1Test(BaseTestCase):
    """
    Automated validation of Recommended Demonstration Scenario 1:
    Patient Registration -> Triage -> Lab Order -> Payment -> Pharmacy Dispensing
    """

    def test_full_clinical_to_billing_to_dispensing_flow(self):
        # ── STEP 1: Patient Registration ──────────────────────────────
        patient = self._create_patient(
            first_name='Martha',
            last_name='Tolbert',
            gender='F',
            date_of_birth=date(1985, 6, 20),
            phone='+231-77-111-2222',
        )
        self.assertIsNotNone(patient.id)
        self.assertTrue(patient.mrn.startswith('JFD-'), f"MRN should start with JFD-, got {patient.mrn}")
        self.assertEqual(patient.first_name, 'Martha')
        self.assertEqual(patient.gender, 'F')

        # ── STEP 2: Create Visit (walk-in registration) ───────────────
        visit = self._create_visit(
            patient,
            visit_type='opd',
            chief_complaint='Persistent headache for 3 days',
            status='checked_in',
        )
        self.assertIsNotNone(visit.id)
        self.assertTrue(visit.visit_number.startswith('VIS-'))
        self.assertEqual(visit.status, 'checked_in')

        # ── STEP 3: Triage Submission ─────────────────────────────────
        triage_data = {
            'chief_complaint': 'Persistent headache for 3 days, mild fever',
            'acuity_level': 3,
            'temperature': Decimal('37.8'),
            'heart_rate': 82,
            'respiratory_rate': 18,
            'blood_pressure_systolic': 128,
            'blood_pressure_diastolic': 82,
            'oxygen_saturation': Decimal('98.0'),
            'weight': Decimal('68.5'),
            'height': Decimal('165.0'),
            'pain_scale': 5,
            'blood_glucose': 95,
            'screening_notes': 'Patient reports throbbing headache, worse in the morning.',
        }

        response = self.client.post(
            f'/api/clinical/visits/{visit.id}/triage/submit/',
            triage_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        triage_resp = response.data
        self.assertIn('triage_record', triage_resp)
        self.assertIn('routing', triage_resp)
        self.assertEqual(triage_resp['triage_record']['acuity_level'], 3)
        self.assertEqual(triage_resp['routing']['department'], 'OPD')

        # Verify visit status updated
        visit.refresh_from_db()
        self.assertEqual(visit.status, 'in_progress')
        self.assertEqual(visit.triage_priority, '3')

        # ── STEP 4: Place Lab Order ───────────────────────────────────
        order_data = {
            'order_type': 'laboratory',
            'items': [
                {'description': 'Full Blood Count (FBC)'},
            ],
            'clinical_indication': 'Persistent headache, fever',
            'priority': 'routine',
        }

        response = self.client.post(
            f'/api/clinical/visits/{visit.id}/place-order/',
            order_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        order_resp = response.data
        self.assertEqual(order_resp['total_orders'], 1)
        self.assertGreater(len(order_resp['billing_items']), 0)

        # Verify billing line item was auto-created
        billing_item = order_resp['billing_items'][0]
        self.assertIn('line_item_id', billing_item)
        self.assertIn('amount', billing_item)
        self.assertEqual(billing_item['payment_status'], 'pending')

        # ── STEP 5: Verify Invoice was created ────────────────────────
        from billing.models import Invoice, InvoiceLineItem

        invoices = Invoice.objects.filter(patient=patient, visit=visit, is_deleted=False)
        self.assertEqual(invoices.count(), 1, "Exactly one invoice should be created")
        invoice = invoices.first()
        self.assertEqual(invoice.status, 'pending')
        self.assertGreater(invoice.total_amount, Decimal('0.00'))

        line_items = InvoiceLineItem.objects.filter(invoice=invoice)
        self.assertGreater(line_items.count(), 0, "Invoice should have line items")
        line_item = line_items.first()
        self.assertEqual(line_item.payment_status, 'pending')

        # ── STEP 6: Process Payment ───────────────────────────────────
        payment_data = {
            'invoice_id': str(invoice.id),
            'amount': str(invoice.total_amount),
            'payment_method': 'cash',
        }

        response = self.client.post(
            '/api/billing/pay/',
            payment_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        pay_resp = response.data
        self.assertIn('receipt_number', pay_resp)
        self.assertTrue(pay_resp['receipt_number'].startswith('REC-'))
        self.assertEqual(pay_resp['invoice_status'], 'paid')
        self.assertEqual(Decimal(pay_resp['balance_due']), Decimal('0.00'))

        # Verify invoice updated
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
        self.assertEqual(invoice.balance_due, Decimal('0.00'))

        # Verify line item updated
        line_item.refresh_from_db()
        self.assertEqual(line_item.payment_status, 'paid')
        self.assertEqual(line_item.paid_amount, line_item.total_amount)

        # ── STEP 7: Create Prescription + Dispense ────────────────────
        from pharmacy.models import Prescription, PrescriptionItem

        prescription = Prescription.objects.create(
            visit=visit,
            patient=patient,
            prescription_number=f'RX-{uuid.uuid4().hex[:10].upper()}',
            prescribed_by=self.user_doctor,
            status='pending',
        )

        prescription_item = PrescriptionItem.objects.create(
            prescription=prescription,
            medication=self.med_paracetamol,
            dosage='500mg',
            frequency='TDS',
            duration='5 days',
            quantity_prescribed=Decimal('15'),
            quantity_dispensed=Decimal('0'),
            route='oral',
        )

        # Post prescription item to billing
        from billing.services import post_prescription_item_to_invoice
        post_prescription_item_to_invoice(prescription_item, visit, patient)

        # Mark billing as paid for dispensing gate
        from billing.models import InvoiceLineItem
        pharma_line = InvoiceLineItem.objects.filter(prescription_item=prescription_item).first()
        if pharma_line:
            pharma_line.payment_status = 'paid'
            pharma_line.paid_amount = pharma_line.total_amount
            pharma_line.save()
            from billing.services import recalculate_invoice_totals
            recalculate_invoice_totals(pharma_line.invoice)

        # Record stock before dispensing
        self.stock_paracetamol.refresh_from_db()
        stock_before = self.stock_paracetamol.quantity_on_hand

        # Dispense
        dispense_data = {
            'prescription_item_id': str(prescription_item.id),
            'quantity': 15,
            'batch_lot_number': 'BATCH-001',
            'store_id': str(self.store_main.id),
        }

        response = self.client.post(
            '/api/pharmacy/dispense/',
            dispense_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        dispense_resp = response.data
        self.assertEqual(float(dispense_resp['quantity_dispensed']), 15.0)

        # Verify stock decremented
        self.stock_paracetamol.refresh_from_db()
        stock_after = self.stock_paracetamol.quantity_on_hand
        self.assertEqual(stock_before - stock_after, Decimal('15'))

        # Verify prescription item updated
        prescription_item.refresh_from_db()
        self.assertEqual(prescription_item.quantity_dispensed, Decimal('15'))
        self.assertEqual(prescription_item.status, 'completed')

        # Verify StockMovement created
        from inventory.models import StockMovement
        movements = StockMovement.objects.filter(
            item=self.item_paracetamol,
            store=self.store_main,
            movement_type='dispensed',
            reference_id=prescription_item.id,
        )
        self.assertEqual(movements.count(), 1)

        # ── STEP 8: Verify Receipt ────────────────────────────────────
        receipt_number = pay_resp['receipt_number']
        response = self.client.get(f'/api/billing/receipts/{receipt_number}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        receipt_resp = response.data
        self.assertEqual(receipt_resp['invoice']['invoice_number'], invoice.invoice_number)
        self.assertEqual(receipt_resp['invoice']['status'], 'paid')
