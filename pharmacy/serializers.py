from rest_framework import serializers
from .models import Medication, Prescription, PrescriptionItem, MedicationDispensing


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ['id', 'name', 'generic_name', 'brand_name', 'medication_code',
                  'category', 'dosage_form', 'strength', 'unit', 'route',
                  'manufacturer', 'is_controlled', 'controlled_schedule',
                  'requires_prescription', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class PrescriptionItemSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    dispensed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = PrescriptionItem
        fields = ['id', 'prescription', 'medication', 'medication_name', 'dosage',
                  'frequency', 'duration', 'quantity_prescribed', 'quantity_dispensed',
                  'route', 'instructions', 'refills_allowed', 'refills_used',
                  'status', 'dispensed_by', 'dispensed_by_name', 'dispensed_at', 'created_at']
        read_only_fields = ['id', 'quantity_dispensed', 'created_at']

    def get_dispensed_by_name(self, obj):
        if obj.dispensed_by:
            return f"{obj.dispensed_by.first_name} {obj.dispensed_by.last_name}"
        return None


class PrescriptionSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()
    prescribed_by_name = serializers.SerializerMethodField()
    items = PrescriptionItemSerializer(many=True, read_only=True)

    class Meta:
        model = Prescription
        fields = ['id', 'visit', 'patient', 'patient_mrn', 'patient_name', 'encounter',
                  'prescription_number', 'prescribed_by', 'prescribed_by_name',
                  'status', 'notes', 'items', 'created_at']
        read_only_fields = ['id', 'prescription_number', 'prescribed_at', 'created_at']

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None

    def get_prescribed_by_name(self, obj):
        if obj.prescribed_by:
            return f"{obj.prescribed_by.first_name} {obj.prescribed_by.last_name}"
        return None


class MedicationDispensingSerializer(serializers.ModelSerializer):
    medication_name = serializers.CharField(source='medication.name', read_only=True)
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)
    patient_name = serializers.SerializerMethodField()
    dispensed_by_name = serializers.SerializerMethodField()
    store_name = serializers.SerializerMethodField()

    class Meta:
        model = MedicationDispensing
        fields = ['id', 'prescription_item', 'medication', 'medication_name',
                  'patient', 'patient_mrn', 'patient_name', 'quantity_dispensed', 'batch_lot_number',
                  'expiry_date', 'unit_cost', 'total_cost', 'inventory_stock',
                  'store_name', 'dispensed_by', 'dispensed_by_name',
                  'dispensed_at', 'notes', 'created_at']
        read_only_fields = ['id', 'dispensed_at', 'created_at']

    def get_patient_name(self, obj):
        if obj.patient:
            return f"{obj.patient.first_name} {obj.patient.last_name}"
        return None

    def get_dispensed_by_name(self, obj):
        if obj.dispensed_by:
            return f"{obj.dispensed_by.first_name} {obj.dispensed_by.last_name}"
        return None

    def get_store_name(self, obj):
        if obj.inventory_stock and obj.inventory_stock.store:
            return obj.inventory_stock.store.name
        return None
