from django.db.models import Q
from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Medication, Prescription, PrescriptionItem, MedicationDispensing
from .serializers import (
    MedicationSerializer, PrescriptionSerializer,
    PrescriptionItemSerializer, MedicationDispensingSerializer
)
from jfd_hms.permissions import require_permission, make_permission_class


class MedicationListView(generics.ListCreateAPIView):
    queryset = Medication.objects.filter(is_active=True)
    serializer_class = MedicationSerializer
    permission_classes = [make_permission_class('RX_VIEW')]

    def get_queryset(self):
        queryset = Medication.objects.filter(is_active=True)
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(generic_name__icontains=search) |
                Q(brand_name__icontains=search)
            )

        if category:
            queryset = queryset.filter(category=category)

        return queryset


class MedicationDetailView(generics.RetrieveUpdateAPIView):
    queryset = Medication.objects.all()
    serializer_class = MedicationSerializer
    permission_classes = [make_permission_class('RX_MANAGE')]


class PrescriptionListView(generics.ListCreateAPIView):
    serializer_class = PrescriptionSerializer
    permission_classes = [make_permission_class('RX_VIEW')]

    def get_queryset(self):
        queryset = Prescription.objects.all()
        patient = self.request.query_params.get('patient', None)
        status_filter = self.request.query_params.get('status', None)

        if patient:
            queryset = queryset.filter(patient_id=patient)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def perform_create(self, serializer):
        serializer.save(prescribed_by=self.request.user)


class PrescriptionDetailView(generics.RetrieveUpdateAPIView):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [make_permission_class('RX_MANAGE')]


class PrescriptionItemListView(generics.ListCreateAPIView):
    serializer_class = PrescriptionItemSerializer
    permission_classes = [make_permission_class('RX_VIEW')]

    def get_queryset(self):
        return PrescriptionItem.objects.filter(prescription_id=self.kwargs['prescription_id'])

    def perform_create(self, serializer):
        prescription_item = serializer.save()
        try:
            from billing.services import post_prescription_item_to_invoice
            prescription = prescription_item.prescription
            post_prescription_item_to_invoice(
                prescription_item,
                prescription.visit,
                prescription.patient
            )
        except Exception as e:
            logger.error(
                f"Failed to post prescription item {prescription_item.id} "
                f"to invoice: {e}", exc_info=True
            )


class PrescriptionItemDetailView(generics.RetrieveUpdateAPIView):
    queryset = PrescriptionItem.objects.all()
    serializer_class = PrescriptionItemSerializer
    permission_classes = [make_permission_class('RX_MANAGE')]


class DispensingListView(generics.ListAPIView):
    serializer_class = MedicationDispensingSerializer
    permission_classes = [make_permission_class('RX_VIEW')]

    def get_queryset(self):
        queryset = MedicationDispensing.objects.all()
        patient = self.request.query_params.get('patient', None)
        medication = self.request.query_params.get('medication', None)

        if patient:
            queryset = queryset.filter(patient_id=patient)
        if medication:
            queryset = queryset.filter(medication_id=medication)

        return queryset


class DispensingDetailView(generics.RetrieveAPIView):
    queryset = MedicationDispensing.objects.all()
    serializer_class = MedicationDispensingSerializer
    permission_classes = [make_permission_class('RX_VIEW')]


