from rest_framework import serializers
from .models import (
    Visit, TriageRecord, Encounter, VitalSigns, Diagnosis,
    Order, ProgressNote, NursingNote, Admission, AdmissionTransfer,
    Ward, Room, Bed, PatientMovement,
    LabTestCatalogue, RadiologyTestCatalogue, DiagnosticResult,
    AntenatalVisit, LaborRecord, DeliveryRecord, BirthRecord, PostnatalVisit,
    SurgicalCase, Referral, Appointment, Specimen
)
from patients.serializers import PatientSerializer


class WardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ward
        fields = ['id', 'name', 'code', 'department', 'ward_type', 'floor', 'capacity', 'is_active']


class RoomSerializer(serializers.ModelSerializer):
    ward_name = serializers.CharField(source='ward.name', read_only=True)

    class Meta:
        model = Room
        fields = ['id', 'ward', 'ward_name', 'room_number', 'room_type', 'capacity', 'is_private', 'is_active']


class BedSerializer(serializers.ModelSerializer):
    ward_name = serializers.CharField(source='room.ward.name', read_only=True)
    room_number = serializers.CharField(source='room.room_number', read_only=True)

    class Meta:
        model = Bed
        fields = ['id', 'room', 'ward_name', 'room_number', 'bed_number', 'bed_type',
                  'is_occupied', 'is_reserved', 'is_active']


class BedOccupancySerializer(serializers.Serializer):
    ward_id = serializers.UUIDField()
    ward_name = serializers.CharField()
    ward_code = serializers.CharField()
    total_beds = serializers.IntegerField()
    occupied_beds = serializers.IntegerField()
    available_beds = serializers.IntegerField()
    reserved_beds = serializers.IntegerField()


class VisitSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True, default=None)
    provider_name = serializers.SerializerMethodField()

    class Meta:
        model = Visit
        fields = ['id', 'patient', 'patient_mrn', 'patient_name', 'visit_number', 'visit_date',
                  'visit_type', 'department', 'department_name', 'status', 'chief_complaint',
                  'triage_priority', 'triage_notes', 'triage_time', 'check_in_time', 'check_out_time',
                  'provider', 'provider_name', 'attending_physician', 'nurse',
                  'is_follow_up', 'follow_up_date', 'created_at']
        read_only_fields = ['id', 'visit_number', 'visit_date', 'created_at']

    def get_patient_name(self, obj):
        if obj.patient.middle_name:
            return f"{obj.patient.first_name} {obj.patient.middle_name} {obj.patient.last_name}"
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_provider_name(self, obj):
        if obj.provider:
            return f"{obj.provider.first_name} {obj.provider.last_name}"
        return None


class VisitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visit
        fields = ['id', 'patient', 'visit_type', 'department', 'chief_complaint', 'provider',
                  'triage_priority', 'status', 'triage_notes',
                  'is_follow_up', 'follow_up_date']
        read_only_fields = ['id', 'visit_number', 'visit_date', 'created_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user.id
        return super().create(validated_data)


class TriageRecordSerializer(serializers.ModelSerializer):
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    triage_nurse_name = serializers.SerializerMethodField()

    class Meta:
        model = TriageRecord
        fields = ['id', 'visit', 'visit_number', 'patient', 'patient_mrn', 'chief_complaint',
                  'acuity_level', 'temperature', 'heart_rate', 'respiratory_rate',
                  'blood_pressure_systolic', 'blood_pressure_diastolic', 'oxygen_saturation',
                  'weight', 'height', 'pain_scale', 'blood_glucose', 'screening_notes',
                  'triage_nurse', 'triage_nurse_name', 'triage_time', 'created_at']
        read_only_fields = ['id', 'triage_time', 'created_at']

    def get_triage_nurse_name(self, obj):
        if obj.triage_nurse:
            return f"{obj.triage_nurse.first_name} {obj.triage_nurse.last_name}"
        return None


class EncounterSerializer(serializers.ModelSerializer):
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    provider_name = serializers.SerializerMethodField()

    class Meta:
        model = Encounter
        fields = ['id', 'visit', 'visit_number', 'patient', 'patient_mrn', 'encounter_type',
                  'encounter_date', 'provider', 'provider_name', 'department', 'location',
                  'status', 'subjective', 'objective', 'assessment', 'plan',
                  'diagnosis_primary', 'diagnosis_secondary', 'diagnosis_notes',
                  'is_finalized', 'finalized_at', 'signed_by', 'signed_at', 'created_at']
        read_only_fields = ['id', 'encounter_date', 'created_at']
        extra_kwargs = {
            'visit': {'required': False},
            'patient': {'required': False},
        }

    def get_provider_name(self, obj):
        if obj.provider:
            return f"{obj.provider.first_name} {obj.provider.last_name}"
        return None


class VitalSignsSerializer(serializers.ModelSerializer):
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = VitalSigns
        fields = ['id', 'visit', 'visit_number', 'patient', 'encounter',
                  'temperature', 'heart_rate', 'respiratory_rate',
                  'blood_pressure_systolic', 'blood_pressure_diastolic',
                  'oxygen_saturation', 'weight', 'height', 'bmi',
                  'pain_scale', 'blood_glucose', 'recorded_by', 'recorded_by_name',
                  'recorded_at', 'created_at']
        read_only_fields = ['id', 'recorded_at', 'created_at']
        extra_kwargs = {
            'visit': {'required': False},
            'patient': {'required': False},
        }

    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return f"{obj.recorded_by.first_name} {obj.recorded_by.last_name}"
        return None


class DiagnosisSerializer(serializers.ModelSerializer):
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)

    class Meta:
        model = Diagnosis
        fields = ['id', 'encounter', 'patient', 'visit', 'visit_number',
                  'diagnosis_code', 'diagnosis_code_system', 'diagnosis_description',
                  'diagnosis_type', 'is_principal', 'status', 'onset_date',
                  'resolved_date', 'notes', 'coded_at', 'created_at']
        read_only_fields = ['id', 'coded_at', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)
    patient_name = serializers.SerializerMethodField()
    ordering_provider_name = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'visit', 'visit_number', 'patient', 'patient_name', 'encounter',
                  'order_type', 'order_description', 'priority', 'status',
                  'ordering_provider', 'ordering_provider_name', 'ordered_at',
                  'required_by', 'completed_at', 'cancellation_reason', 'notes', 'created_at']
        read_only_fields = ['id', 'ordered_at', 'created_at']

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None

    def get_ordering_provider_name(self, obj):
        if obj.ordering_provider:
            return f"{obj.ordering_provider.first_name} {obj.ordering_provider.last_name}"
        return None


class ProgressNoteSerializer(serializers.ModelSerializer):
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = ProgressNote
        fields = ['id', 'encounter', 'patient', 'visit', 'visit_number',
                  'note_type', 'subjective', 'objective', 'assessment', 'plan',
                  'note_text', 'author', 'author_name', 'authored_at',
                  'is_signed', 'signed_at', 'created_at']
        read_only_fields = ['id', 'authored_at', 'created_at']
        extra_kwargs = {
            'encounter': {'required': False},
            'patient': {'required': False},
            'visit': {'required': False},
            'author': {'required': False},
        }

    def get_author_name(self, obj):
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}"
        return None


class NursingNoteSerializer(serializers.ModelSerializer):
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = NursingNote
        fields = ['id', 'encounter', 'patient', 'visit', 'visit_number',
                  'note_type', 'note_text', 'interventions', 'patient_response',
                  'author', 'author_name', 'authored_at', 'created_at']
        read_only_fields = ['id', 'authored_at', 'created_at']

    def get_author_name(self, obj):
        if obj.author:
            return f"{obj.author.first_name} {obj.author.last_name}"
        return None


class AdmissionSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()
    ward_name = serializers.CharField(source='ward.name', read_only=True, default=None)
    room_number = serializers.CharField(source='room.room_number', read_only=True, default=None)
    bed_number = serializers.CharField(source='bed.bed_number', read_only=True, default=None)
    admitting_provider_name = serializers.SerializerMethodField()

    class Meta:
        model = Admission
        fields = ['id', 'patient', 'patient_mrn', 'patient_name', 'visit',
                  'admission_number', 'admission_date', 'admission_type',
                  'admitting_diagnosis', 'admitting_provider', 'admitting_provider_name',
                  'ward', 'ward_name', 'room', 'room_number', 'bed', 'bed_number',
                  'expected_discharge_date', 'actual_discharge_date', 'discharge_type',
                  'discharge_summary', 'discharge_provider', 'status', 'created_at']
        read_only_fields = ['id', 'admission_number', 'admission_date', 'created_at']

    def get_patient_name(self, obj):
        if obj.patient.middle_name:
            return f"{obj.patient.first_name} {obj.patient.middle_name} {obj.patient.last_name}"
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_admitting_provider_name(self, obj):
        if obj.admitting_provider:
            return f"{obj.admitting_provider.first_name} {obj.admitting_provider.last_name}"
        return None


