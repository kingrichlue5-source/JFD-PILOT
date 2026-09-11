from django.contrib import admin
from .models import Medication, Prescription, PrescriptionItem, MedicationDispensing


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'generic_name', 'brand_name', 'dosage_form', 'strength', 'is_controlled', 'is_active']
    list_filter = ['category', 'dosage_form', 'is_controlled', 'requires_prescription', 'is_active']
    search_fields = ['name', 'generic_name', 'brand_name', 'medication_code']


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['prescription_number', 'patient', 'visit', 'prescribed_by', 'status', 'prescribed_at']
    list_filter = ['status']
    search_fields = ['prescription_number', 'patient__mrn']
    readonly_fields = ['prescription_number', 'created_at']
    date_hierarchy = 'prescribed_at'


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ['prescription', 'medication', 'dosage', 'frequency', 'quantity_prescribed', 'quantity_dispensed', 'status']
    list_filter = ['status', 'medication']
    search_fields = ['prescription__prescription_number', 'medication__name']


@admin.register(MedicationDispensing)
class MedicationDispensingAdmin(admin.ModelAdmin):
    list_display = ['medication', 'patient', 'quantity_dispensed', 'batch_lot_number', 'dispensed_by', 'dispensed_at']
    list_filter = ['medication', 'dispensed_by']
    search_fields = ['patient__mrn', 'medication__name', 'batch_lot_number']
    date_hierarchy = 'dispensed_at'
