"""
Full Patient Journey Integration Test
Registration → Triage → Consultation → Lab Order → Pharmacy → Billing → Discharge
"""
import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import status

from .base import BaseTestCase


class FullPatientJourneyTest(BaseTestCase):
    """End-to-end patient journey through the hospital."""

    def test_complete_patient_journey(self):
        """Walk a patient through every department from registration to discharge."""

        # --- STEP 1+2: Registration + Walk-in Check-in ---
        resp = self.client.post('/api/patients/register/', {
            'first_name': 'Mary',
            'last_name': 'Johnson',
            'date_of_birth': '1985-06-20',
            'gender': 'F',
            'phone': '+231-77-123-4567',
            'payer_category': 'self_pay',
            'address': 'Monrovia, Liberia',
            'visit_type': 'opd',
            'chief_complaint': 'Persistent cough and mild fever for 3 days',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        patient_id = resp.data['patient']['id']
        mrn = resp.data['patient']['mrn']
        visit_id = resp.data['visit']['id']
        self.assertTrue(mrn.startswith('JFD-'))
        self.assertEqual(resp.data['visit']['status'], 'checked_in')
        print(f'Step 1+2 OK: Patient registered ({mrn}) + Visit created ({str(visit_id)[:8]}...)')

        # --- STEP 3: Triage ---
        resp = self.client.post(f'/api/clinical/visits/{visit_id}/triage/submit/', {
            'temperature': '37.8',
            'blood_pressure_systolic': '120',
            'blood_pressure_diastolic': '80',
            'heart_rate': '88',
            'respiratory_rate': '20',
            'oxygen_saturation': '97',
            'weight': '68',
            'height': '165',
            'chief_complaint': 'Persistent cough and mild fever for 3 days',
            'screening_notes': 'Patient appears mildly unwell, low-grade fever',
            'acuity_level': '3',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        print('Step 3 OK: Triage completed - Priority 3')

        # --- STEP 4: OPD Consultation (Create Encounter) ---
        resp = self.client.post(f'/api/clinical/visits/{visit_id}/encounters/', {
            'visit': visit_id,
            'patient': patient_id,
            'encounter_type': 'opd',
            'subjective': 'Patient reports cough for 3 days, low-grade fever, mild fatigue.',
            'assessment': 'Upper respiratory tract infection, likely viral',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        encounter_id = resp.data['id']
        print('Step 4 OK: Encounter created')

        # Record vital signs
        resp = self.client.post(f'/api/clinical/visits/{visit_id}/vitals/', {
            'visit': visit_id,
            'patient': patient_id,
            'encounter': encounter_id,
            'temperature': '37.8',
            'blood_pressure_systolic': '120',
            'blood_pressure_diastolic': '80',
            'heart_rate': '88',
            'respiratory_rate': '20',
            'oxygen_saturation': '97',
            'weight': '68',
            'height': '165',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        print('Step 4a OK: Vital signs recorded')

        # --- STEP 5: Diagnosis ---
        resp = self.client.post(f'/api/clinical/encounters/{encounter_id}/diagnoses/', {
            'encounter': encounter_id,
            'patient': patient_id,
            'visit': visit_id,
            'diagnosis_code': 'J06.9',
            'diagnosis_description': 'Acute upper respiratory infection, unspecified',
            'diagnosis_type': 'primary',
            'is_principal': True,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        print('Step 5 OK: Diagnosis recorded - J06.9')

        # --- STEP 6: Lab Order ---
        resp = self.client.post(f'/api/clinical/visits/{visit_id}/orders/', {
            'visit': visit_id,
            'patient': patient_id,
            'order_type': 'lab',
            'order_description': 'Complete Blood Count (CBC)',
            'priority': 'routine',
            'ordering_provider': self.user_doctor.id,
            'notes': 'Evaluate for infection',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        lab_order_id = resp.data['id']
        print('Step 6 OK: Lab order placed')

        # --- STEP 7: Lab Result ---
        resp = self.client.post(f'/api/clinical/visits/{visit_id}/diagnostic-results/', {
            'order': lab_order_id,
            'patient': patient_id,
            'visit': visit_id,
            'result_text': 'WBC 12.5 (elevated), Hemoglobin 13.2, Platelets 250 cells/uL',
            'is_abnormal': True,
            'notes': 'Slightly elevated WBC consistent with infection',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        print('Step 7 OK: Lab result recorded')

        # --- STEP 8: Treatment Plan (Progress Note) ---
        resp = self.client.post(f'/api/clinical/encounters/{encounter_id}/notes/', {
            'encounter': encounter_id,
            'patient': patient_id,
            'visit': visit_id,
            'note_type': 'assessment',
            'note_text': 'Assessment: Acute URTI. Plan: Amoxicillin 500mg TID x 7 days, Paracetamol PRN for fever.',
            'author': self.user_doctor.id,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        print('Step 8 OK: Progress note documented')

        # --- STEP 9: Prescription ---
        resp = self.client.post('/api/pharmacy/prescriptions/', {
            'visit': visit_id,
            'patient': patient_id,
            'prescribed_by': self.user_doctor.id,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        prescription_id = resp.data['id']
        print('Step 9 OK: Prescription created')

        # Add prescription items - post_prescription_item_to_invoice auto-creates billing line items
        resp = self.client.post(f'/api/pharmacy/prescriptions/{prescription_id}/items/', {
            'prescription': prescription_id,
            'medication': self.med_amoxicillin.id,
            'dosage': '500mg',
            'frequency': 'Three times daily',
            'duration': '7 days',
            'quantity_prescribed': 21,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        amox_item_id = resp.data['id']
        print('Step 9a OK: Amoxicillin 500mg x 21 added')

        resp = self.client.post(f'/api/pharmacy/prescriptions/{prescription_id}/items/', {
            'prescription': prescription_id,
            'medication': self.med_paracetamol.id,
            'dosage': '500mg',
            'frequency': 'As needed for fever',
            'duration': '7 days',
            'quantity_prescribed': 14,
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, resp.data)
        para_item_id = resp.data['id']
        print('Step 9b OK: Paracetamol 500mg x 14 added')

        # --- STEP 10: Billing ---
        # The prescription items auto-created line items + invoice via post_prescription_item_to_invoice.
        # Find that invoice and add a consultation line item.
        from billing.models import Invoice, InvoiceLineItem
        from billing.services import recalculate_invoice_totals

        invoice = Invoice.objects.filter(patient_id=patient_id, visit_id=visit_id).first()
        self.assertIsNotNone(invoice, 'Invoice should have been auto-created by prescription item billing')

        # Add consultation line item
        InvoiceLineItem.objects.create(
            invoice=invoice,
            service_item=self.svc_consult,
            description='OPD Consultation',
            unit_price=Decimal('500.00'),
            quantity=1,
            total_amount=Decimal('500.00'),
        )

        recalculate_invoice_totals(invoice)
        self.assertGreater(invoice.total_amount, Decimal('0.00'))
        print(f'Step 10 OK: Invoice total = ${invoice.total_amount}')

        # Verify line items exist for prescription items
        amox_line = InvoiceLineItem.objects.filter(invoice=invoice, prescription_item_id=amox_item_id).first()
        para_line = InvoiceLineItem.objects.filter(invoice=invoice, prescription_item_id=para_item_id).first()
        self.assertIsNotNone(amox_line, 'Amoxicillin line item should exist')
        self.assertIsNotNone(para_line, 'Paracetamol line item should exist')
        print('Step 10a OK: All line items accounted for')

        # --- STEP 11: Payment ---
        resp = self.client.post('/api/billing/pay/', {
            'invoice_id': invoice.id,
            'amount': str(invoice.total_amount),
            'payment_method': 'cash',
        }, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED], resp.data)
        print(f'Step 11 OK: Payment of ${invoice.total_amount} received')

        # Verify invoice is now paid
        invoice.refresh_from_db()
        self.assertEqual(invoice.status, 'paid')
        print('Step 11a OK: Invoice status = paid')

        # --- STEP 12: Pharmacy Dispensing ---
        resp = self.client.post('/api/pharmacy/dispense/', {
            'prescription_item_id': amox_item_id,
            'quantity': 21,
            'batch_lot_number': 'BATCH-002',
            'store_id': str(self.store_main.id),
        }, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED], resp.data)
        print('Step 12a OK: Amoxicillin dispensed')

        resp = self.client.post('/api/pharmacy/dispense/', {
            'prescription_item_id': para_item_id,
            'quantity': 14,
            'batch_lot_number': 'BATCH-001',
            'store_id': str(self.store_main.id),
        }, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED], resp.data)
        print('Step 12b OK: Paracetamol dispensed')

        # --- STEP 13: Discharge ---
        from clinical.models import Ward, Room, Bed, Admission
        ward, _ = Ward.objects.get_or_create(
            code='WARD_A', defaults={'name': 'Ward A', 'ward_type': 'general'}
        )
        room, _ = Room.objects.get_or_create(
            ward=ward, room_number='A-101', defaults={'room_type': 'general', 'capacity': 2}
        )
        bed, _ = Bed.objects.get_or_create(
            room=room, bed_number='A-101-A',
            defaults={'bed_type': 'general', 'is_occupied': False}
        )
        admission = Admission.objects.create(
            visit_id=visit_id,
            patient_id=patient_id,
            bed=bed,
            ward=ward,
            room=room,
            status='active',
            admitting_diagnosis='Persistent cough with fever',
            admitting_provider=self.user_doctor,
        )
        bed.is_occupied = True
        bed.save(update_fields=['is_occupied'])
        print('Step 13a OK: Patient admitted to bed')

        resp = self.client.post(f'/api/clinical/admissions/{admission.id}/discharge/', {
            'discharge_type': 'routine',
            'discharge_summary': 'Patient improved. Continue medications at home. Follow up in 1 week.',
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp.data)
        print('Step 13b OK: Patient discharged')

        # Verify
        admission.refresh_from_db()
        self.assertEqual(admission.status, 'discharged')
        bed.refresh_from_db()
        self.assertFalse(bed.is_occupied)

        resp = self.client.get(f'/api/clinical/visits/{visit_id}/')
        self.assertEqual(resp.data['status'], 'completed')
        print('Step 13c OK: Visit completed, bed freed')

        print('\n=== FULL PATIENT JOURNEY COMPLETED SUCCESSFULLY ===')
        print(f'Patient: {mrn}')
        print('Journey: Registration -> Triage -> Consultation -> Lab -> Pharmacy -> Billing -> Discharge')