class AdmissionTransferSerializer(serializers.ModelSerializer):
    from_ward_name = serializers.CharField(source='from_ward.name', read_only=True, default=None)
    to_ward_name = serializers.CharField(source='to_ward.name', read_only=True, default=None)
    transferred_by_name = serializers.SerializerMethodField()

    class Meta:
        model = AdmissionTransfer
        fields = ['id', 'admission', 'from_ward', 'from_ward_name', 'from_room', 'from_bed',
                  'to_ward', 'to_ward_name', 'to_room', 'to_bed', 'transfer_reason',
                  'transferred_by', 'transferred_by_name', 'transferred_at', 'created_at']
        read_only_fields = ['id', 'transferred_at', 'created_at']
        extra_kwargs = {
            'from_ward': {'required': False},
            'from_room': {'required': False},
            'from_bed': {'required': False},
            'to_ward': {'required': False},
            'to_room': {'required': False},
            'transfer_reason': {'required': False},
        }

    def get_transferred_by_name(self, obj):
        if obj.transferred_by:
            return f"{obj.transferred_by.first_name} {obj.transferred_by.last_name}"
        return None


class PatientMovementSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    recorded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientMovement
        fields = ['id', 'patient', 'patient_mrn', 'visit', 'admission',
                  'movement_type', 'from_location', 'to_location', 'movement_time',
                  'reason', 'recorded_by', 'recorded_by_name', 'created_at']
        read_only_fields = ['id', 'movement_time', 'created_at']

    def get_recorded_by_name(self, obj):
        if obj.recorded_by:
            return f"{obj.recorded_by.first_name} {obj.recorded_by.last_name}"
        return None


class LabTestCatalogueSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabTestCatalogue
        fields = ['id', 'name', 'code', 'category', 'specimen_type', 'turnaround_time', 'price', 'is_active']
        read_only_fields = ['id']


class RadiologyTestCatalogueSerializer(serializers.ModelSerializer):
    class Meta:
        model = RadiologyTestCatalogue
        fields = ['id', 'name', 'code', 'body_part', 'modality', 'turnaround_time', 'price', 'is_active']
        read_only_fields = ['id']


