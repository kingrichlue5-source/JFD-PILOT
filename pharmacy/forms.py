from django import forms
from django.db import models


class DispensingForm(forms.Form):
    prescription_item = forms.UUIDField(widget=forms.HiddenInput)
    medication = forms.UUIDField(widget=forms.HiddenInput)
    quantity_dispensed = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'Qty'}))
    batch_lot_number = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Batch number'}))

    def check_allergies(self):
        from patients.models import PatientAllergy
        from .models import PrescriptionItem, DrugInteraction

        item = PrescriptionItem.objects.get(id=self.cleaned_data['prescription_item'])
        patient = item.prescription.patient
        medication = item.medication

        warnings = []
        allergies = PatientAllergy.objects.filter(patient=patient, status='active')
        med_name = (medication.name or '').lower()
        med_generic = (medication.generic_name or '').lower()
        for allergy in allergies:
            allergen = (allergy.allergen or '').lower()
            if allergen in med_name or allergen in med_generic or med_name in allergen or med_generic in allergen:
                warnings.append({
                    'type': 'allergy',
                    'allergen': allergy.allergen,
                    'severity': allergy.severity,
                    'reaction': allergy.reaction or 'Not specified',
                    'message': f'Patient allergic to {allergy.allergen}. {medication.name} may be contraindicated.',
                })

        other_meds = PrescriptionItem.objects.filter(
            prescription__patient=patient, status='completed'
        ).exclude(id=item.id).values_list('medication_id', flat=True)
        if other_meds:
            interactions = DrugInteraction.objects.filter(
                models.Q(drug_a=medication, drug_b_id__in=other_meds) |
                models.Q(drug_b=medication, drug_a_id__in=other_meds),
                is_active=True
            )
            for ix in interactions:
                warnings.append({
                    'type': 'interaction',
                    'drug_a': ix.drug_a.name,
                    'drug_b': ix.drug_b.name,
                    'severity': ix.severity,
                    'description': ix.description,
                    'recommendation': ix.recommendation or '',
                })

        return warnings

    def process(self, user=None):
        from .models import PrescriptionItem, MedicationDispensing
        from inventory.models import Stock, StockMovement
        from django.utils import timezone as tz

        item = PrescriptionItem.objects.get(id=self.cleaned_data['prescription_item'])
        quantity = self.cleaned_data['quantity_dispensed']
        batch = self.cleaned_data['batch_lot_number']

        stock = Stock.objects.filter(
            batch_lot_number=batch,
            quantity_on_hand__gte=quantity,
        ).first()

        if not stock:
            raise ValueError(f'No stock found for batch {batch} with sufficient quantity')

        if stock.expiry_date and stock.expiry_date < tz.now().date():
            raise ValueError(f'Stock batch expired on {stock.expiry_date}')

        from django.db.models import F
        stock.quantity_on_hand = F('quantity_on_hand') - quantity
        stock.last_issued_date = tz.now().date()
        stock.save(update_fields=['quantity_on_hand', 'last_issued_date'])

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
            performed_by=user if user and user.is_authenticated else None
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
            dispensed_by=user if user and user.is_authenticated else None
        )

        item.quantity_dispensed += quantity
        if item.quantity_dispensed >= item.quantity_prescribed:
            item.status = 'completed'
        item.save()

        rx = item.prescription
        all_items = PrescriptionItem.objects.filter(prescription=rx)
        if all(i.status == 'completed' for i in all_items):
            rx.status = 'completed'
            rx.save()

        return dispensing
