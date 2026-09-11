from rest_framework import serializers
from .models import Patient, PatientAllergy, PatientAlert, PatientDocument, PatientConsent


class PatientSearchSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'mrn', 'first_name', 'middle_name', 'last_name', 'full_name',
                  'date_of_birth', 'age', 'gender', 'phone', 'email', 'status',
                  'insurance_provider', 'payer_category']

    def get_full_name(self, obj):
        if obj.middle_name:
            return f"{obj.first_name} {obj.middle_name} {obj.last_name}"
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        if obj.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - obj.date_of_birth.year - (
                (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
            )
        return None


class PatientSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()
    allergies_count = serializers.SerializerMethodField()
    alerts_count = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'mrn', 'first_name', 'middle_name', 'last_name', 'full_name',
                  'date_of_birth', 'age', 'gender', 'blood_type', 'marital_status',
                  'nationality', 'ethnicity', 'religion', 'occupation', 'education_level',
                  'phone', 'email', 'address_line1', 'address_line2', 'city',
                  'state_province', 'country', 'postal_code', 'photo',
                  'identification_type', 'identification_number',
                  'next_of_kin_name', 'next_of_kin_phone', 'next_of_kin_relationship',
                  'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
                  'insurance_provider', 'insurance_policy_number', 'insurance_group_number',
                  'insurance_expiry_date', 'payer_category', 'credit_limit',
                  'status', 'allergies_count', 'alerts_count',
                  'registered_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'mrn', 'registered_at', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        if obj.middle_name:
            return f"{obj.first_name} {obj.middle_name} {obj.last_name}"
        return f"{obj.first_name} {obj.last_name}"

    def get_age(self, obj):
        if obj.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - obj.date_of_birth.year - (
                (today.month, today.day) < (obj.date_of_birth.month, obj.date_of_birth.day)
            )
        return None

    def get_allergies_count(self, obj):
        return obj.allergies.filter(status='active').count()

    def get_alerts_count(self, obj):
        return obj.alerts.filter(is_active=True).count()


class PatientCreateSerializer(serializers.ModelSerializer):
    allergies = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    alerts = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)

    class Meta:
        model = Patient
        fields = ['first_name', 'middle_name', 'last_name', 'date_of_birth', 'gender',
                  'blood_type', 'marital_status', 'nationality', 'ethnicity', 'religion',
                  'occupation', 'education_level', 'phone', 'email',
                  'address_line1', 'address_line2', 'city', 'state_province', 'country',
                  'postal_code', 'identification_type', 'identification_number',
                  'next_of_kin_name', 'next_of_kin_phone', 'next_of_kin_relationship',
                  'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
                   'insurance_provider', 'insurance_policy_number', 'insurance_group_number',
                   'insurance_expiry_date', 'payer_category', 'credit_limit', 'photo',
                   'allergies', 'alerts']

    def validate(self, attrs):
        first_name = attrs.get('first_name', '').strip().lower()
        last_name = attrs.get('last_name', '').strip().lower()
        dob = attrs.get('date_of_birth')
        phone = attrs.get('phone', '').strip()

        if first_name and last_name and dob:
            matches = Patient.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
                date_of_birth=dob
            )
            if matches.exists():
                existing = matches.first()
                raise serializers.ValidationError(
                    f'Potential duplicate: {existing.mrn} - {existing.first_name} {existing.last_name} (DOB: {existing.date_of_birth}). Use merge endpoint if confirmed.'
                )

        if phone and len(phone) >= 7:
            matches = Patient.objects.filter(phone=phone)
            if matches.exists():
                existing = matches.first()
                raise serializers.ValidationError(
                    f'Potential duplicate: {existing.mrn} - {existing.first_name} {existing.last_name} (Phone: {existing.phone}). Use merge endpoint if confirmed.'
                )

        return attrs

    def create(self, validated_data):
        allergies_data = validated_data.pop('allergies', [])
        alerts_data = validated_data.pop('alerts', [])

        patient = Patient.objects.create(**validated_data)

        for allergy_data in allergies_data:
            PatientAllergy.objects.create(patient=patient, **allergy_data)

        for alert_data in alerts_data:
            PatientAlert.objects.create(patient=patient, **alert_data)

        return patient


class PatientAllergySerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)

    class Meta:
        model = PatientAllergy
        fields = ['id', 'patient', 'patient_mrn', 'allergen', 'allergy_type', 'severity',
                  'reaction', 'onset_date', 'status', 'notes', 'recorded_at', 'created_at']
        read_only_fields = ['id', 'recorded_at', 'created_at']


class PatientAlertSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)

    class Meta:
        model = PatientAlert
        fields = ['id', 'patient', 'patient_mrn', 'alert_type', 'alert_text', 'severity',
                  'is_active', 'expires_at', 'created_at']
        read_only_fields = ['id', 'created_at']


class PatientDocumentSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)

    class Meta:
        model = PatientDocument
        fields = ['id', 'patient', 'patient_mrn', 'document_type', 'document_name',
                  'file_url', 'file_size', 'mime_type', 'description', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class PatientConsentSerializer(serializers.ModelSerializer):
    patient_mrn = serializers.CharField(source='patient.mrn', read_only=True)

    class Meta:
        model = PatientConsent
        fields = ['id', 'patient', 'patient_mrn', 'consent_type', 'consent_given',
                  'consent_date', 'expiry_date', 'witness_name', 'notes', 'created_at']
        read_only_fields = ['id', 'consent_date', 'created_at']
