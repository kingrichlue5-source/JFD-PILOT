from datetime import timedelta
from django.db import transaction
from django.db.models import Q, Count, Min
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Visit, TriageRecord, Encounter, VitalSigns, Diagnosis,
    Order, ProgressNote, NursingNote, Admission, AdmissionTransfer,
    Ward, Room, Bed, PatientMovement, WorkflowTransition,
    LabTestCatalogue, RadiologyTestCatalogue, DiagnosticResult,
    AntenatalVisit, LaborRecord, DeliveryRecord, BirthRecord, PostnatalVisit,
    SurgicalCase, Referral, Appointment, Specimen
)
from .serializers import (
    VisitSerializer, VisitCreateSerializer,
    TriageRecordSerializer, EncounterSerializer,
    VitalSignsSerializer, DiagnosisSerializer,
    OrderSerializer, ProgressNoteSerializer,
    NursingNoteSerializer, AdmissionSerializer,
    AdmissionTransferSerializer, WardSerializer,
    BedSerializer, BedOccupancySerializer, RoomSerializer,
    PatientMovementSerializer,
    LabTestCatalogueSerializer, RadiologyTestCatalogueSerializer,
    DiagnosticResultSerializer, EncounterDetailSerializer,
    AntenatalVisitSerializer, LaborRecordSerializer, DeliveryRecordSerializer,
    BirthRecordSerializer, PostnatalVisitSerializer, SurgicalCaseSerializer,
    ReferralSerializer, AppointmentSerializer, SpecimenSerializer
)
from jfd_hms.permissions import require_permission, make_permission_class

VALID_STATUS_TRANSITIONS = {
    'scheduled': ['checked_in', 'cancelled'],
    'checked_in': ['in_triage', 'in_progress', 'cancelled', 'no_show'],
    'in_triage': ['in_progress', 'cancelled', 'pending_registration'],
    'in_progress': ['completed', 'cancelled'],
    'pending_registration': ['in_triage', 'in_progress', 'completed', 'cancelled'],
    'awaiting_reconciliation': ['in_triage', 'in_progress', 'completed', 'cancelled'],
    'completed': [],
    'cancelled': [],
    'no_show': [],
}

OBGYN_KEYWORDS = [
    'pregnant', 'pregnancy', 'labor', 'delivery', 'contraction',
    'vaginal bleeding', 'prenatal', 'antenatal', 'postnatal',
    'abdominal pain lower', 'missed period', 'morning sickness',
    'obgyn', 'gynecology', 'c-section', 'cesarean', 'apgar',
    'newborn', 'maternal', 'fetal', 'breastfeeding'
]

ER_KEYWORDS = [
    'chest pain', 'difficulty breathing', 'severe bleeding', 'unconscious',
    'seizure', 'stroke', 'heart attack', 'anaphylaxis', 'trauma',
    'gunshot', 'stab wound', 'burn', 'poisoning', 'overdose',
    'cardiac arrest', 'respiratory distress', 'shock', 'coma'
]


def route_patient(acuity_level, chief_complaint):
    complaint_lower = chief_complaint.lower() if chief_complaint else ''

    if acuity_level in [1, 2]:
        return {
            'department': 'ER',
            'department_code': 'ER',
            'priority': 'STAT',
            'reason': f'Acuity Level {acuity_level} - Requires immediate emergency care'
        }

    if any(kw in complaint_lower for kw in OBGYN_KEYWORDS):
        return {
            'department': 'OBGYN',
            'department_code': 'OBGYN',
            'priority': 'URGENT' if acuity_level <= 3 else 'ROUTINE',
            'reason': 'OB/GYN related complaint'
        }

    if any(kw in complaint_lower for kw in ER_KEYWORDS):
        return {
            'department': 'ER',
            'department_code': 'ER',
            'priority': 'URGENT',
            'reason': 'Emergency keywords detected in chief complaint'
        }

    if acuity_level == 3:
        return {
            'department': 'OPD',
            'department_code': 'OPD',
            'priority': 'URGENT',
            'reason': 'Acuity Level 3 - Urgent outpatient care'
        }

    return {
        'department': 'OPD',
        'department_code': 'OPD',
        'priority': 'ROUTINE',
        'reason': 'Standard outpatient care'
    }


class VisitListView(generics.ListCreateAPIView):
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return VisitCreateSerializer
        return VisitSerializer

    def get_queryset(self):
        queryset = Visit.objects.filter(is_deleted=False)
        patient = self.request.query_params.get('patient', None)
        status_list = self.request.query_params.getlist('status')
        visit_type = self.request.query_params.get('type', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)

        if patient:
            queryset = queryset.filter(patient_id=patient)
        if status_list:
            queryset = queryset.filter(status__in=status_list)
        if visit_type:
            queryset = queryset.filter(visit_type=visit_type)
        if date_from:
            queryset = queryset.filter(visit_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(visit_date__lte=date_to)

        return queryset.order_by('-visit_date', '-created_at')

    def perform_create(self, serializer):
        visit = serializer.save()
        from audit.utils import log_audit
        log_audit('clinical', 'visits', visit.id, 'CREATE',
                  new_values={
                      'visit_number': visit.visit_number,
                      'patient': str(visit.patient.mrn),
                      'visit_type': visit.visit_type,
                      'status': visit.status,
                  },
                  request=self.request)


class VisitDetailView(generics.RetrieveUpdateAPIView):
    queryset = Visit.objects.filter(is_deleted=False)
    serializer_class = VisitSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


@api_view(['PATCH'])
@permission_classes([make_permission_class('ENCOUNTER_EDIT')])
def visit_status_transition(request, visit_id):
    try:
        visit = Visit.objects.get(id=visit_id, is_deleted=False)
    except Visit.DoesNotExist:
        return Response({'error': 'Visit not found'}, status=status.HTTP_404_NOT_FOUND)

    from audit.utils import log_audit

    new_status = request.data.get('status')
    if not new_status:
        return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)

    old_status = visit.status
    allowed = VALID_STATUS_TRANSITIONS.get(visit.status, [])
    if new_status not in allowed:
        return Response({
            'error': f'Cannot transition from "{visit.status}" to "{new_status}". Allowed: {allowed}'
        }, status=status.HTTP_400_BAD_REQUEST)

    visit.status = new_status

    if new_status == 'checked_in' and not visit.check_in_time:
        visit.check_in_time = timezone.now()
    elif new_status == 'completed' and not visit.check_out_time:
        visit.check_out_time = timezone.now()

    visit.save()

    log_audit('clinical', 'visits', visit.id, 'UPDATE', old_values={'status': old_status}, new_values={'status': visit.status}, request=request)

    return Response(VisitSerializer(visit).data)


@api_view(['GET'])
def triage_queue(request):
    now = timezone.now()

    visits = Visit.objects.filter(
        is_deleted=False,
        status='checked_in'
    ).select_related('patient', 'department', 'provider').order_by(
        'triage_priority', 'check_in_time'
    )

    queue = []
    for visit in visits:
        wait_minutes = 0
        if visit.check_in_time:
            delta = now - visit.check_in_time
            wait_minutes = int(delta.total_seconds() / 60)

        queue.append({
            'id': str(visit.id),
            'visit_number': visit.visit_number,
            'patient_id': str(visit.patient.id),
            'patient_mrn': visit.patient.mrn,
            'patient_name': f"{visit.patient.first_name} {visit.patient.last_name}",
            'patient_gender': visit.patient.gender,
            'patient_dob': visit.patient.date_of_birth.isoformat() if visit.patient.date_of_birth else None,
            'visit_type': visit.visit_type,
            'status': visit.status,
            'chief_complaint': visit.chief_complaint,
            'triage_priority': visit.triage_priority,
            'check_in_time': visit.check_in_time.isoformat() if visit.check_in_time else None,
            'wait_minutes': wait_minutes,
            'department': visit.department.name if visit.department else None,
            'provider': f"{visit.provider.first_name} {visit.provider.last_name}" if visit.provider else None,
        })

    return Response(queue)


class TriageRecordListView(generics.ListCreateAPIView):
    serializer_class = TriageRecordSerializer
    permission_classes = [make_permission_class('TRIAGE_PERFORM')]

    def get_queryset(self):
        return TriageRecord.objects.filter(visit_id=self.kwargs['visit_id'])

    def perform_create(self, serializer):
        visit = Visit.objects.get(id=self.kwargs['visit_id'])
        record = serializer.save(
            patient=visit.patient,
            triage_nurse=self.request.user if self.request.user.is_authenticated else None
        )
        from audit.utils import log_audit
        log_audit('clinical', 'triage_records', record.id, 'CREATE',
                  new_values={
                      'visit': visit.visit_number,
                      'patient': str(visit.patient.mrn),
                      'acuity_level': record.acuity_level,
                  },
                  request=self.request)


@api_view(['POST'])
def triage_evaluate(request):
    """Lightweight real-time triage evaluation — returns suggestion without persisting."""
    from clinical.triage_engine import evaluate_vitals, get_acuity_label

    vitals = {
        'temperature': request.data.get('temperature'),
        'heart_rate': request.data.get('heart_rate'),
        'respiratory_rate': request.data.get('respiratory_rate'),
        'blood_pressure_systolic': request.data.get('blood_pressure_systolic'),
        'blood_pressure_diastolic': request.data.get('blood_pressure_diastolic'),
        'oxygen_saturation': request.data.get('oxygen_saturation'),
        'pain_scale': request.data.get('pain_scale'),
        'blood_glucose': request.data.get('blood_glucose'),
    }

    result = evaluate_vitals(vitals)
    result['acuity_label'] = get_acuity_label(result['suggested_acuity'])
    return Response(result)


