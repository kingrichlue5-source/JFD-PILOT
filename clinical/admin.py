from django.contrib import admin
from .models import (
    Ward, Room, Bed, Visit, TriageRecord, Encounter, VitalSigns,
    Diagnosis, Order, ProgressNote, NursingNote, Admission,
    AdmissionTransfer, PatientMovement,
    LabTestCatalogue, RadiologyTestCatalogue, DiagnosticResult,
    AntenatalVisit, LaborRecord, DeliveryRecord, BirthRecord, PostnatalVisit,
    SurgicalCase, Referral, Appointment,
    ERNurseEvaluation, PediatricAssessment
)


@admin.register(Ward)
class WardAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'department', 'ward_type', 'capacity', 'is_active']
    list_filter = ['ward_type', 'is_active']
    search_fields = ['name', 'code']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['ward', 'room_number', 'room_type', 'capacity', 'is_private', 'is_active']
    list_filter = ['room_type', 'is_private', 'is_active']
    search_fields = ['room_number']


@admin.register(Bed)
class BedAdmin(admin.ModelAdmin):
    list_display = ['room', 'bed_number', 'bed_type', 'is_occupied', 'is_reserved', 'is_active']
    list_filter = ['bed_type', 'is_occupied', 'is_reserved', 'is_active']
    search_fields = ['bed_number']


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ['visit_number', 'patient', 'visit_type', 'status', 'visit_date', 'provider']
    list_filter = ['visit_type', 'status', 'visit_date']
    search_fields = ['visit_number', 'patient__mrn']
    readonly_fields = ['visit_number', 'created_at']
    date_hierarchy = 'visit_date'


@admin.register(TriageRecord)
class TriageRecordAdmin(admin.ModelAdmin):
    list_display = ['visit', 'patient', 'acuity_level', 'triage_nurse', 'triage_time']
    list_filter = ['acuity_level']
    search_fields = ['visit__visit_number', 'patient__mrn']


@admin.register(Encounter)
class EncounterAdmin(admin.ModelAdmin):
    list_display = ['visit', 'patient', 'encounter_type', 'provider', 'status', 'is_finalized']
    list_filter = ['encounter_type', 'status', 'is_finalized']
    search_fields = ['visit__visit_number', 'patient__mrn']
    date_hierarchy = 'encounter_date'


@admin.register(VitalSigns)
class VitalSignsAdmin(admin.ModelAdmin):
    list_display = ['visit', 'patient', 'temperature', 'heart_rate', 'blood_pressure_systolic', 'recorded_at']
    list_filter = ['recorded_at']
    search_fields = ['visit__visit_number', 'patient__mrn']
    date_hierarchy = 'recorded_at'


@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ['encounter', 'patient', 'diagnosis_code', 'diagnosis_type', 'status']
    list_filter = ['diagnosis_type', 'status', 'diagnosis_code_system']
    search_fields = ['diagnosis_code', 'diagnosis_description', 'patient__mrn']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['visit', 'patient', 'order_type', 'priority', 'status', 'ordering_provider']
    list_filter = ['order_type', 'priority', 'status']
    search_fields = ['visit__visit_number', 'patient__mrn']
    date_hierarchy = 'ordered_at'


@admin.register(ProgressNote)
class ProgressNoteAdmin(admin.ModelAdmin):
    list_display = ['visit', 'patient', 'note_type', 'author', 'is_signed', 'authored_at']
    list_filter = ['note_type', 'is_signed']
    search_fields = ['visit__visit_number', 'patient__mrn']
    date_hierarchy = 'authored_at'


@admin.register(NursingNote)
class NursingNoteAdmin(admin.ModelAdmin):
    list_display = ['visit', 'patient', 'note_type', 'author', 'authored_at']
    list_filter = ['note_type']
    search_fields = ['visit__visit_number', 'patient__mrn']
    date_hierarchy = 'authored_at'


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'patient', 'ward', 'status', 'admission_date']
    list_filter = ['status', 'ward', 'discharge_type']
    search_fields = ['admission_number', 'patient__mrn']
    readonly_fields = ['admission_number', 'created_at']
    date_hierarchy = 'admission_date'


@admin.register(AdmissionTransfer)
class AdmissionTransferAdmin(admin.ModelAdmin):
    list_display = ['admission', 'from_ward', 'to_ward', 'transferred_by', 'transferred_at']
    list_filter = ['from_ward', 'to_ward']
    search_fields = ['admission__admission_number']
    date_hierarchy = 'transferred_at'