@api_view(['POST'])
@permission_classes([make_permission_class('RX_DISPENSE')])
def dispense_medication(request):
    from decimal import Decimal
    from django.utils import timezone as tz
    from django.db import transaction, models
    from inventory.models import Stock, StockMovement, Item as InventoryItem

    prescription_item_id = request.data.get('prescription_item_id')
    quantity = request.data.get('quantity')
    batch_lot_number = request.data.get('batch_lot_number', '')
    expiry_date = request.data.get('expiry_date', None)
    store_id = request.data.get('store_id', None)
    waived = request.data.get('waived', False)
    waived_by_user_id = request.data.get('waived_by_user_id', None)

    if not prescription_item_id or not quantity:
        return Response(
            {'error': 'prescription_item_id and quantity are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        item = PrescriptionItem.objects.get(id=prescription_item_id)
    except PrescriptionItem.DoesNotExist:
        return Response({'error': 'Prescription item not found'}, status=status.HTTP_404_NOT_FOUND)

    remaining = item.quantity_prescribed - item.quantity_dispensed
    quantity = Decimal(str(quantity))
    if quantity > remaining:
        return Response(
            {'error': f'Only {remaining} units remaining to dispense'},
            status=status.HTTP_400_BAD_REQUEST
        )

    from patients.models import PatientAllergy
    patient = item.prescription.patient
    medication = item.medication
    allergy_warnings = []
    patient_allergies = PatientAllergy.objects.filter(patient=patient, status='active')
    med_name = (medication.name or '').lower()
    med_generic = (medication.generic_name or '').lower()
    med_category = (medication.category or '').lower()
    for allergy in patient_allergies:
        allergen = (allergy.allergen or '').lower()
        if (allergen in med_name or allergen in med_generic or allergen in med_category or
                med_name in allergen or med_generic in allergen):
            allergy_warnings.append({
                'allergen': allergy.allergen,
                'severity': allergy.severity,
                'reaction': allergy.reaction or 'Not specified',
                'message': f'Patient allergic to {allergy.allergen}. Medication {medication.name} may be contraindicated.',
            })

    from .models import DrugInteraction
    interaction_warnings = []
    other_meds = PrescriptionItem.objects.filter(
        prescription__patient=patient,
        status='completed'
    ).exclude(id=item.id).values_list('medication_id', flat=True)
    if other_meds:
        interactions = DrugInteraction.objects.filter(
            models.Q(drug_a=medication, drug_b_id__in=other_meds) |
            models.Q(drug_b=medication, drug_a_id__in=other_meds),
            is_active=True
        )
        for interaction in interactions:
            other = interaction.drug_b if interaction.drug_a == medication else interaction.drug_a
            interaction_warnings.append({
                'drug_a': interaction.drug_a.name,
                'drug_b': interaction.drug_b.name,
                'severity': interaction.severity,
                'description': interaction.description,
                'recommendation': interaction.recommendation or '',
            })

    from billing.models import InvoiceLineItem
    line_item = InvoiceLineItem.objects.filter(
        prescription_item=item
    ).first()

    if not waived:
        if not line_item:
            return Response(
                {'error': 'No invoice line item found for this prescription. Billing must be set up before dispensing.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if line_item.payment_status != 'paid':
            balance = line_item.total_amount - line_item.paid_amount
            return Response(
                {'error': f'Payment required before dispensing. Line item status: {line_item.payment_status}. Amount due: {balance}'},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        if line_item and line_item.payment_status != 'waived':
            allowed_roles = ['PHARMACIST', 'DOCTOR', 'ADMIN', 'SYS_ADMIN']
            from users_auth.models import UserRole
            user_roles = UserRole.objects.filter(
                user_id=request.user.id if request.user.is_authenticated else None,
                role__code__in=allowed_roles
            )
            if not user_roles.exists():
                return Response(
                    {'error': 'Unauthorized: only Pharmacists, Doctors, or Admins can waive payment'},
                    status=status.HTTP_403_FORBIDDEN
                )
            line_item.payment_status = 'waived'
            line_item.save()

    if not store_id:
        from inventory.models import Store
        default_store = Store.objects.filter(
            store_type='pharmacy', is_active=True
        ).first()
        if default_store:
            store_id = str(default_store.id)

    # Atomic stock deduction with select_for_update to prevent race conditions
    stock = None
    if store_id:
        with transaction.atomic():
            stock_query = Stock.objects.select_for_update().filter(
                item__medication=item.medication,
                store_id=store_id,
                quantity_on_hand__gte=quantity
            )
            if batch_lot_number:
                stock = stock_query.filter(batch_lot_number=batch_lot_number).first()
            else:
                stock = stock_query.order_by('expiry_date').first()

            if not stock:
                return Response(
                    {'error': 'Insufficient stock or no matching batch/lot found for this medication in the selected store'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if stock.expiry_date and stock.expiry_date < tz.now().date():
                return Response(
                    {'error': f'Stock batch expired on {stock.expiry_date}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            stock.quantity_on_hand = models.F('quantity_on_hand') - quantity
            stock.last_issued_date = tz.now().date()
            stock.save(update_fields=['quantity_on_hand', 'last_issued_date'])

    if not stock:
        return Response(
            {'error': 'No matching stock found for this medication in the selected store'},
            status=status.HTTP_400_BAD_REQUEST
        )

    StockMovement.objects.create(
        item=stock.item,
        store=stock.store,
        movement_type='dispensed',
        quantity=quantity,
        unit_cost=stock.unit_cost,
        total_cost=quantity * stock.unit_cost if stock.unit_cost else None,
        batch_lot_number=stock.batch_lot_number,
        expiry_date=stock.expiry_date,
        reference_type='prescription_item',
        reference_id=item.id,
        performed_by=request.user if request.user.is_authenticated else None
    )

    dispensing = MedicationDispensing.objects.create(
        prescription_item=item,
        medication=item.medication,
        patient=item.prescription.patient,
        quantity_dispensed=quantity,
        batch_lot_number=stock.batch_lot_number,
        expiry_date=stock.expiry_date,
        unit_cost=stock.unit_cost,
        total_cost=quantity * stock.unit_cost if stock.unit_cost else None,
        inventory_stock=stock,
        dispensed_by=request.user if request.user.is_authenticated else None
    )

    from audit.utils import log_audit
    log_audit('pharmacy', 'medication_dispensings', dispensing.id, 'CREATE',
              new_values={
                  'medication': str(item.medication),
                  'patient': str(item.prescription.patient),
                  'quantity': str(quantity),
                  'batch': stock.batch_lot_number,
              },
              request=request)

    item.quantity_dispensed += quantity
    if item.quantity_dispensed >= item.quantity_prescribed:
        item.status = 'completed'
    item.save()

    response_data = MedicationDispensingSerializer(dispensing).data

    if allergy_warnings:
        response_data['allergy_warnings'] = allergy_warnings
    if interaction_warnings:
        response_data['interaction_warnings'] = interaction_warnings

    if stock.item and stock.item.reorder_level > 0:
        stock.refresh_from_db()
        if stock.quantity_on_hand <= stock.item.reorder_level:
            response_data['low_stock_warning'] = {
                'item_name': stock.item.name,
                'item_code': stock.item.code,
                'store_name': stock.store.name,
                'current_stock': str(stock.quantity_on_hand),
                'reorder_level': stock.item.reorder_level,
                'message': f'Low stock alert: {stock.item.name} has {stock.quantity_on_hand} units remaining (reorder level: {stock.item.reorder_level})'
            }

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([make_permission_class('RX_VIEW')])
def dispensing_summary(request):
    from django.db.models import Sum, Count
    from datetime import date

    try:
        year = int(request.query_params.get('year', date.today().year))
        month = int(request.query_params.get('month', date.today().month))
    except (TypeError, ValueError):
        return Response({'error': 'year and month must be valid integers'}, status=status.HTTP_400_BAD_REQUEST)

    if month < 1 or month > 12:
        return Response({'error': 'month must be 1-12'}, status=status.HTTP_400_BAD_REQUEST)

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    dispensings = MedicationDispensing.objects.filter(
        dispensed_at__gte=start_date, dispensed_at__lt=end_date
    )

    total_dispensed = dispensings.count()
    total_units = dispensings.aggregate(total=Sum('quantity_dispensed'))['total'] or 0
    total_cost = dispensings.aggregate(total=Sum('total_cost'))['total'] or 0
    by_medication = list(
        dispensings.values('medication__name')
        .annotate(count=Count('id'), units=Sum('quantity_dispensed'))
        .order_by('-count')[:20]
    )

    return Response({
        'period': f'{year}-{month:02d}',
        'total_dispensings': total_dispensed,
        'total_units_dispensed': total_units,
        'total_cost': str(total_cost),
        'top_medications': by_medication,
    })


@api_view(['GET'])
@permission_classes([make_permission_class('RX_VIEW')])
def prescription_summary(request):
    from django.db.models import Count, Q
    from datetime import date

    try:
        year = int(request.query_params.get('year', date.today().year))
        month = int(request.query_params.get('month', date.today().month))
    except (TypeError, ValueError):
        return Response({'error': 'year and month must be valid integers'}, status=status.HTTP_400_BAD_REQUEST)

    if month < 1 or month > 12:
        return Response({'error': 'month must be 1-12'}, status=status.HTTP_400_BAD_REQUEST)

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    prescriptions = Prescription.objects.filter(
        prescribed_at__gte=start_date, prescribed_at__lt=end_date
    )

    return Response({
        'period': f'{year}-{month:02d}',
        'total_prescriptions': prescriptions.count(),
        'pending': prescriptions.filter(status='pending').count(),
        'completed': prescriptions.filter(status='completed').count(),
    })