@api_view(['POST'])
@permission_classes([make_permission_class('TRIAGE_PERFORM')])
def triage_submit(request, visit_id):
    from audit.utils import log_audit
    from clinical.triage_engine import evaluate_vitals, get_acuity_label

    try:
        visit = Visit.objects.get(id=visit_id, is_deleted=False)
    except Visit.DoesNotExist:
        return Response({'error': 'Visit not found'}, status=status.HTTP_404_NOT_FOUND)

    if visit.status not in ['checked_in', 'in_triage']:
        return Response({
            'error': f'Visit status "{visit.status}" is not eligible for triage'
        }, status=status.HTTP_400_BAD_REQUEST)

    data = request.data.copy()

    acuity_level = data.get('acuity_level')
    if acuity_level is not None:
        try:
            acuity_level = int(acuity_level)
            if acuity_level not in [1, 2, 3, 4, 5]:
                return Response({'error': 'acuity_level must be 1-5'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({'error': 'acuity_level must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)

    for field, min_val, max_val in [
        ('temperature', 30.0, 45.0),
        ('heart_rate', 20, 300),
        ('respiratory_rate', 5, 80),
        ('blood_pressure_systolic', 50, 300),
        ('blood_pressure_diastolic', 20, 200),
        ('oxygen_saturation', 0, 100),
        ('pain_scale', 0, 10),
        ('blood_glucose', 20, 800),
    ]:
        val = data.get(field)
        if val is not None:
            try:
                val = float(val)
                if val < min_val or val > max_val:
                    return Response({'error': f'{field} must be between {min_val} and {val}'},
                                    status=status.HTTP_400_BAD_REQUEST)
            except (TypeError, ValueError):
                return Response({'error': f'{field} must be a valid number'}, status=status.HTTP_400_BAD_REQUEST)

    # --- Triage Engine: evaluate vitals against Admin Criteria Matrix ---
    vitals_for_evaluation = {}
    for field in ['temperature', 'heart_rate', 'respiratory_rate', 'blood_pressure_systolic',
                  'blood_pressure_diastolic', 'oxygen_saturation', 'pain_scale', 'blood_glucose']:
        if data.get(field) is not None:
            vitals_for_evaluation[field] = data.get(field)

    engine_suggestion = evaluate_vitals(vitals_for_evaluation)

    # Fallback: if no criteria matched, use keyword-based routing (route_patient)
    if not engine_suggestion.get('matched_rules'):
        fallback_routing = route_patient(
            acuity_level=acuity_level or 5,
            chief_complaint=data.get('chief_complaint', '')
        )
        engine_suggestion['suggested_department'] = fallback_routing['department_code']
        engine_suggestion['suggested_acuity'] = acuity_level or 5
        engine_suggestion['reason'] = f"Fallback: {fallback_routing['reason']}"

    # Determine final acuity — use clinician's input if provided, otherwise use engine suggestion
    acuity_overridden = False
    acuity_override_reason = data.get('acuity_override_reason', '')
    route_overridden = False
    route_override_reason = data.get('route_override_reason', '')

    if acuity_level is not None:
        # Clinician provided explicit acuity — check if it differs from suggestion
        if acuity_level != engine_suggestion['suggested_acuity']:
            acuity_overridden = True
            if acuity_level > engine_suggestion['suggested_acuity']:
                # Downgrading severity requires justification
                if not acuity_override_reason:
                    return Response({
                        'error': 'Clinical justification required when downgrading acuity from Level '
                                 f"{engine_suggestion['suggested_acuity']} to Level {acuity_level}",
                        'suggestion': engine_suggestion
                    }, status=status.HTTP_400_BAD_REQUEST)
        final_acuity = acuity_level
    else:
        final_acuity = engine_suggestion['suggested_acuity']

    # Determine final department — check for routing override
    department_code = data.get('department_code')
    if department_code:
        if department_code != engine_suggestion['suggested_department']:
            route_overridden = True
            if not route_override_reason:
                return Response({
                    'error': 'Clinical justification required when overriding routing from '
                             f"{engine_suggestion['suggested_department']} to {department_code}",
                    'suggestion': engine_suggestion
                }, status=status.HTTP_400_BAD_REQUEST)
        final_department_code = department_code
    else:
        final_department_code = engine_suggestion['suggested_department']

    # Create TriageRecord
    triage_record = TriageRecord.objects.create(
        visit=visit,
        patient=visit.patient,
        chief_complaint=data.get('chief_complaint', ''),
        acuity_level=final_acuity,
        temperature=data.get('temperature'),
        heart_rate=data.get('heart_rate'),
        respiratory_rate=data.get('respiratory_rate'),
        blood_pressure_systolic=data.get('blood_pressure_systolic'),
        blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
        oxygen_saturation=data.get('oxygen_saturation'),
        weight=data.get('weight'),
        height=data.get('height'),
        pain_scale=data.get('pain_scale'),
        blood_glucose=data.get('blood_glucose'),
        screening_notes=data.get('screening_notes', ''),
        triage_nurse=request.user if request.user.is_authenticated else None
    )

    # Update visit
    visit.chief_complaint = data.get('chief_complaint', visit.chief_complaint)
    visit.triage_priority = str(final_acuity)
    visit.triage_notes = data.get('screening_notes', '')
    visit.triage_time = timezone.now()
    visit.suggested_acuity = engine_suggestion['suggested_acuity']
    visit.suggested_department = engine_suggestion['suggested_department']
    visit.acuity_override = acuity_overridden
    visit.acuity_override_reason = acuity_override_reason
    visit.route_override = final_department_code if route_overridden else None
    visit.route_override_reason = route_override_reason
    visit.status = 'in_progress'

    from users_auth.models import Department
    try:
        dept = Department.objects.get(code=final_department_code)
        visit.department = dept
    except Department.DoesNotExist:
        logger.warning(f"Routed department '{final_department_code}' not found for visit {visit.visit_number}")

    visit.save()

    # Build routing response
    routing = {
        'department': final_department_code,
        'department_code': final_department_code,
        'priority': 'STAT' if final_acuity in [1, 2] else ('URGENT' if final_acuity == 3 else 'ROUTINE'),
        'reason': f"Acuity Level {final_acuity} ({get_acuity_label(final_acuity)})" + (
            f" - Overridden from {engine_suggestion['suggested_department']}" if route_overridden else ''
        ),
        'suggested_department': engine_suggestion['suggested_department'],
        'route_overridden': route_overridden,
    }

    # Log workflow transition
    WorkflowTransition.objects.create(
        patient=visit.patient,
        visit=visit,
        from_status='checked_in',
        to_status='in_progress',
        to_department=dept if 'dept' in dir() else None,
        triggered_by=request.user if request.user.is_authenticated else None,
        trigger_action='triage_submit',
        metadata={
            'suggested_acuity': engine_suggestion['suggested_acuity'],
            'final_acuity': final_acuity,
            'acuity_overridden': acuity_overridden,
            'route_overridden': route_overridden,
            'matched_rules': engine_suggestion['matched_rules'],
        }
    )

    log_audit(
        'clinical', 'triage_records', triage_record.id, 'CREATE',
        new_values={
            'acuity_level': triage_record.acuity_level,
            'chief_complaint': triage_record.chief_complaint,
            'visit_number': visit.visit_number,
            'new_status': visit.status,
            'suggested_acuity': engine_suggestion['suggested_acuity'],
            'acuity_overridden': acuity_overridden,
            'route_overridden': route_overridden,
        },
        request=request,
    )

    return Response({
        'triage_record': TriageRecordSerializer(triage_record).data,
        'suggestion': {
            'acuity_level': engine_suggestion['suggested_acuity'],
            'acuity_label': get_acuity_label(engine_suggestion['suggested_acuity']),
            'department_code': engine_suggestion['suggested_department'],
            'reason': engine_suggestion['reason'],
            'matched_rules': engine_suggestion['matched_rules'],
        },
        'overrides': {
            'acuity_overridden': acuity_overridden,
            'acuity_override_reason': acuity_override_reason,
            'route_overridden': route_overridden,
            'route_override_reason': route_override_reason,
        },
        'routing': routing,
        'visit': VisitSerializer(visit).data
    }, status=status.HTTP_201_CREATED)


class TriageRecordDetailView(generics.RetrieveUpdateAPIView):
    queryset = TriageRecord.objects.all()
    serializer_class = TriageRecordSerializer
    permission_classes = [make_permission_class('TRIAGE_PERFORM')]


class EncounterListView(generics.ListCreateAPIView):
    serializer_class = EncounterSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        return Encounter.objects.filter(visit_id=self.kwargs['visit_id'])

    def perform_create(self, serializer):
        visit = Visit.objects.get(id=self.kwargs['visit_id'])
        encounter = serializer.save(
            visit=visit,
            patient=visit.patient,
            provider=self.request.user if self.request.user.is_authenticated else None,
            created_by=self.request.user.id if self.request.user.is_authenticated else None
        )
        from audit.utils import log_audit
        log_audit('clinical', 'encounters', encounter.id, 'CREATE',
                  new_values={
                      'visit': visit.visit_number,
                      'patient': str(visit.patient.mrn),
                      'encounter_type': encounter.encounter_type,
                  },
                  request=self.request)


class EncounterDetailView(generics.RetrieveUpdateAPIView):
    queryset = Encounter.objects.all()
    serializer_class = EncounterSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


@api_view(['POST'])
@permission_classes([make_permission_class('ENCOUNTER_SIGN')])
def finalize_encounter(request, encounter_id):
    from audit.utils import log_audit

    try:
        encounter = Encounter.objects.get(id=encounter_id)
    except Encounter.DoesNotExist:
        return Response({'error': 'Encounter not found'}, status=status.HTTP_404_NOT_FOUND)

    if encounter.is_finalized:
        return Response({'error': 'Encounter is already finalized'}, status=status.HTTP_400_BAD_REQUEST)

    encounter.subjective = request.data.get('subjective', encounter.subjective)
    encounter.objective = request.data.get('objective', encounter.objective)
    encounter.assessment = request.data.get('assessment', encounter.assessment)
    encounter.plan = request.data.get('plan', encounter.plan)
    encounter.diagnosis_primary = request.data.get('diagnosis_primary', encounter.diagnosis_primary)
    encounter.diagnosis_secondary = request.data.get('diagnosis_secondary', encounter.diagnosis_secondary)
    encounter.status = 'completed'
    encounter.is_finalized = True
    encounter.finalized_at = timezone.now()
    encounter.save()

    log_audit('clinical', 'encounters', encounter.id, 'UPDATE', new_values={'status': 'signed'}, request=request)

    return Response(EncounterDetailSerializer(encounter).data)


class VitalSignsListView(generics.ListCreateAPIView):
    serializer_class = VitalSignsSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        return VitalSigns.objects.filter(visit_id=self.kwargs['visit_id'])

    def perform_create(self, serializer):
        visit = Visit.objects.get(id=self.kwargs['visit_id'])
        serializer.save(
            visit=visit,
            patient=visit.patient,
            recorded_by=self.request.user if self.request.user.is_authenticated else None
        )


class VitalSignsDetailView(generics.RetrieveUpdateAPIView):
    queryset = VitalSigns.objects.all()
    serializer_class = VitalSignsSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class DiagnosisListView(generics.ListCreateAPIView):
    serializer_class = DiagnosisSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        return Diagnosis.objects.filter(encounter_id=self.kwargs['encounter_id'])

    def perform_create(self, serializer):
        encounter = Encounter.objects.get(id=self.kwargs['encounter_id'])
        serializer.save(
            encounter=encounter,
            patient=encounter.patient,
            visit=encounter.visit,
            coded_by=self.request.user.id if self.request.user.is_authenticated else None
        )


class DiagnosisDetailView(generics.RetrieveUpdateAPIView):
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class OrderListView(generics.ListCreateAPIView):
    serializer_class = OrderSerializer
    permission_classes = [make_permission_class('ORDER_VIEW')]

    def get_queryset(self):
        queryset = Order.objects.filter(visit_id=self.kwargs['visit_id'])
        order_type = self.request.query_params.get('type', None)
        status_filter = self.request.query_params.get('status', None)

        if order_type:
            queryset = queryset.filter(order_type=order_type)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        visit = Visit.objects.get(id=self.kwargs['visit_id'])
        order = serializer.save(
            patient=visit.patient,
            ordering_provider=self.request.user if self.request.user.is_authenticated else None
        )
        if order.order_type == 'lab':
            from django.utils import timezone as tz
            specimen_type = 'Blood'
            if order.order_description:
                desc_lower = order.order_description.lower()
                if 'urine' in desc_lower:
                    specimen_type = 'Urine'
                elif 'stool' in desc_lower:
                    specimen_type = 'Stool'
                elif 'csf' in desc_lower:
                    specimen_type = 'CSF'
            Specimen.objects.create(
                patient=visit.patient,
                order=order,
                visit=visit,
                specimen_type=specimen_type,
                status='collected',
                collection_datetime=tz.now(),
                collected_by=self.request.user if self.request.user.is_authenticated else None,
            )


class OrderDetailView(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [make_permission_class('ORDER_VIEW')]


class AllOrdersListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [make_permission_class('ORDER_VIEW')]

    def get_queryset(self):
        qs = Order.objects.all()
        order_type = self.request.query_params.get('type', None)
        status_filter = self.request.query_params.get('status', None)
        if order_type:
            qs = qs.filter(order_type=order_type)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by('-created_at')


class ProgressNoteListView(generics.ListCreateAPIView):
    serializer_class = ProgressNoteSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        return ProgressNote.objects.filter(encounter_id=self.kwargs['encounter_id'])

    def perform_create(self, serializer):
        encounter = Encounter.objects.get(id=self.kwargs['encounter_id'])
        serializer.save(
            encounter=encounter,
            patient=encounter.patient,
            visit=encounter.visit,
            author=self.request.user if self.request.user.is_authenticated else None
        )


class ProgressNoteDetailView(generics.RetrieveUpdateAPIView):
    queryset = ProgressNote.objects.all()
    serializer_class = ProgressNoteSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class NursingNoteListView(generics.ListCreateAPIView):
    serializer_class = NursingNoteSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        return NursingNote.objects.filter(encounter_id=self.kwargs['encounter_id'])

    def perform_create(self, serializer):
        encounter = Encounter.objects.get(id=self.kwargs['encounter_id'])
        serializer.save(
            patient=encounter.patient,
            visit=encounter.visit,
            author=self.request.user if self.request.user.is_authenticated else None
        )


class NursingNoteDetailView(generics.RetrieveUpdateAPIView):
    queryset = NursingNote.objects.all()
    serializer_class = NursingNoteSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class AdmissionListView(generics.ListCreateAPIView):
    serializer_class = AdmissionSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        queryset = Admission.objects.all()
        patient = self.request.query_params.get('patient', None)
        ward = self.request.query_params.get('ward', None)
        status_filter = self.request.query_params.get('status', None)

        if patient:
            queryset = queryset.filter(patient_id=patient)
        if ward:
            queryset = queryset.filter(ward_id=ward)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        admission = serializer.save(
            created_by=self.request.user.id if self.request.user.is_authenticated else None
        )
        from audit.utils import log_audit
        log_audit('clinical', 'admissions', admission.id, 'CREATE',
                  new_values={
                      'admission_number': admission.admission_number,
                      'patient': str(admission.patient.mrn),
                      'ward': str(admission.ward) if admission.ward else None,
                  },
                  request=self.request)


class AdmissionDetailView(generics.RetrieveUpdateAPIView):
    queryset = Admission.objects.all()
    serializer_class = AdmissionSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


@api_view(['POST'])
@permission_classes([make_permission_class('ENCOUNTER_EDIT')])
def discharge_patient(request, admission_id):
    from django.db import transaction
    from audit.utils import log_audit

    try:
        with transaction.atomic():
            admission = Admission.objects.select_for_update().get(id=admission_id)
    except Admission.DoesNotExist:
        return Response({'error': 'Admission not found'}, status=status.HTTP_404_NOT_FOUND)

    if admission.status != 'active':
        return Response({'error': f'Cannot discharge: admission status is "{admission.status}"'},
                        status=status.HTTP_400_BAD_REQUEST)

    discharge_type = request.data.get('discharge_type', 'routine')
    discharge_summary = request.data.get('discharge_summary', '')

    valid_discharge_types = ['routine', 'against_medical_advice', 'referred', 'transferred', 'deceased']
    if discharge_type not in valid_discharge_types:
        return Response({'error': f'discharge_type must be one of: {", ".join(valid_discharge_types)}'},
                        status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        admission.status = 'discharged'
        admission.discharge_type = discharge_type
        admission.discharge_summary = discharge_summary
        admission.actual_discharge_date = timezone.now()
        admission.discharge_provider = request.user if request.user.is_authenticated else None
        admission.save()

        if admission.bed:
            bed = Bed.objects.select_for_update().get(id=admission.bed_id)
            bed.is_occupied = False
            bed.save(update_fields=['is_occupied'])

        visit = admission.visit
        if visit:
            visit.status = 'completed'
            visit.check_out_time = timezone.now()
            visit.save()

    log_audit('clinical', 'admissions', admission.id, 'UPDATE', new_values={'status': 'discharged'}, request=request)

    return Response(AdmissionSerializer(admission).data)


class AdmissionTransferListView(generics.ListCreateAPIView):
    serializer_class = AdmissionTransferSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        return AdmissionTransfer.objects.filter(admission_id=self.kwargs['admission_id'])

    def perform_create(self, serializer):
        from django.db import transaction

        with transaction.atomic():
            admission = Admission.objects.select_for_update().get(id=self.kwargs['admission_id'])
            to_bed_id = self.request.data.get('to_bed')
            to_bed = Bed.objects.select_for_update().get(id=to_bed_id) if to_bed_id else None
            from_bed = admission.bed
            if from_bed:
                from_bed = Bed.objects.select_for_update().get(id=from_bed.id)
            from_room = from_bed.room if from_bed else None
            from_ward = from_room.ward if from_room else None
            to_room = to_bed.room if to_bed else None
            to_ward = to_room.ward if to_room else None

            admission.bed = to_bed
            if to_ward:
                admission.ward = to_ward
            if to_room:
                admission.room = to_room
            admission.save()

            if from_bed:
                from_bed.is_occupied = False
                from_bed.save(update_fields=['is_occupied'])
            if to_bed:
                to_bed.is_occupied = True
                to_bed.save(update_fields=['is_occupied'])

        serializer.save(
            admission=admission,
            from_ward=from_ward, from_room=from_room, from_bed=from_bed,
            to_ward=to_ward, to_room=to_room, to_bed=to_bed,
            transferred_by=self.request.user if self.request.user.is_authenticated else None
        )


class WardListView(generics.ListCreateAPIView):
    queryset = Ward.objects.filter(is_active=True)
    serializer_class = WardSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def perform_create(self, serializer):
        code = self.request.data.get('code', '')
        if not code:
            name = self.request.data.get('name', '')
            code = name[:3].upper() if name else 'WRD'
            base = code
            i = 1
            while Ward.objects.filter(code=code).exists():
                code = f"{base}{i}"
                i += 1
        serializer.save(code=code)


class WardDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ward.objects.all()
    serializer_class = WardSerializer
    permission_classes = [make_permission_class('ENCOUNTER_EDIT')]


class BedListView(generics.ListCreateAPIView):
    serializer_class = BedSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        queryset = Bed.objects.filter(is_active=True)
        ward = self.request.query_params.get('ward', None)
        ward_type = self.request.query_params.get('ward_type', None)
        available = self.request.query_params.get('available', None)

        if ward:
            queryset = queryset.filter(room__ward_id=ward)
        if ward_type:
            queryset = queryset.filter(room__ward__ward_type=ward_type)
        if available and available.lower() == 'true':
            queryset = queryset.filter(is_occupied=False, is_reserved=False)

        return queryset

    def perform_create(self, serializer):
        ward_id = self.request.data.get('ward')
        room_number = self.request.data.get('room_number')
        if ward_id and room_number:
            ward = Ward.objects.get(id=ward_id)
            room, _ = Room.objects.get_or_create(ward=ward, room_number=room_number, defaults={'capacity': 1})
            serializer.save(room=room)
        else:
            serializer.save()


class BedDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bed.objects.all()
    serializer_class = BedSerializer
    permission_classes = [make_permission_class('ENCOUNTER_EDIT')]


@api_view(['GET'])
@permission_classes([make_permission_class('ENCOUNTER_VIEW')])
def bed_occupancy(request):
    ward_id = request.query_params.get('ward', None)

    queryset = Bed.objects.filter(
        is_active=True,
        room__ward__is_active=True
    ).select_related('room', 'room__ward')

    if ward_id:
        queryset = queryset.filter(room__ward_id=ward_id)

    wards = {}
    for bed in queryset:
        ward = bed.room.ward
        if ward.id not in wards:
            wards[ward.id] = {
                'ward_id': str(ward.id),
                'ward_name': ward.name,
                'ward_code': ward.code,
                'total_beds': 0,
                'occupied_beds': 0,
                'available_beds': 0,
                'reserved_beds': 0
            }
        wards[ward.id]['total_beds'] += 1
        if bed.is_occupied:
            wards[ward.id]['occupied_beds'] += 1
        elif bed.is_reserved:
            wards[ward.id]['reserved_beds'] += 1
        else:
            wards[ward.id]['available_beds'] += 1

    return Response(list(wards.values()))


class PatientMovementListView(generics.ListCreateAPIView):
    serializer_class = PatientMovementSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        queryset = PatientMovement.objects.all()
        patient = self.request.query_params.get('patient', None)

        if patient:
            queryset = queryset.filter(patient_id=patient)

        return queryset

    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user if self.request.user.is_authenticated else None)


@api_view(['GET'])
def lab_test_catalogue(request):
    search = request.query_params.get('search', None)
    category = request.query_params.get('category', None)

    queryset = LabTestCatalogue.objects.filter(is_active=True)

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )

    if category:
        queryset = queryset.filter(category=category)

    return Response(LabTestCatalogueSerializer(queryset, many=True).data)


@api_view(['GET'])
def radiology_test_catalogue(request):
    search = request.query_params.get('search', None)
    body_part = request.query_params.get('body_part', None)

    queryset = RadiologyTestCatalogue.objects.filter(is_active=True)

    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(code__icontains=search)
        )

    if body_part:
        queryset = queryset.filter(body_part__icontains=body_part)

    return Response(RadiologyTestCatalogueSerializer(queryset, many=True).data)


@api_view(['GET'])
def icd_diagnosis_lookup(request):
    search = request.query_params.get('search', None)
    if not search or len(search) < 1:
        return Response([])

    common_diagnoses = [
        {'code': 'A00.9', 'description': 'Cholera, unspecified'},
        {'code': 'A09', 'description': 'Infectious gastroenteritis and colitis, unspecified'},
        {'code': 'B34.9', 'description': 'Viral infection, unspecified'},
        {'code': 'B54', 'description': 'Unspecified malaria'},
        {'code': 'D50.9', 'description': 'Iron deficiency anemia, unspecified'},
        {'code': 'D64.9', 'description': 'Anemia, unspecified'},
        {'code': 'E10.9', 'description': 'Type 1 diabetes mellitus without complications'},
        {'code': 'E11.9', 'description': 'Type 2 diabetes mellitus without complications'},
        {'code': 'E46', 'description': 'Protein-energy malnutrition, unspecified'},
        {'code': 'E78.5', 'description': 'Hyperlipidemia, unspecified'},
        {'code': 'F10.20', 'description': 'Alcohol dependence, uncomplicated'},
        {'code': 'F20.9', 'description': 'Schizophrenia, unspecified'},
        {'code': 'F32.9', 'description': 'Major depressive disorder, single episode, unspecified'},
        {'code': 'F41.9', 'description': 'Anxiety disorder, unspecified'},
        {'code': 'G40.909', 'description': 'Epilepsy, unspecified, not intractable'},
        {'code': 'G43.909', 'description': 'Migraine, unspecified, not intractable'},
        {'code': 'H10.9', 'description': 'Conjunctivitis, unspecified'},
        {'code': 'I10', 'description': 'Essential (primary) hypertension'},
        {'code': 'I25.10', 'description': 'Atherosclerotic heart disease of native coronary artery without angina pectoris'},
        {'code': 'I48.91', 'description': 'Unspecified atrial fibrillation'},
        {'code': 'I50.9', 'description': 'Heart failure, unspecified'},
        {'code': 'J06.9', 'description': 'Acute upper respiratory infection, unspecified'},
        {'code': 'J18.9', 'description': 'Pneumonia, unspecified organism'},
        {'code': 'J20.9', 'description': 'Acute bronchitis, unspecified'},
        {'code': 'J44.1', 'description': 'Chronic obstructive pulmonary disease with acute exacerbation'},
        {'code': 'K21.0', 'description': 'Gastro-esophageal reflux disease with esophagitis'},
        {'code': 'K35.80', 'description': 'Acute appendicitis, unspecified'},
        {'code': 'K40.90', 'description': 'Inguinal hernia, unspecified side, not specified as obstructed'},
        {'code': 'K59.00', 'description': 'Constipation, unspecified'},
        {'code': 'K76.0', 'description': 'Fatty (change of) liver, not elsewhere classified'},
        {'code': 'K80.20', 'description': 'Calculus of gallbladder without cholecystitis without obstruction'},
        {'code': 'L03.90', 'description': 'Cellulitis, unspecified'},
        {'code': 'M54.5', 'description': 'Low back pain'},
        {'code': 'M79.3', 'description': 'Panniculitis, unspecified'},
        {'code': 'N10', 'description': 'Acute pyelonephritis'},
        {'code': 'N18.9', 'description': 'Chronic kidney disease, unspecified'},
        {'code': 'N39.0', 'description': 'Urinary tract infection, site not specified'},
        {'code': 'N83.20', 'description': 'Unspecified ovarian cyst'},
        {'code': 'O80.0', 'description': 'Encounter for full-term uncomplicated delivery'},
        {'code': 'O82.0', 'description': 'Encounter for elective cesarean section'},
        {'code': 'O83.9', 'description': 'Assisted delivery, unspecified'},
        {'code': 'O14.90', 'description': 'Pre-eclampsia, unspecified, unspecified trimester'},
        {'code': 'O36.59', 'description': 'Maternal care for known or suspected fetal growth restriction'},
        {'code': 'P07.10', 'description': 'Other low birth weight newborn, unspecified'},
        {'code': 'R05.9', 'description': 'Cough, unspecified'},
        {'code': 'R10.0', 'description': 'Acute abdomen'},
        {'code': 'R10.9', 'description': 'Unspecified abdominal pain'},
        {'code': 'R51.9', 'description': 'Headache, unspecified'},
        {'code': 'R53.83', 'description': 'Other fatigue'},
        {'code': 'S06.0X0A', 'description': 'Concussion without loss of consciousness, initial encounter'},
        {'code': 'S12.001A', 'description': 'Unspecified fracture of first cervical vertebra, initial encounter'},
        {'code': 'S32.010A', 'description': 'Fracture of L1 vertebra, initial encounter'},
        {'code': 'S52.501A', 'description': 'Fracture of lower end of radius, right arm, initial encounter'},
        {'code': 'S72.001A', 'description': 'Fracture of unspecified part of neck of right femur, initial encounter'},
        {'code': 'S82.001A', 'description': 'Fracture of unspecified patella, right knee, initial encounter'},
        {'code': 'T14.9', 'description': 'Injury, unspecified'},
        {'code': 'Z00.00', 'description': 'Encounter for general adult medical examination without abnormal findings'},
        {'code': 'Z01.00', 'description': 'Encounter for examination of eyes and vision without abnormal findings'},
        {'code': 'Z09', 'description': 'Encounter for examination and treatment of conditions subsequent to surgery'},
        {'code': 'Z23', 'description': 'Encounter for immunization'},
        {'code': 'Z66', 'description': 'Do not resuscitate'},
        {'code': 'Z71.3', 'description': 'Dietary counseling and surveillance'},
        {'code': 'Z72.0', 'description': 'Tobacco use'},
        {'code': 'Z87.891', 'description': 'Personal history of nicotine dependence'},
        {'code': 'Z98.1', 'description': 'Arthrodesis status'},
    ]

    search_lower = search.lower()
    results = [
        d for d in common_diagnoses
        if search_lower in d['code'].lower() or search_lower in d['description'].lower()
    ]

    return Response(results[:20])


@api_view(['POST'])
def place_order(request, visit_id):
    try:
        visit = Visit.objects.get(id=visit_id, is_deleted=False)
    except Visit.DoesNotExist:
        return Response({'error': 'Visit not found'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    order_type = data.get('order_type')
    items = data.get('items', [])

    if not order_type or not items:
        return Response(
            {'error': 'order_type and items are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    encounter_id = data.get('encounter_id')
    encounter = None
    if encounter_id:
        try:
            encounter = Encounter.objects.get(id=encounter_id)
        except Encounter.DoesNotExist:
            return Response({'error': f'Encounter {encounter_id} not found'}, status=status.HTTP_404_NOT_FOUND)

    orders_created = []

    for item in items:
        order = Order.objects.create(
            visit=visit,
            encounter=encounter,
            patient=visit.patient,
            order_type=order_type,
            order_description=item.get('description', ''),
            priority=data.get('priority', 'routine'),
            ordering_provider=request.user if request.user.is_authenticated else None,
            notes=item.get('notes', ''),
            status='pending'
        )
        orders_created.append(order)

    billing_items = []
    billing_errors = []
    try:
        from billing.services import post_order_to_invoice
        for order in orders_created:
            line_item = post_order_to_invoice(order, visit, visit.patient)
            if line_item:
                billing_items.append({
                    'order_id': str(order.id),
                    'line_item_id': str(line_item.id),
                    'amount': str(line_item.total_amount),
                    'payment_status': line_item.payment_status,
                })
    except Exception as e:
        import logging
        logger = logging.getLogger('clinical')
        logger.error(f"Billing integration failed for orders {[str(o.id) for o in orders_created]}: {e}", exc_info=True)
        billing_errors.append(str(e))

    response_data = {
        'orders': OrderSerializer(orders_created, many=True).data,
        'total_orders': len(orders_created),
        'billing_items': billing_items,
    }
    if billing_errors:
        response_data['billing_warnings'] = billing_errors

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def visit_orders_summary(request, visit_id):
    try:
        visit = Visit.objects.get(id=visit_id, is_deleted=False)
    except Visit.DoesNotExist:
        return Response({'error': 'Visit not found'}, status=status.HTTP_404_NOT_FOUND)

    orders = Order.objects.filter(visit=visit).order_by('-created_at')

    return Response({
        'visit_id': str(visit.id),
        'visit_number': visit.visit_number,
        'total_orders': orders.count(),
        'pending_orders': orders.filter(status='pending').count(),
        'in_progress_orders': orders.filter(status='in_progress').count(),
        'completed_orders': orders.filter(status='completed').count(),
        'orders': OrderSerializer(orders, many=True).data
    })


class AntenatalVisitListView(generics.ListCreateAPIView):
    serializer_class = AntenatalVisitSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        qs = AntenatalVisit.objects.all()
        patient_id = self.request.query_params.get('patient')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user if self.request.user.is_authenticated else None)


class AntenatalVisitDetailView(generics.RetrieveUpdateAPIView):
    queryset = AntenatalVisit.objects.all()
    serializer_class = AntenatalVisitSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class LaborRecordListView(generics.ListCreateAPIView):
    serializer_class = LaborRecordSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        qs = LaborRecord.objects.all()
        patient_id = self.request.query_params.get('patient')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        return qs

    def perform_create(self, serializer):
        admission_time = self.request.data.get('admission_time')
        if not admission_time:
            admission_time = timezone.now()
        serializer.save(
            provider=self.request.user if self.request.user.is_authenticated else None,
            admission_time=admission_time,
        )


class LaborRecordDetailView(generics.RetrieveUpdateAPIView):
    queryset = LaborRecord.objects.all()
    serializer_class = LaborRecordSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class DeliveryRecordListView(generics.ListCreateAPIView):
    serializer_class = DeliveryRecordSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        qs = DeliveryRecord.objects.all()
        labor_id = self.request.query_params.get('labor_record')
        if labor_id:
            qs = qs.filter(labor_record_id=labor_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user if self.request.user.is_authenticated else None)


class DeliveryRecordDetailView(generics.RetrieveUpdateAPIView):
    queryset = DeliveryRecord.objects.all()
    serializer_class = DeliveryRecordSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class BirthRecordListView(generics.ListCreateAPIView):
    serializer_class = BirthRecordSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        qs = BirthRecord.objects.all()
        delivery_id = self.request.query_params.get('delivery_record')
        if delivery_id:
            qs = qs.filter(delivery_record_id=delivery_id)
        return qs


class BirthRecordDetailView(generics.RetrieveUpdateAPIView):
    queryset = BirthRecord.objects.all()
    serializer_class = BirthRecordSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class PostnatalVisitListView(generics.ListCreateAPIView):
    serializer_class = PostnatalVisitSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        qs = PostnatalVisit.objects.all()
        patient_id = self.request.query_params.get('patient')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(provider=self.request.user if self.request.user.is_authenticated else None)


class PostnatalVisitDetailView(generics.RetrieveUpdateAPIView):
    queryset = PostnatalVisit.objects.all()
    serializer_class = PostnatalVisitSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class SurgicalCaseListView(generics.ListCreateAPIView):
    serializer_class = SurgicalCaseSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        qs = SurgicalCase.objects.all()
        patient_id = self.request.query_params.get('patient')
        status_filter = self.request.query_params.get('status')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    def perform_create(self, serializer):
        data = self.request.data
        surgeon_id = data.get('surgeon')
        if surgeon_id:
            from users_auth.models import User
            try:
                surgeon = User.objects.get(id=surgeon_id)
            except User.DoesNotExist:
                surgeon = None
        else:
            surgeon = self.request.user if self.request.user.is_authenticated else None
        serializer.save(surgeon=surgeon)


class SurgicalCaseDetailView(generics.RetrieveUpdateAPIView):
    queryset = SurgicalCase.objects.all()
    serializer_class = SurgicalCaseSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class ReferralListView(generics.ListCreateAPIView):
    serializer_class = ReferralSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        qs = Referral.objects.all()
        patient_id = self.request.query_params.get('patient')
        referral_type = self.request.query_params.get('type')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if referral_type:
            qs = qs.filter(referral_type=referral_type)
        return qs

    def perform_create(self, serializer):
        serializer.save(referring_provider=self.request.user if self.request.user.is_authenticated else None)


class ReferralDetailView(generics.RetrieveUpdateAPIView):
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class AppointmentListView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        qs = Appointment.objects.filter(is_deleted=False)
        patient_id = self.request.query_params.get('patient')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        status_filter = self.request.query_params.get('status')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if date_from:
            qs = qs.filter(appointment_date__gte=date_from)
        if date_to:
            qs = qs.filter(appointment_date__lte=date_to)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs


class AppointmentDetailView(generics.RetrieveUpdateAPIView):
    queryset = Appointment.objects.filter(is_deleted=False)
    serializer_class = AppointmentSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class DiagnosticResultListView(generics.ListCreateAPIView):
    serializer_class = DiagnosticResultSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        return DiagnosticResult.objects.filter(visit_id=self.kwargs['visit_id'])

    def perform_create(self, serializer):
        serializer.save(
            entered_by=self.request.user if self.request.user.is_authenticated else None,
            status='pending_verification'
        )


class DiagnosticResultCreateView(generics.CreateAPIView):
    serializer_class = DiagnosticResultSerializer
    permission_classes = [make_permission_class('ORDER_VIEW')]

    def perform_create(self, serializer):
        result = serializer.save(
            entered_by=self.request.user if self.request.user.is_authenticated else None,
            status='pending_verification'
        )

    def finalize_result(self, result):
        order = result.order
        if order and order.status != 'completed':
            order.status = 'completed'
            order.completed_at = timezone.now()
            order.save()


@api_view(['POST'])
@permission_classes([make_permission_class('ORDER_VIEW')])
def verify_diagnostic_result(request, result_id):
    from audit.utils import log_audit

    try:
        result = DiagnosticResult.objects.get(id=result_id)
    except DiagnosticResult.DoesNotExist:
        return Response({'error': 'Result not found'}, status=status.HTTP_404_NOT_FOUND)

    if result.status != 'pending_verification':
        return Response({'error': f'Cannot verify result in "{result.status}" status'}, status=status.HTTP_400_BAD_REQUEST)

    action = request.data.get('action', 'verify')
    if action == 'reject':
        result.status = 'rejected'
        result.rejection_reason = request.data.get('rejection_reason', '')
        result.save(update_fields=['status', 'rejection_reason', 'updated_at'])
        log_audit('clinical', 'diagnostic_results', result.id, 'UPDATE',
                  new_values={'status': 'rejected'}, request=request)
        return Response({'status': 'rejected', 'message': 'Result rejected'})

    result.status = 'verified'
    result.verified_by = request.user if request.user.is_authenticated else None
    result.verified_at = timezone.now()
    result.save(update_fields=['status', 'verified_by', 'verified_at', 'updated_at'])

    if result.critical_flag:
        from clinical.models import CriticalResultNotification
        CriticalResultNotification.objects.create(
            result=result,
            patient=result.patient,
            notification_type='critical',
            message=f'CRITICAL result: {result.order.order_type} - {result.result_text[:200] if result.result_text else "See result details"}',
        )

    order = result.order
    if order and order.status != 'completed':
        order.status = 'completed'
        order.completed_at = timezone.now()
        order.save()

    log_audit('clinical', 'diagnostic_results', result.id, 'UPDATE',
              new_values={'status': 'verified', 'verified_by': str(result.verified_by_id)},
              request=request)

    return Response({'status': 'verified', 'message': 'Result verified and published'})


class DiagnosticResultDetailView(generics.RetrieveUpdateAPIView):
    queryset = DiagnosticResult.objects.all()
    serializer_class = DiagnosticResultSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class RoomListView(generics.ListCreateAPIView):
    serializer_class = RoomSerializer
    queryset = Room.objects.filter(is_active=True)
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class RoomDetailView(generics.RetrieveUpdateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


class SpecimenListView(generics.ListCreateAPIView):
    serializer_class = SpecimenSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]

    def get_queryset(self):
        qs = Specimen.objects.all()
        patient_id = self.request.query_params.get('patient')
        status_filter = self.request.query_params.get('status')
        specimen_type = self.request.query_params.get('type')
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if status_filter:
            qs = qs.filter(status=status_filter)
        if specimen_type:
            qs = qs.filter(specimen_type=specimen_type)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            collected_by=self.request.user if self.request.user.is_authenticated else None
        )


class SpecimenDetailView(generics.RetrieveUpdateAPIView):
    queryset = Specimen.objects.all()
    serializer_class = SpecimenSerializer
    permission_classes = [make_permission_class('ENCOUNTER_VIEW')]


@api_view(['POST'])
@permission_classes([make_permission_class('ENCOUNTER_EDIT')])
def specimen_receive(request, specimen_id):
    from audit.utils import log_audit
    try:
        specimen = Specimen.objects.get(id=specimen_id)
    except Specimen.DoesNotExist:
        return Response({'error': 'Specimen not found'}, status=status.HTTP_404_NOT_FOUND)

    if specimen.status not in ['collected', 'in_transit']:
        return Response(
            {'error': f'Specimen status "{specimen.status}" cannot be received'},
            status=status.HTTP_400_BAD_REQUEST
        )

    specimen.status = 'received'
    specimen.received_by = request.user if request.user.is_authenticated else None
    specimen.received_at = timezone.now()
    specimen.storage_location = request.data.get('storage_location', '')
    specimen.save()

    log_audit('clinical', 'specimens', specimen.id, 'UPDATE',
              new_values={'status': 'received', 'received_by': str(specimen.received_by)},
              request=request)

    return Response(SpecimenSerializer(specimen).data)


@api_view(['POST'])
@permission_classes([make_permission_class('ENCOUNTER_EDIT')])
def specimen_complete(request, specimen_id):
    from audit.utils import log_audit
    try:
        specimen = Specimen.objects.get(id=specimen_id)
    except Specimen.DoesNotExist:
        return Response({'error': 'Specimen not found'}, status=status.HTTP_404_NOT_FOUND)

    if specimen.status not in ['received', 'analyzing']:
        return Response(
            {'error': f'Specimen status "{specimen.status}" cannot be completed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    specimen.status = 'completed'
    specimen.save()

    log_audit('clinical', 'specimens', specimen.id, 'UPDATE',
              new_values={'status': 'completed'},
              request=request)

    return Response(SpecimenSerializer(specimen).data)


@api_view(['POST'])
@permission_classes([make_permission_class('TRIAGE_PERFORM')])
def emergency_bypass(request):
    from django.db import transaction
    from audit.utils import log_audit
    from patients.models import Patient

    reason = request.data.get('reason', '')
    chief_complaint = request.data.get('chief_complaint', 'Emergency presentation')
    visit_type = request.data.get('visit_type', 'er')

    if not reason:
        return Response({'error': 'Emergency bypass reason is required'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        patient_name = request.data.get('patient_name', 'UNKNOWN PATIENT')
        parts = patient_name.strip().split(' ', 1)
        first_name = parts[0] if parts else 'UNKNOWN'
        last_name = parts[1] if len(parts) > 1 else 'PATIENT'

        patient = Patient(
            first_name=first_name,
            last_name=last_name,
            gender=request.data.get('gender', 'M'),
            date_of_birth=request.data.get('date_of_birth', '1990-01-01'),
            phone=request.data.get('phone', ''),
            payer_category='Emergency Care',
        )
        patient.save()

        visit = Visit(
            patient=patient,
            visit_type=visit_type,
            chief_complaint=chief_complaint,
            status='checked_in',
            check_in_time=timezone.now(),
            is_emergency_bypass=True,
            emergency_bypass_reason=reason,
            created_by=request.user.id if request.user.is_authenticated else None,
        )
        visit.save()

        log_audit('clinical', 'visits', visit.id, 'CREATE',
                  new_values={
                      'visit_number': visit.visit_number,
                      'emergency_bypass': True,
                      'reason': reason,
                  },
                  request=request)
        log_audit('clinical', 'visits', visit.id, 'EMERGENCY_BYPASS',
                  new_values={'reason': reason, 'patient': patient.mrn},
                  request=request)

    return Response({
        'patient': {
            'id': str(patient.id),
            'mrn': patient.mrn,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
        },
        'visit': {
            'id': str(visit.id),
            'visit_number': visit.visit_number,
            'visit_type': visit.visit_type,
            'status': visit.status,
        },
        'message': 'Emergency bypass: Patient registered with temporary record. Complete registration after stabilization.'
    }, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════════════════
# ENHANCED EMERGENCY BYPASS — Instant ER with Temporary Token
# ═══════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([make_permission_class('TRIAGE_PERFORM')])
def instant_er_bypass(request):
    """
    Instant ER Bypass — creates a Visit with NO patient record.
    Returns a temporary_token (TEMP-ER-YYYY-XXXXX) for tracking.
    All clinical records are linked via visit_id only.
    """
    from audit.utils import log_audit

    chief_complaint = request.data.get('chief_complaint', 'Emergency presentation')
    patient_name = request.data.get('patient_name', 'UNKNOWN PATIENT')
    reason = request.data.get('reason', 'Immediate emergency bypass')

    with transaction.atomic():
        # Create visit with NO patient — purely token-based
        visit = Visit(
            patient=None,
            visit_type='er',
            chief_complaint=chief_complaint,
            status='checked_in',
            check_in_time=timezone.now(),
            is_emergency_bypass=True,
            emergency_bypass_reason=reason,
            created_by=request.user.id if request.user.is_authenticated else None,
        )
        visit.save()

        # Create temporary patient record flagged as temporary
        from patients.models import Patient
        parts = patient_name.strip().split(' ', 1)
        first_name = parts[0] if parts else 'UNKNOWN'
        last_name = parts[1] if len(parts) > 1 else 'PATIENT'

        patient = Patient(
            first_name=first_name,
            last_name=last_name,
            gender=request.data.get('gender', 'M'),
            date_of_birth=request.data.get('date_of_birth', '1990-01-01'),
            phone=request.data.get('phone', ''),
            payer_category='Emergency Care',
            is_temporary=True,
        )
        patient.save()

        # Link patient to visit
        visit.patient = patient
        visit.save()

        # Auto-assign acuity 1 (Resuscitation) for bypass
        visit.triage_priority = '1'
        visit.suggested_acuity = 1
        visit.suggested_department = 'ER'
        visit.save()

        # Route to ER department
        from users_auth.models import Department
        try:
            dept = Department.objects.get(code='ER')
            visit.department = dept
            visit.save()
        except Department.DoesNotExist:
            pass

        # Log workflow transition
        WorkflowTransition.objects.create(
            patient=patient,
            visit=visit,
            from_status='',
            to_status='checked_in',
            to_department=dept if 'dept' in dir() else None,
            triggered_by=request.user if request.user.is_authenticated else None,
            trigger_action='instant_er_bypass',
            metadata={'reason': reason, 'temporary_token': patient.temporary_token}
        )

        log_audit('clinical', 'visits', visit.id, 'EMERGENCY_BYPASS',
                  new_values={
                      'visit_number': visit.visit_number,
                      'temporary_token': patient.temporary_token,
                      'reason': reason,
                  },
                  request=request)

    return Response({
        'patient': {
            'id': str(patient.id),
            'temporary_token': patient.temporary_token,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'is_temporary': True,
        },
        'visit': {
            'id': str(visit.id),
            'visit_number': visit.visit_number,
            'visit_type': visit.visit_type,
            'status': visit.status,
            'temporary_token': patient.temporary_token,
        },
        'message': 'Instant ER bypass activated. Use temporary token for all clinical actions. Complete formal registration after stabilization.'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([make_permission_class('TRIAGE_PERFORM')])
def reconcile_emergency_patient(request):
    """
    Reconcile a temporary emergency patient with full demographics.
    Creates/updates Patient with formal registration, generates MRN,
    and links all clinical records.
    """
    from audit.utils import log_audit
    from patients.models import Patient

    visit_id = request.data.get('visit_id')
    if not visit_id:
        return Response({'error': 'visit_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        visit = Visit.objects.get(id=visit_id, is_emergency_bypass=True, is_deleted=False)
    except Visit.DoesNotExist:
        return Response({'error': 'Emergency bypass visit not found'}, status=status.HTTP_404_NOT_FOUND)

    patient = visit.patient
    if not patient or not patient.is_temporary:
        return Response({'error': 'Visit does not have a temporary patient record'}, status=status.HTTP_400_BAD_REQUEST)

    # Update patient with full demographics
    patient.first_name = request.data.get('first_name', patient.first_name)
    patient.last_name = request.data.get('last_name', patient.last_name)
    patient.middle_name = request.data.get('middle_name', patient.middle_name)
    patient.date_of_birth = request.data.get('date_of_birth', patient.date_of_birth)
    patient.gender = request.data.get('gender', patient.gender)
    patient.phone = request.data.get('phone', patient.phone)
    patient.blood_type = request.data.get('blood_type', patient.blood_type)
    patient.marital_status = request.data.get('marital_status', patient.marital_status)
    patient.nationality = request.data.get('nationality', patient.nationality)
    patient.address_line1 = request.data.get('address_line1', patient.address_line1)
    patient.city = request.data.get('city', patient.city)
    patient.payer_category = request.data.get('payer_category', patient.payer_category)
    patient.insurance_provider = request.data.get('insurance_provider', patient.insurance_provider)
    patient.insurance_policy_number = request.data.get('insurance_policy_number', patient.insurance_policy_number)

    # Generate MRN — patient will no longer be temporary
    patient.is_temporary = False
    if not patient.mrn:
        patient.mrn = patient._generate_mrn_with_retry()
    patient.save()

    # Optionally backfill triage if provided
    triage_data = request.data.get('triage', {})
    if triage_data:
        existing_triage = TriageRecord.objects.filter(visit=visit).first()
        if existing_triage:
            for field in ['temperature', 'heart_rate', 'respiratory_rate', 'blood_pressure_systolic',
                          'blood_pressure_diastolic', 'oxygen_saturation', 'weight', 'height',
                          'pain_scale', 'blood_glucose', 'screening_notes']:
                if field in triage_data:
                    setattr(existing_triage, field, triage_data[field])
            existing_triage.patient = patient
            existing_triage.save()

    # Transition visit status
    old_status = visit.status
    if visit.status == 'checked_in':
        visit.status = 'in_triage'
    elif visit.status in ['awaiting_reconciliation', 'pending_registration']:
        visit.status = 'in_progress'
    visit.save()

    # Link all related clinical records to the formal patient
    for model_class in [Encounter, Order, Diagnosis]:
        model_class.objects.filter(visit=visit, patient__isnull=True).update(patient=patient)

    # Log transition
    WorkflowTransition.objects.create(
        patient=patient,
        visit=visit,
        from_status=old_status,
        to_status=visit.status,
        triggered_by=request.user if request.user.is_authenticated else None,
        trigger_action='reconcile_emergency',
        metadata={
            'mrn_generated': patient.mrn,
            'temporary_token': patient.temporary_token,
        }
    )

    log_audit('clinical', 'visits', visit.id, 'RECONCILE',
              new_values={
                  'patient_mrn': patient.mrn,
                  'is_temporary': False,
                  'visit_status': visit.status,
              },
              request=request)

    return Response({
        'patient': {
            'id': str(patient.id),
            'mrn': patient.mrn,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
            'is_temporary': False,
        },
        'visit': {
            'id': str(visit.id),
            'visit_number': visit.visit_number,
            'status': visit.status,
        },
        'message': f'Patient reconciled. MRN: {patient.mrn}. All clinical records linked.'
    }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════
# CLINICAL-FIRST FLOW (Triage → Registration)
# ═══════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([make_permission_class('TRIAGE_PERFORM')])
def triage_first(request):
    """
    Clinical-First Flow: Triage assessment before formal registration.
    Creates anonymous TriageRecord + Visit with status=pending_registration.
    Returns temporary_token for tracking.
    """
    from audit.utils import log_audit
    from clinical.triage_engine import evaluate_vitals, get_acuity_label

    data = request.data.copy()
    chief_complaint = data.get('chief_complaint', '')

    # Evaluate vitals immediately
    vitals_for_evaluation = {}
    for field in ['temperature', 'heart_rate', 'respiratory_rate', 'blood_pressure_systolic',
                  'blood_pressure_diastolic', 'oxygen_saturation', 'pain_scale', 'blood_glucose']:
        if data.get(field) is not None:
            vitals_for_evaluation[field] = data.get(field)

    engine_suggestion = evaluate_vitals(vitals_for_evaluation) if vitals_for_evaluation else {
        'suggested_acuity': 5, 'suggested_department': 'OPD', 'matched_rules': [], 'reason': 'No vitals provided'
    }

    final_acuity = int(data.get('acuity_level', engine_suggestion['suggested_acuity']))
    final_department_code = data.get('department_code', engine_suggestion['suggested_department'])

    with transaction.atomic():
        # Create visit with no patient, pending registration
        visit = Visit(
            patient=None,
            visit_type=final_department_code.lower() if final_department_code else 'opd',
            chief_complaint=chief_complaint,
            status='pending_registration',
            check_in_time=timezone.now(),
            suggested_acuity=engine_suggestion['suggested_acuity'],
            suggested_department=engine_suggestion['suggested_department'],
            created_by=request.user.id if request.user.is_authenticated else None,
        )
        visit.save()

        # Create anonymous triage record
        triage_record = TriageRecord.objects.create(
            visit=visit,
            patient=None,
            chief_complaint=chief_complaint,
            acuity_level=final_acuity,
            temperature=data.get('temperature'),
            heart_rate=data.get('heart_rate'),
            respiratory_rate=data.get('respiratory_rate'),
            blood_pressure_systolic=data.get('blood_pressure_systolic'),
            blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
            oxygen_saturation=data.get('oxygen_saturation'),
            weight=data.get('weight'),
            height=data.get('height'),
            pain_scale=data.get('pain_scale'),
            blood_glucose=data.get('blood_glucose'),
            screening_notes=data.get('screening_notes', ''),
            triage_nurse=request.user if request.user.is_authenticated else None
        )

        # Route to department
        from users_auth.models import Department
        try:
            dept = Department.objects.get(code=final_department_code)
            visit.department = dept
            visit.triage_priority = str(final_acuity)
            visit.triage_time = timezone.now()
            visit.save()
        except Department.DoesNotExist:
            pass

        # Log transition
        WorkflowTransition.objects.create(
            visit=visit,
            from_status='',
            to_status='pending_registration',
            to_department=dept if 'dept' in dir() else None,
            triggered_by=request.user if request.user.is_authenticated else None,
            trigger_action='triage_first',
            metadata={
                'suggested_acuity': engine_suggestion['suggested_acuity'],
                'final_acuity': final_acuity,
                'matched_rules': engine_suggestion['matched_rules'],
            }
        )

        log_audit('clinical', 'triage_records', triage_record.id, 'CREATE',
                  new_values={
                      'acuity_level': final_acuity,
                      'chief_complaint': chief_complaint,
                      'visit_number': visit.visit_number,
                      'flow': 'clinical_first',
                  },
                  request=request)

    return Response({
        'triage_record': TriageRecordSerializer(triage_record).data,
        'suggestion': {
            'acuity_level': engine_suggestion['suggested_acuity'],
            'acuity_label': get_acuity_label(engine_suggestion['suggested_acuity']),
            'department_code': engine_suggestion['suggested_department'],
            'reason': engine_suggestion['reason'],
            'matched_rules': engine_suggestion['matched_rules'],
        },
        'visit': {
            'id': str(visit.id),
            'visit_number': visit.visit_number,
            'status': visit.status,
        },
        'message': 'Triage completed. Visit pending formal registration.'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([make_permission_class('PATIENT_CREATE')])
def complete_clinical_first_registration(request):
    """
    Complete registration for a Clinical-First visit.
    Creates Patient with full demographics, generates MRN, links to Visit.
    """
    from audit.utils import log_audit
    from patients.models import Patient

    visit_id = request.data.get('visit_id')
    if not visit_id:
        return Response({'error': 'visit_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        visit = Visit.objects.get(id=visit_id, status='pending_registration', is_deleted=False)
    except Visit.DoesNotExist:
        return Response({'error': 'Visit not found or not in pending_registration status'},
                        status=status.HTTP_404_NOT_FOUND)

    if visit.patient:
        return Response({'error': 'Visit already has a patient linked'}, status=status.HTTP_400_BAD_REQUEST)

    # Create patient
    patient = Patient(
        first_name=request.data.get('first_name', ''),
        last_name=request.data.get('last_name', ''),
        middle_name=request.data.get('middle_name', ''),
        date_of_birth=request.data.get('date_of_birth'),
        gender=request.data.get('gender', 'M'),
        phone=request.data.get('phone', ''),
        blood_type=request.data.get('blood_type', 'UNKNOWN'),
        marital_status=request.data.get('marital_status', 'unknown'),
        payer_category=request.data.get('payer_category', ''),
    )
    patient.save()

    # Link patient to visit
    visit.patient = patient
    visit.status = 'in_progress'
    visit.save()

    # Link all related clinical records
    for model_class in [TriageRecord, Encounter, Order, Diagnosis]:
        model_class.objects.filter(visit=visit, patient__isnull=True).update(patient=patient)

    # Log transition
    WorkflowTransition.objects.create(
        patient=patient,
        visit=visit,
        from_status='pending_registration',
        to_status='in_progress',
        triggered_by=request.user if request.user.is_authenticated else None,
        trigger_action='complete_clinical_first_registration',
        metadata={'mrn_generated': patient.mrn}
    )

    log_audit('clinical', 'visits', visit.id, 'UPDATE',
              new_values={
                  'patient_mrn': patient.mrn,
                  'visit_status': 'in_progress',
                  'flow': 'clinical_first_complete',
              },
              request=request)

    try:
        from billing.services import post_registration_fee_to_invoice
        post_registration_fee_to_invoice(patient, visit)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f'Registration fee posting failed: {e}')

    return Response({
        'patient': {
            'id': str(patient.id),
            'mrn': patient.mrn,
            'first_name': patient.first_name,
            'last_name': patient.last_name,
        },
        'visit': {
            'id': str(visit.id),
            'visit_number': visit.visit_number,
            'status': visit.status,
        },
        'message': f'Registration complete. MRN: {patient.mrn}. Clinical records linked.'
    }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════════════
# INTER-DEPARTMENTAL TRANSFERS
# ═══════════════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([make_permission_class('ENCOUNTER_EDIT')])
def transfer_patient(request, visit_id):
    """
    Transfer a patient between departments.
    Body: { department_code: str, reason: str }
    """
    from audit.utils import log_audit

    try:
        visit = Visit.objects.get(id=visit_id, is_deleted=False)
    except Visit.DoesNotExist:
        return Response({'error': 'Visit not found'}, status=status.HTTP_404_NOT_FOUND)

    if visit.status not in ['in_progress', 'checked_in', 'in_triage']:
        return Response({
            'error': f'Cannot transfer visit in status "{visit.status}". Must be in_progress, checked_in, or in_triage.'
        }, status=status.HTTP_400_BAD_REQUEST)

    department_code = request.data.get('department_code')
    reason = request.data.get('reason', '')

    if not department_code:
        return Response({'error': 'department_code is required'}, status=status.HTTP_400_BAD_REQUEST)

    from users_auth.models import Department
    try:
        new_dept = Department.objects.get(code=department_code)
    except Department.DoesNotExist:
        return Response({'error': f'Department "{department_code}" not found'}, status=status.HTTP_404_NOT_FOUND)

    old_department = visit.department
    old_visit_type = visit.visit_type

    # Update visit
    visit.department = new_dept

    # Update visit_type based on target department
    type_map = {'ER': 'er', 'OPD': 'opd', 'IPD': 'ipd', 'OBGYN': 'obgyn'}
    if department_code in type_map:
        visit.visit_type = type_map[department_code]

    visit.route_override = department_code
    visit.route_override_reason = reason
    visit.save()

    # Log transition
    WorkflowTransition.objects.create(
        patient=visit.patient,
        visit=visit,
        from_status=visit.status,
        to_status=visit.status,
        from_department=old_department,
        to_department=new_dept,
        triggered_by=request.user if request.user.is_authenticated else None,
        trigger_action='transfer_patient',
        metadata={
            'reason': reason,
            'from_department': old_department.code if old_department else None,
            'to_department': department_code,
            'from_visit_type': old_visit_type,
            'to_visit_type': visit.visit_type,
        }
    )

    # Create movement record
    PatientMovement.objects.create(
        patient=visit.patient,
        visit=visit,
        movement_type='department_transfer',
        from_location=old_department.name if old_department else 'None',
        to_location=new_dept.name,
        reason=reason,
        recorded_by=request.user if request.user.is_authenticated else None,
    )

    log_audit('clinical', 'visits', visit.id, 'TRANSFER',
              new_values={
                  'from_department': old_department.code if old_department else None,
                  'to_department': department_code,
                  'reason': reason,
              },
              request=request)

    return Response({
        'visit': VisitSerializer(visit).data,
        'message': f'Patient transferred from {old_department.name if old_department else "None"} to {new_dept.name}'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([make_permission_class('ENCOUNTER_EDIT')])
def escalate_to_er(request, visit_id):
    """
    One-click escalation from OPD/other to ER.
    Changes visit_type to 'er', sets department to ER, logs the escalation.
    """
    from audit.utils import log_audit

    try:
        visit = Visit.objects.get(id=visit_id, is_deleted=False)
    except Visit.DoesNotExist:
        return Response({'error': 'Visit not found'}, status=status.HTTP_404_NOT_FOUND)

    if visit.status not in ['in_progress', 'checked_in']:
        return Response({
            'error': f'Cannot escalate visit in status "{visit.status}"'
        }, status=status.HTTP_400_BAD_REQUEST)

    reason = request.data.get('reason', 'Clinical escalation to ER')

    from users_auth.models import Department
    try:
        er_dept = Department.objects.get(code='ER')
    except Department.DoesNotExist:
        return Response({'error': 'ER department not found'}, status=status.HTTP_404_NOT_FOUND)

    old_department = visit.department
    visit.visit_type = 'er'
    visit.department = er_dept
    visit.route_override = 'ER'
    visit.route_override_reason = reason
    visit.save()

    # Log transition
    WorkflowTransition.objects.create(
        patient=visit.patient,
        visit=visit,
        from_status=visit.status,
        to_status=visit.status,
        from_department=old_department,
        to_department=er_dept,
        triggered_by=request.user if request.user.is_authenticated else None,
        trigger_action='escalate_to_er',
        metadata={'reason': reason}
    )

    # Create movement record
    PatientMovement.objects.create(
        patient=visit.patient,
        visit=visit,
        movement_type='escalation_to_er',
        from_location=old_department.name if old_department else 'OPD',
        to_location='Emergency Room',
        reason=reason,
        recorded_by=request.user if request.user.is_authenticated else None,
    )

    log_audit('clinical', 'visits', visit.id, 'ESCALATE_TO_ER',
              new_values={
                  'from_department': old_department.code if old_department else None,
                  'to_department': 'ER',
                  'reason': reason,
              },
              request=request)

    return Response({
        'visit': VisitSerializer(visit).data,
        'message': f'Patient escalated to ER from {old_department.name if old_department else "OPD"}'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([make_permission_class('ENCOUNTER_EDIT')])
def admit_to_ipd(request, visit_id):
    """
    Direct admission from any active visit to IPD.
    Creates Admission record, links to visit.
    """
    from audit.utils import log_audit

    try:
        visit = Visit.objects.get(id=visit_id, is_deleted=False)
    except Visit.DoesNotExist:
        return Response({'error': 'Visit not found'}, status=status.HTTP_404_NOT_FOUND)

    if visit.status not in ['in_progress', 'checked_in']:
        return Response({
            'error': f'Cannot admit visit in status "{visit.status}"'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not visit.patient:
        return Response({'error': 'Cannot admit without a registered patient'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if already admitted
    existing_admission = Admission.objects.filter(visit=visit, status='active').first()
    if existing_admission:
        return Response({
            'error': f'Visit already has active admission {existing_admission.admission_number}'
        }, status=status.HTTP_400_BAD_REQUEST)

    bed_id = request.data.get('bed_id')
    ward_id = request.data.get('ward_id')
    admitting_diagnosis = request.data.get('admitting_diagnosis', '')
    admission_type = request.data.get('admission_type', 'emergency')

    from users_auth.models import Department
    try:
        ipd_dept = Department.objects.get(code='IPD')
    except Department.DoesNotExist:
        return Response({'error': 'IPD department not found'}, status=status.HTTP_404_NOT_FOUND)

    # Create admission
    admission = Admission(
        patient=visit.patient,
        visit=visit,
        admission_type=admission_type,
        admitting_diagnosis=admitting_diagnosis,
        admitting_provider=request.user if request.user.is_authenticated else None,
        created_by=request.user.id if request.user.is_authenticated else None,
    )

    # Assign bed if provided
    if bed_id:
        try:
            bed = Bed.objects.get(id=bed_id, is_occupied=False)
            admission.bed = bed
            admission.room = bed.room
            admission.ward = bed.room.ward
        except Bed.DoesNotExist:
            return Response({'error': 'Bed not found or already occupied'}, status=status.HTTP_400_BAD_REQUEST)

    admission.save()

    # Update visit
    visit.visit_type = 'ipd'
    visit.department = ipd_dept
    visit.save()

    # Log transition
    WorkflowTransition.objects.create(
        patient=visit.patient,
        visit=visit,
        from_status=visit.status,
        to_status=visit.status,
        from_department=visit.department,
        to_department=ipd_dept,
        triggered_by=request.user if request.user.is_authenticated else None,
        trigger_action='admit_to_ipd',
        metadata={
            'admission_number': admission.admission_number,
            'ward': admission.ward.name if admission.ward else None,
            'bed': admission.bed.bed_number if admission.bed else None,
        }
    )

    log_audit('clinical', 'admissions', admission.id, 'CREATE',
              new_values={
                  'admission_number': admission.admission_number,
                  'patient': visit.patient.mrn,
                  'ward': admission.ward.name if admission.ward else None,
                  'source_visit': visit.visit_number,
              },
              request=request)

    return Response({
        'admission': AdmissionSerializer(admission).data,
        'visit': VisitSerializer(visit).data,
        'message': f'Patient admitted to IPD. Admission: {admission.admission_number}'
    }, status=status.HTTP_201_CREATED)