@admin.register(PatientMovement)
class PatientMovementAdmin(admin.ModelAdmin):
    list_display = ['patient', 'movement_type', 'from_location', 'to_location', 'movement_time']
    list_filter = ['movement_type']
    search_fields = ['patient__mrn']
    date_hierarchy = 'movement_time'


@admin.register(LabTestCatalogue)
class LabTestCatalogueAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'category', 'specimen_type', 'price', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'code']


@admin.register(RadiologyTestCatalogue)
class RadiologyTestCatalogueAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'modality', 'body_part', 'price', 'is_active']
    list_filter = ['modality', 'is_active']
    search_fields = ['name', 'code']


@admin.register(DiagnosticResult)
class DiagnosticResultAdmin(admin.ModelAdmin):
    list_display = ['order', 'patient', 'visit', 'is_abnormal', 'critical_flag', 'verified_by', 'created_at']
    list_filter = ['is_abnormal', 'critical_flag']
    search_fields = ['patient__mrn', 'visit__visit_number']
    date_hierarchy = 'created_at'


@admin.register(AntenatalVisit)
class AntenatalVisitAdmin(admin.ModelAdmin):
    list_display = ['visit_number', 'patient', 'ga_weeks', 'gravida', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['visit_number', 'patient__mrn']
    date_hierarchy = 'created_at'


@admin.register(LaborRecord)
class LaborRecordAdmin(admin.ModelAdmin):
    list_display = ['labor_number', 'patient', 'admission_time', 'status']
    list_filter = ['status']
    search_fields = ['labor_number', 'patient__mrn']
    date_hierarchy = 'admission_time'


@admin.register(DeliveryRecord)
class DeliveryRecordAdmin(admin.ModelAdmin):
    list_display = ['delivery_number', 'patient', 'delivery_time', 'delivery_method']
    list_filter = ['delivery_method']
    search_fields = ['delivery_number', 'patient__mrn']
    date_hierarchy = 'delivery_time'


@admin.register(BirthRecord)
class BirthRecordAdmin(admin.ModelAdmin):
    list_display = ['birth_number', 'baby_name', 'sex', 'birth_weight_grams', 'status']
    list_filter = ['sex', 'status']
    search_fields = ['birth_number', 'baby_name']
    date_hierarchy = 'created_at'


@admin.register(PostnatalVisit)
class PostnatalVisitAdmin(admin.ModelAdmin):
    list_display = ['visit_number', 'patient', 'visit_day_postpartum', 'status']
    list_filter = ['status']
    search_fields = ['visit_number', 'patient__mrn']
    date_hierarchy = 'created_at'


@admin.register(SurgicalCase)
class SurgicalCaseAdmin(admin.ModelAdmin):
    list_display = ['case_number', 'patient', 'procedure_name', 'surgeon', 'status', 'scheduled_date']
    list_filter = ['status', 'priority', 'anesthesia_type']
    search_fields = ['case_number', 'procedure_name', 'patient__mrn']
    date_hierarchy = 'scheduled_date'


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ['referral_number', 'patient', 'referral_type', 'urgency', 'status', 'referral_date']
    list_filter = ['referral_type', 'urgency', 'status']
    search_fields = ['referral_number', 'patient__mrn']
    date_hierarchy = 'referral_date'


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['appointment_number', 'patient', 'appointment_date', 'appointment_time', 'status']
    list_filter = ['status', 'appointment_type']
    search_fields = ['appointment_number', 'patient__mrn']
    date_hierarchy = 'appointment_date'


@admin.register(ERNurseEvaluation)
class ERNurseEvaluationAdmin(admin.ModelAdmin):
    list_display = ['patient', 'visit', 'triage_category', 'disposition', 'completed_by', 'completed_at']
    list_filter = ['triage_category', 'disposition', 'mode_of_arrival']
    search_fields = ['patient__mrn', 'visit__visit_number']
    date_hierarchy = 'completed_at'


@admin.register(PediatricAssessment)
class PediatricAssessmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'visit', 'visit_type', 'completed_by', 'completed_at']
    list_filter = ['visit_type']
    search_fields = ['patient__mrn', 'visit__visit_number']
    date_hierarchy = 'completed_at'
