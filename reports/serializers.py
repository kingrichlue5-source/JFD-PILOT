from rest_framework import serializers


class HMISIndicatorSerializer(serializers.Serializer):
    total_attendance = serializers.IntegerField()
    opd_attendance = serializers.IntegerField()
    er_attendance = serializers.IntegerField()
    ipd_admissions = serializers.IntegerField()
    maternal_deliveries = serializers.IntegerField()
    newborn_deliveries = serializers.IntegerField()
    lab_orders = serializers.IntegerField()
    radiology_orders = serializers.IntegerField()
    prescriptions_issued = serializers.IntegerField()
    medications_dispensed = serializers.IntegerField()
    mortality_count = serializers.IntegerField()
    revenue_collected = serializers.DecimalField(max_digits=14, decimal_places=2)


class DiagnosisCountSerializer(serializers.Serializer):
    diagnosis_code = serializers.CharField()
    diagnosis_description = serializers.CharField()
    count = serializers.IntegerField()


class HMISSummarySerializer(serializers.Serializer):
    period = serializers.CharField()
    org_unit = serializers.CharField()
    org_unit_code = serializers.CharField()
    indicators = HMISIndicatorSerializer()
    top_diagnoses = DiagnosisCountSerializer(many=True)
