from django.contrib import admin
from .models import Patient, PatientAllergy, PatientAlert, PatientDocument, PatientConsent


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['mrn', 'first_name', 'last_name', 'gender', 'date_of_birth', 'phone', 'status']
    list_filter = ['status', 'gender', 'blood_type', 'insurance_provider']
    search_fields = ['mrn', 'first_name', 'last_name', 'phone', 'email']
    readonly_fields = ['mrn', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('MRN', {'fields': ('mrn',)}),
        ('Personal Information', {'fields': ('first_name', 'middle_name', 'last_name', 'date_of_birth', 'gender', 'blood_type', 'marital_status')}),
        ('Contact Information', {'fields': ('phone', 'email', 'address_line1', 'address_line2', 'city', 'state_province', 'country', 'postal_code')}),
        ('Demographics', {'fields': ('nationality', 'ethnicity', 'religion', 'occupation', 'education_level')}),
        ('Identification', {'fields': ('identification_type', 'identification_number')}),
        ('Next of Kin', {'fields': ('next_of_kin_name', 'next_of_kin_phone', 'next_of_kin_relationship')}),
        ('Emergency Contact', {'fields': ('emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship')}),
        ('Insurance', {'fields': ('insurance_provider', 'insurance_policy_number', 'insurance_group_number', 'insurance_expiry_date', 'payer_category', 'credit_limit')}),
        ('Status', {'fields': ('status', 'merged_into', 'registered_by', 'registered_at', 'is_deleted')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'last_modified')}),
    )


@admin.register(PatientAllergy)
class PatientAllergyAdmin(admin.ModelAdmin):
    list_display = ['patient', 'allergen', 'severity', 'status', 'recorded_at']
    list_filter = ['severity', 'status']
    search_fields = ['patient__mrn', 'allergen']


@admin.register(PatientAlert)
class PatientAlertAdmin(admin.ModelAdmin):
    list_display = ['patient', 'alert_type', 'severity', 'is_active', 'created_at']
    list_filter = ['alert_type', 'severity', 'is_active']
    search_fields = ['patient__mrn', 'alert_text']


@admin.register(PatientDocument)
class PatientDocumentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'document_type', 'document_name', 'uploaded_at']
    list_filter = ['document_type']
    search_fields = ['patient__mrn', 'document_name']


@admin.register(PatientConsent)
class PatientConsentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'consent_type', 'consent_given', 'consent_date']
    list_filter = ['consent_type', 'consent_given']
    search_fields = ['patient__mrn']