class DiagnosticResultSerializer(serializers.ModelSerializer):
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    order_type = serializers.CharField(source='order.order_type', read_only=True)
    order_description = serializers.CharField(source='order.order_description', read_only=True)

    class Meta:
        model = DiagnosticResult
        fields = ['id', 'order', 'patient', 'patient_mrn', 'visit', 'visit_number',
                  'order_type', 'order_description', 'result_text', 'result_file_url',
                  'is_abnormal', 'critical_flag', 'verified_by', 'verified_at',
                  'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class EncounterDetailSerializer(serializers.ModelSerializer):
    visit_number = serializers.CharField(source='visit.visit_number', read_only=True)
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    provider_name = serializers.SerializerMethodField()
    diagnoses = serializers.SerializerMethodField()
    orders = serializers.SerializerMethodField()
    vitals = serializers.SerializerMethodField()
    triage = serializers.SerializerMethodField()

    class Meta:
        model = Encounter
        fields = ['id', 'visit', 'visit_number', 'patient', 'patient_mrn', 'encounter_type',
                  'encounter_date', 'provider', 'provider_name', 'department', 'location',
                  'status', 'subjective', 'objective', 'assessment', 'plan',
                  'diagnosis_primary', 'diagnosis_secondary', 'diagnosis_notes',
                  'is_finalized', 'finalized_at', 'diagnoses', 'orders', 'vitals', 'triage', 'created_at']
        read_only_fields = ['id', 'encounter_date', 'created_at']

    def get_provider_name(self, obj):
        if obj.provider:
            return f"{obj.provider.first_name} {obj.provider.last_name}"
        return None

    def get_diagnoses(self, obj):
        diagnoses = Diagnosis.objects.filter(encounter=obj)
        return DiagnosisSerializer(diagnoses, many=True).data

    def get_orders(self, obj):
        orders = Order.objects.filter(encounter=obj)
        return OrderSerializer(orders, many=True).data

    def get_vitals(self, obj):
        vitals = VitalSigns.objects.filter(visit=obj.visit).order_by('-recorded_at')[:5]
        return VitalSignsSerializer(vitals, many=True).data

    def get_triage(self, obj):
        triage = TriageRecord.objects.filter(visit=obj.visit).order_by('-created_at').first()
        if triage:
            return TriageRecordSerializer(triage).data
        return None


class AntenatalVisitSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = AntenatalVisit
        fields = '__all__'
        read_only_fields = ['id', 'visit_number', 'created_at', 'updated_at']

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"


class LaborRecordSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = LaborRecord
        fields = '__all__'
        read_only_fields = ['id', 'labor_number', 'created_at', 'updated_at']

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None


class DeliveryRecordSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryRecord
        fields = '__all__'
        read_only_fields = ['id', 'delivery_number', 'created_at', 'updated_at']

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None


class BirthRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BirthRecord
        fields = '__all__'
        read_only_fields = ['id', 'birth_number', 'created_at', 'updated_at']


class PostnatalVisitSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()

    class Meta:
        model = PostnatalVisit
        fields = '__all__'
        read_only_fields = ['id', 'visit_number', 'created_at', 'updated_at']

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None


class SurgicalCaseSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()
    surgeon_name = serializers.SerializerMethodField()

    class Meta:
        model = SurgicalCase
        fields = '__all__'
        read_only_fields = ['id', 'case_number', 'created_at', 'updated_at']

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None

    def get_surgeon_name(self, obj):
        if obj.surgeon:
            return f"{obj.surgeon.first_name} {obj.surgeon.last_name}"
        return None


class ReferralSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    referring_provider_name = serializers.SerializerMethodField()
    receiving_provider_name = serializers.SerializerMethodField()

    class Meta:
        model = Referral
        fields = '__all__'
        read_only_fields = ['id', 'referral_number', 'referral_date', 'updated_at']

    def get_referring_provider_name(self, obj):
        if obj.referring_provider:
            return f"{obj.referring_provider.first_name} {obj.referring_provider.last_name}"
        return None

    def get_receiving_provider_name(self, obj):
        if obj.receiving_provider:
            return f"{obj.receiving_provider.first_name} {obj.receiving_provider.last_name}"
        return None


class AppointmentSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()
    provider_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['id', 'appointment_number', 'created_at', 'updated_at']

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_provider_name(self, obj):
        if obj.provider:
            return f"{obj.provider.first_name} {obj.provider.last_name}"
        return None

    def validate(self, attrs):
        provider = attrs.get('provider') or getattr(self.instance, 'provider', None)
        appointment_date = attrs.get('appointment_date') or getattr(self.instance, 'appointment_date', None)
        appointment_time = attrs.get('appointment_time') or getattr(self.instance, 'appointment_time', None)
        duration = attrs.get('duration_minutes') or getattr(self.instance, 'duration_minutes', 30)

        if provider and appointment_date and appointment_time:
            from datetime import datetime, timedelta
            new_start = datetime.combine(appointment_date, appointment_time)
            new_end = new_start + timedelta(minutes=duration)

            existing = Appointment.objects.filter(
                provider=provider,
                appointment_date=appointment_date,
                status__in=['scheduled', 'confirmed', 'checked_in', 'in_progress'],
            ).exclude(pk=getattr(self.instance, 'pk', None))

            for appt in existing:
                if appt.appointment_time is None:
                    continue
                exist_start = datetime.combine(appt.appointment_date, appt.appointment_time)
                exist_end = exist_start + timedelta(minutes=appt.duration_minutes or 30)
                if new_start < exist_end and new_end > exist_start:
                    raise serializers.ValidationError(
                        f'Scheduling conflict: {provider.first_name} {provider.last_name} '
                        f'already has an appointment at {appt.appointment_time} on {appointment_date} '
                        f'(APT-{appt.appointment_number}).'
                    )

        return attrs


class SpecimenSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    order_type = serializers.CharField(source='order.order_type', read_only=True, default=None)
    collected_by_name = serializers.SerializerMethodField()
    received_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Specimen
        fields = '__all__'
        read_only_fields = ['id', 'specimen_number', 'barcode', 'created_at', 'updated_at']

    def get_patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"

    def get_collected_by_name(self, obj):
        if obj.collected_by:
            return f"{obj.collected_by.first_name} {obj.collected_by.last_name}"
        return None

    def get_received_by_name(self, obj):
        if obj.received_by:
            return f"{obj.received_by.first_name} {obj.received_by.last_name}"
        return None
