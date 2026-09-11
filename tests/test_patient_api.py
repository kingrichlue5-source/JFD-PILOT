"""
Tests for Patient API endpoints.
"""
import uuid
from datetime import date

from rest_framework import status

from .base import BaseTestCase


class PatientRegistrationTest(BaseTestCase):

    def test_create_patient_via_walkin(self):
        data = {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'date_of_birth': '1992-03-15',
            'gender': 'F',
            'phone': '+231-77-222-3333',
            'visit_type': 'opd',
            'chief_complaint': 'Stomach pain',
        }
        response = self.client.post('/api/patients/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertIn('patient', response.data)
        self.assertIn('visit', response.data)
        self.assertTrue(response.data['patient']['mrn'].startswith('JFD-'))
        self.assertEqual(response.data['visit']['status'], 'checked_in')

    def test_patient_mrn_format(self):
        patient = self._create_patient()
        import re
        self.assertRegex(patient.mrn, r'^JFD-\d{4}-\d{5}$')

    def test_patient_search_by_name(self):
        self._create_patient(first_name='Samuel', last_name='Doe')
        self._create_patient(first_name='Sarah', last_name='Doe')

        response = self.client.get('/api/patients/search/', {'q': 'Samuel'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['first_name'], 'Samuel')

    def test_patient_search_by_mrn(self):
        patient = self._create_patient(first_name='Search', last_name='Test')
        response = self.client.get('/api/patients/search/', {'q': patient.mrn})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_patient_search_minimum_query(self):
        response = self.client.get('/api/patients/search/', {'q': 'A'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_soft_delete_patient(self):
        patient = self._create_patient()
        response = self.client.delete(f'/api/patients/{patient.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        from patients.models import Patient
        patient.refresh_from_db()
        self.assertTrue(patient.is_deleted)

        response = self.client.get(f'/api/patients/{patient.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
