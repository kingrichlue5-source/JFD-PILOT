from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Patient, PatientAllergy, PatientAlert, PatientDocument
from .serializers import (
    PatientSerializer, PatientCreateSerializer, PatientSearchSerializer,
    PatientAllergySerializer, PatientAlertSerializer, PatientDocumentSerializer
)
from jfd_hms.permissions import require_permission, make_permission_class


class PatientListView(generics.ListCreateAPIView):
    queryset = Patient.objects.filter(is_deleted=False)
    permission_classes = [make_permission_class('PATIENT_VIEW')]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PatientCreateSerializer
        return PatientSerializer

    def get_queryset(self):
        queryset = Patient.objects.filter(is_deleted=False)
        search = self.request.query_params.get('search', None)
        status_filter = self.request.query_params.get('status', None)
        gender = self.request.query_params.get('gender', None)
        insurance = self.request.query_params.get('insurance', None)

        if search:
            queryset = queryset.filter(
                Q(mrn__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if gender:
            queryset = queryset.filter(gender=gender)

        if insurance:
            queryset = queryset.filter(insurance_provider__icontains=insurance)

        return queryset.order_by('-created_at')


class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.filter(is_deleted=False)
    serializer_class = PatientSerializer
    permission_classes = [make_permission_class('PATIENT_VIEW')]

    def destroy(self, request, *args, **kwargs):
        from audit.utils import log_audit
        patient = self.get_object()
        old_values = {'is_deleted': False, 'mrn': patient.mrn}
        patient.is_deleted = True
        patient.save()
        log_audit('patients', 'patients', patient.id, 'DELETE',
                  old_values=old_values,
                  new_values={'is_deleted': True, 'mrn': patient.mrn},
                  request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([make_permission_class('PATIENT_VIEW')])
def patient_search(request):
    query = request.query_params.get('q', '')
    if len(query) < 2:
        return Response([])

    patients = Patient.objects.filter(
        Q(mrn__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(phone__icontains=query) |
        Q(email__icontains=query)
    ).filter(is_deleted=False)[:10]

    serializer = PatientSearchSerializer(patients, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([make_permission_class('PATIENT_CREATE')])
def walk_in_registration_api(request):
    from audit.utils import log_audit
    data = request.data.copy()

    serializer = PatientCreateSerializer(data=data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user if request.user.is_authenticated else None
    patient = serializer.save(registered_by=user.id if user else None)

    from clinical.models import Visit
    visit = Visit.objects.create(
        patient=patient,
        visit_type=data.get('visit_type', 'opd'),
        chief_complaint=data.get('chief_complaint', ''),
        status='checked_in',
        check_in_time=timezone.now(),
        created_by=user.id if user else None
    )

    log_audit('patients', 'patients', patient.id, 'CREATE',
              new_values={'mrn': patient.mrn, 'first_name': patient.first_name, 'last_name': patient.last_name},
              request=request)
    log_audit('clinical', 'visits', visit.id, 'CREATE',
              new_values={'visit_number': visit.visit_number, 'visit_type': visit.visit_type, 'status': visit.status},
              request=request)

    from billing.services import post_registration_fee_to_invoice
    post_registration_fee_to_invoice(patient, visit)

    return Response({
        'patient': PatientSerializer(patient).data,
        'visit': {
            'id': str(visit.id),
            'visit_number': visit.visit_number,
            'visit_type': visit.visit_type,
            'status': visit.status,
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([make_permission_class('PATIENT_MERGE')])
def merge_patients(request):
    primary_id = request.data.get('primary_patient_id')
    secondary_id = request.data.get('secondary_patient_id')

    if not primary_id or not secondary_id:
        return Response({'error': 'Both patient IDs required'}, status=status.HTTP_400_BAD_REQUEST)

    if primary_id == secondary_id:
        return Response({'error': 'Cannot merge a patient with themselves'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        primary = Patient.objects.get(id=primary_id, is_deleted=False)
        secondary = Patient.objects.get(id=secondary_id, is_deleted=False)
    except Patient.DoesNotExist:
        return Response({'error': 'Patient not found'}, status=status.HTTP_404_NOT_FOUND)

    secondary.merged_into = primary
    secondary.status = 'merged'
    secondary.save()

    return Response({'message': 'Patients merged successfully', 'primary_mrn': primary.mrn})


class PatientAllergyListView(generics.ListCreateAPIView):
    serializer_class = PatientAllergySerializer
    permission_classes = [make_permission_class('PATIENT_VIEW')]

    def get_queryset(self):
        return PatientAllergy.objects.filter(patient_id=self.kwargs['patient_id'])

    def perform_create(self, serializer):
        serializer.save(patient_id=self.kwargs['patient_id'], recorded_by=self.request.user.id if self.request.user.is_authenticated else None)


class PatientAllergyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PatientAllergy.objects.all()
    serializer_class = PatientAllergySerializer
    permission_classes = [make_permission_class('PATIENT_VIEW')]


class PatientAlertListView(generics.ListCreateAPIView):
    serializer_class = PatientAlertSerializer
    permission_classes = [make_permission_class('PATIENT_VIEW')]

    def get_queryset(self):
        return PatientAlert.objects.filter(patient_id=self.kwargs['patient_id'], is_active=True)

    def perform_create(self, serializer):
        serializer.save(patient_id=self.kwargs['patient_id'], created_by=self.request.user.id if self.request.user.is_authenticated else None)


class PatientAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PatientAlert.objects.all()
    serializer_class = PatientAlertSerializer
    permission_classes = [make_permission_class('PATIENT_VIEW')]


class PatientDocumentListView(generics.ListCreateAPIView):
    serializer_class = PatientDocumentSerializer
    permission_classes = [make_permission_class('PATIENT_VIEW')]

    def get_queryset(self):
        return PatientDocument.objects.filter(patient_id=self.kwargs['patient_id'], is_active=True)

    def perform_create(self, serializer):
        serializer.save(patient_id=self.kwargs['patient_id'], uploaded_by=self.request.user.id if self.request.user.is_authenticated else None)


class PatientDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PatientDocument.objects.all()
    serializer_class = PatientDocumentSerializer
    permission_classes = [make_permission_class('PATIENT_VIEW')]
