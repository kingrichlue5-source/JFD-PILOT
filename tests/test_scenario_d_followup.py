"""
Scenario D: Multi-Visit Follow-up

Validates that a returning patient can create a follow-up visit (is_follow_up=True),
get triaged, be consulted (SOAP + diagnosis finalized), discharged with a scheduled
follow-up appointment, and that the appointment can be rescheduled from the dashboard.
"""
from datetime import date, timedelta

from rest_framework import status

from .base import BaseTestCase


class ScenarioDFollowUpTest(BaseTestCase):
    """Automated validation of Scenario D: Multi-Visit Follow-up."""

    def test_multi_visit_follow_up_flow(self):
        # ── Patient with an initial (original) visit ─────────────────
        patient = self._create_patient(
            first_name='Jackson',
            last_name='Kofa',
            gender='M',
            date_of_birth=date(1995, 3, 10),
            phone='+231-77-555-0001',
        )
        first_visit = self._create_visit(
            patient,
            visit_type='opd',
            chief_complaint='Persistent headache for 3 days',
            status='completed',
        )
        self.assertFalse(first_visit.is_follow_up)

        # ── STEP 1: Create a follow-up visit for the EXISTING patient ─
        follow_up_date = date.today()
        create_data = {
            'patient': str(patient.id),
            'visit_type': 'opd',
            'chief_complaint': 'Follow up for headache. Feeling much better.',
            'is_follow_up': True,
            'follow_up_date': follow_up_date.isoformat(),
        }
        response = self.client.post(
            '/api/clinical/visits/',
            create_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        follow_up = response.data
        self.assertIn('id', follow_up)
        self.assertTrue(follow_up.get('is_follow_up') is True, "is_follow_up should be True")
        self.assertEqual(follow_up.get('follow_up_date'), follow_up_date.isoformat())
        self.assertEqual(follow_up.get('visit_type'), 'opd')
        self.assertEqual(follow_up.get('chief_complaint'), 'Follow up for headache. Feeling much better.')

        # Verify new visit persisted as follow-up
        from clinical.models import Visit
        follow_visit = Visit.objects.get(id=follow_up['id'])
        self.assertTrue(follow_visit.is_follow_up)
        self.assertEqual(follow_visit.follow_up_date, follow_up_date)
        self.assertTrue(follow_visit.visit_number.startswith('VIS-'))

        # ── Check in (scheduled -> checked_in) so triage is possible ─
        if follow_visit.status != 'checked_in':
            response = self.client.patch(
                f'/api/clinical/visits/{follow_visit.id}/status/',
                {'status': 'checked_in'},
                format='json',
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
            self.assertEqual(response.data['status'], 'checked_in')

        # ── STEP 2: Triage (abbreviated for follow-up) ───────────────
        triage_data = {
            'chief_complaint': 'Follow up for headache. Feeling much better.',
            'acuity_level': 5,
            'temperature': '36.8',
            'heart_rate': 76,
            'respiratory_rate': 16,
            'blood_pressure_systolic': 122,
            'blood_pressure_diastolic': 78,
            'oxygen_saturation': '99.0',
            'pain_scale': 1,
            'screening_notes': 'Routine follow-up, stable.',
        }
        response = self.client.post(
            f'/api/clinical/visits/{follow_visit.id}/triage/submit/',
            triage_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertEqual(response.data['triage_record']['heart_rate'], 76)
        self.assertEqual(response.data['visit']['status'], 'in_progress')

        # ── STEP 3: Doctor follow-up consultation (SOAP + diagnosis) ─
        encounter_data = {
            'encounter_type': 'opd',
            'subjective': 'Patient reports significant improvement. Headache resolved. No fever x48hrs.',
            'objective': 'T:36.8, HR:76, BP:122/78. Appearance well. Throat clear.',
            'assessment': 'Resolving viral illness. Hydration status improved.',
            'plan': '1. No new labs needed 2. Continue ORS PRN 3. Discharge',
        }
        response = self.client.post(
            f'/api/clinical/visits/{follow_visit.id}/encounters/',
            encounter_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        encounter_id = response.data['id']
        self.assertEqual(str(response.data['visit']), str(follow_visit.id))

        # Finalize the encounter with primary diagnosis
        finalize_data = {
            'diagnosis_primary': 'Resolving viral illness',
            'subjective': encounter_data['subjective'],
            'objective': encounter_data['objective'],
            'assessment': encounter_data['assessment'],
            'plan': encounter_data['plan'],
        }
        response = self.client.post(
            f'/api/clinical/encounters/{encounter_id}/finalize/',
            finalize_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(response.data['is_finalized'])
        self.assertEqual(response.data['diagnosis_primary'], 'Resolving viral illness')

        # ── STEP 4: Discharge creates scheduled follow-up appointment ─
        follow_up_appt_date = (date.today() + timedelta(weeks=2)).isoformat()
        appointment_data = {
            'patient': str(patient.id),
            'appointment_date': follow_up_appt_date,
            'appointment_time': '09:00',
            'duration_minutes': 30,
            'appointment_type': 'follow_up',
            'reason': 'Post-treatment review',
            'linked_visit': str(follow_visit.id),
            'status': 'scheduled',
        }
        response = self.client.post(
            '/api/clinical/appointments/',
            appointment_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        appt = response.data
        self.assertEqual(appt['appointment_type'], 'follow_up')
        self.assertEqual(appt['status'], 'scheduled')
        self.assertEqual(appt['appointment_date'], follow_up_appt_date)
        self.assertEqual(str(appt['linked_visit']), str(follow_visit.id))

        # ── Verify the appointment appears in the list ───────────────
        response = self.client.get('/api/clinical/appointments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        appts = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        matching = [a for a in appts if a['id'] == appt['id']]
        self.assertEqual(len(matching), 1, "Follow-up appointment should be in the list")

        # ── STEP 5: Reschedule the appointment ───────────────────────
        new_date = (date.today() + timedelta(weeks=3)).isoformat()
        response = self.client.patch(
            f'/api/clinical/appointments/{appt["id"]}/',
            {
                'appointment_date': new_date,
                'appointment_time': '10:00',
                'status': 'rescheduled',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['appointment_date'], new_date)
        self.assertEqual(response.data['appointment_time'][:5], '10:00')
        self.assertEqual(response.data['status'], 'rescheduled')

        # ── STEP 6: Patient returns — Check In creates a new Visit ───
        # Reset appointment to scheduled for check-in (simulates new date)
        response = self.client.patch(
            f'/api/clinical/appointments/{appt["id"]}/',
            {'status': 'scheduled'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        # Check In: creates a Visit and links it to the appointment
        new_visit_data = {
            'patient': str(patient.id),
            'visit_type': 'opd',
            'chief_complaint': appointment_data.get('reason', 'Follow-up visit'),
            'is_follow_up': True,
        }
        response = self.client.post(
            '/api/clinical/visits/',
            new_visit_data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        new_visit_id = response.data['id']

        # Link the visit to the appointment and set checked_in
        response = self.client.patch(
            f'/api/clinical/appointments/{appt["id"]}/',
            {'visit': new_visit_id, 'status': 'checked_in'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(str(response.data['visit']), new_visit_id)
        self.assertEqual(response.data['status'], 'checked_in')

        # Auto-check-in the visit
        response = self.client.patch(
            f'/api/clinical/visits/{new_visit_id}/status/',
            {'status': 'checked_in'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data['status'], 'checked_in')

        # ── Verify patient chart shows 3 visits ──────────────────────
        response = self.client.get(f'/api/clinical/visits/?patient={patient.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        visits = response.data.get('results', response.data) if isinstance(response.data, dict) else response.data
        self.assertEqual(len(visits), 3, "Patient chart should show 3 visits (original + 2 follow-ups)")
        follow_ups = [v for v in visits if v.get('is_follow_up')]
        self.assertEqual(len(follow_ups), 2, "Two follow-up visits")
