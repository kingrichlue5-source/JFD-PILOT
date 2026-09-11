"""
Tests for Triage API endpoints and routing engine.
"""
from rest_framework import status

from .base import BaseTestCase


class TriageSubmitTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.patient = self._create_patient()
        self.visit = self._create_visit(self.patient, status='checked_in')

    def test_triage_submit_with_vitals(self):
        data = {
            'chief_complaint': 'Severe abdominal pain',
            'acuity_level': 2,
            'temperature': 38.5,
            'heart_rate': 95,
            'blood_pressure_systolic': 140,
            'blood_pressure_diastolic': 90,
        }
        response = self.client.post(
            f'/api/clinical/visits/{self.visit.id}/triage/submit/',
            data, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('triage_record', response.data)
        self.assertIn('routing', response.data)

        from clinical.models import TriageRecord
        record = TriageRecord.objects.get(visit=self.visit)
        self.assertEqual(record.acuity_level, 2)
        self.assertEqual(record.temperature, 38.5)

    def test_triage_routing_er_acuity_1(self):
        data = {
            'chief_complaint': 'Chest pain',
            'acuity_level': 1,
        }
        response = self.client.post(
            f'/api/clinical/visits/{self.visit.id}/triage/submit/',
            data, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['routing']['department'], 'ER')
        self.assertEqual(response.data['routing']['priority'], 'STAT')

    def test_triage_routing_er_acuity_2(self):
        data = {
            'chief_complaint': 'General weakness',
            'acuity_level': 2,
        }
        response = self.client.post(
            f'/api/clinical/visits/{self.visit.id}/triage/submit/',
            data, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['routing']['department'], 'ER')

    def test_triage_routing_obgyn_keywords(self):
        data = {
            'chief_complaint': 'Pregnant and having contractions',
            'acuity_level': 3,
        }
        response = self.client.post(
            f'/api/clinical/visits/{self.visit.id}/triage/submit/',
            data, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['routing']['department'], 'OBGYN')

    def test_triage_routing_opd_default(self):
        data = {
            'chief_complaint': 'Common cold and runny nose',
            'acuity_level': 4,
        }
        response = self.client.post(
            f'/api/clinical/visits/{self.visit.id}/triage/submit/',
            data, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['routing']['department'], 'OPD')
        self.assertEqual(response.data['routing']['priority'], 'ROUTINE')

    def test_invalid_status_transition_rejected(self):
        self.visit.status = 'completed'
        self.visit.save()

        response = self.client.patch(
            f'/api/clinical/visits/{self.visit.id}/status/',
            {'status': 'checked_in'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_triage_submit_wrong_status_rejected(self):
        self.visit.status = 'completed'
        self.visit.save()

        data = {'chief_complaint': 'Headache', 'acuity_level': 4}
        response = self.client.post(
            f'/api/clinical/visits/{self.visit.id}/triage/submit/',
            data, format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
