from django import forms
from django.utils import timezone
from .models import TriageRecord, Visit, Encounter, Diagnosis, Order, ProgressNote


class TriageForm(forms.Form):
    visit_id = forms.UUIDField(widget=forms.HiddenInput)
    chief_complaint = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'class': 'input-field', 'placeholder': 'Chief complaint...'}))
    acuity_level = forms.IntegerField(min_value=1, max_value=5, initial=3)
    temperature = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'input-field', 'step': '0.1', 'placeholder': '37.0'}))
    heart_rate = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'input-field', 'placeholder': '72'}))
    respiratory_rate = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'input-field', 'placeholder': '18'}))
    blood_pressure_systolic = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'input-field', 'placeholder': '120'}))
    blood_pressure_diastolic = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'input-field', 'placeholder': '80'}))
    oxygen_saturation = forms.DecimalField(required=False, widget=forms.NumberInput(attrs={'class': 'input-field', 'step': '0.1', 'placeholder': '98'}))
    screening_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2, 'class': 'input-field', 'placeholder': 'Additional notes...'}))

    def process(self, user=None):
        visit = Visit.objects.get(id=self.cleaned_data['visit_id'], is_deleted=False)
        triage_record = TriageRecord.objects.create(
            visit=visit,
            patient=visit.patient,
            chief_complaint=self.cleaned_data['chief_complaint'],
            acuity_level=self.cleaned_data['acuity_level'],
            temperature=self.cleaned_data.get('temperature'),
            heart_rate=self.cleaned_data.get('heart_rate'),
            respiratory_rate=self.cleaned_data.get('respiratory_rate'),
            blood_pressure_systolic=self.cleaned_data.get('blood_pressure_systolic'),
            blood_pressure_diastolic=self.cleaned_data.get('blood_pressure_diastolic'),
            oxygen_saturation=self.cleaned_data.get('oxygen_saturation'),
            screening_notes=self.cleaned_data.get('screening_notes', ''),
            triage_nurse=user if user and user.is_authenticated else None
        )
        visit.chief_complaint = self.cleaned_data['chief_complaint']
        visit.triage_priority = str(self.cleaned_data['acuity_level'])
        visit.triage_notes = self.cleaned_data.get('screening_notes', '')
        visit.triage_time = timezone.now()
        visit.status = 'in_progress'
        visit.save()

        from .views import route_patient
        routing = route_patient(
            acuity_level=self.cleaned_data.get('acuity_level', 5),
            chief_complaint=self.cleaned_data['chief_complaint']
        )
        from users_auth.models import Department
        try:
            dept = Department.objects.get(code=routing['department_code'])
            visit.department = dept
            visit.save()
        except Department.DoesNotExist:
            pass

        return triage_record, routing, visit


class EncounterForm(forms.Form):
    visit_id = forms.UUIDField(widget=forms.HiddenInput)
    encounter_id = forms.UUIDField(required=False, widget=forms.HiddenInput)
    subjective = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'input-field', 'placeholder': 'Patient history...'}))
    objective = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'input-field', 'placeholder': 'Examination findings...'}))
    assessment = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2, 'class': 'input-field', 'placeholder': 'Clinical assessment...'}))
    plan = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2, 'class': 'input-field', 'placeholder': 'Treatment plan...'}))
    icd_code = forms.CharField(required=False, max_length=20)
    orders_json = forms.CharField(required=False, widget=forms.HiddenInput)
    prescriptions_json = forms.CharField(required=False, widget=forms.HiddenInput)

    def process(self, user=None):
        from django.utils import timezone
        visit = Visit.objects.get(id=self.cleaned_data['visit_id'], is_deleted=False)
        encounter_id = self.cleaned_data.get('encounter_id')

        if encounter_id:
            encounter = Encounter.objects.get(id=encounter_id)
            encounter.subjective = self.cleaned_data.get('subjective', '')
            encounter.objective = self.cleaned_data.get('objective', '')
            encounter.assessment = self.cleaned_data.get('assessment', '')
            encounter.plan = self.cleaned_data.get('plan', '')
            encounter.save()
        else:
            encounter = Encounter.objects.create(
                visit=visit,
                patient=visit.patient,
                encounter_type='opd',
                subjective=self.cleaned_data.get('subjective', ''),
                objective=self.cleaned_data.get('objective', ''),
                assessment=self.cleaned_data.get('assessment', ''),
                plan=self.cleaned_data.get('plan', ''),
                provider=user if user and user.is_authenticated else None
            )

        icd_code = self.cleaned_data.get('icd_code')
        if icd_code:
            Diagnosis.objects.create(
                encounter=encounter,
                patient=visit.patient,
                visit=visit,
                diagnosis_code=icd_code,
                diagnosis_type='primary',
                diagnosis_description=icd_code
            )

        orders_json = self.cleaned_data.get('orders_json')
        if orders_json:
            import json
            from billing.services import post_order_to_invoice
            orders = json.loads(orders_json)
            for order in orders:
                order_obj = Order.objects.create(
                    visit=visit,
                    patient=visit.patient,
                    encounter=encounter,
                    order_type=order.get('type', 'lab'),
                    order_description=order.get('description', ''),
                    status='pending',
                    ordering_provider=user if user and user.is_authenticated else None
                )
                if order_obj.order_type == 'lab':
                    from clinical.models import Specimen
                    desc = (order_obj.order_description or '').lower()
                    specimen_type = 'Blood'
                    if 'urine' in desc:
                        specimen_type = 'Urine'
                    elif 'stool' in desc or 'feces' in desc:
                        specimen_type = 'Stool'
                    elif 'csf' in desc or 'spinal' in desc:
                        specimen_type = 'CSF'
                    Specimen.objects.create(
                        patient=visit.patient,
                        visit=visit,
                        order=order_obj,
                        specimen_type=specimen_type,
                        collection_datetime=timezone.now(),
                        collected_by=user if user and user.is_authenticated else None,
                        status='pending'
                    )
                try:
                    post_order_to_invoice(order_obj, visit, visit.patient)
                except Exception:
                    pass

        prescriptions_json = self.cleaned_data.get('prescriptions_json')
        if prescriptions_json:
            import json
            from pharmacy.models import Prescription, PrescriptionItem
            from billing.services import post_prescription_item_to_invoice
            rx_items = json.loads(prescriptions_json)
            if rx_items:
                prescription = Prescription.objects.create(
                    visit=visit,
                    patient=visit.patient,
                    encounter=encounter,
                    prescribed_by=user if user and user.is_authenticated else None
                )
                for item in rx_items:
                    rx_item = PrescriptionItem.objects.create(
                        prescription=prescription,
                        medication_id=item.get('medication'),
                        dosage=item.get('dosage', ''),
                        frequency=item.get('frequency', 'Daily'),
                        duration=item.get('duration', '7 days'),
                        quantity_prescribed=item.get('quantity', 1)
                    )
                    try:
                        post_prescription_item_to_invoice(rx_item, visit, visit.patient)
                    except Exception:
                        pass

        encounter.status = 'completed'
        encounter.is_finalized = True
        encounter.finalized_at = timezone.now()
        encounter.save()

        if visit.status in ['in_triage', 'in_progress']:
            visit.status = 'in_progress'
            visit.save()

        return encounter


class NurseNoteForm(forms.Form):
    visit_id = forms.UUIDField(widget=forms.HiddenInput)
    subjective = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'input-field', 'placeholder': "Patient's complaints, symptoms, concerns..."})
    )
    objective = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'input-field', 'placeholder': 'Vital signs, physical exam findings, lab results...'})
    )
    assessment = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'input-field', 'placeholder': "Nurse's clinical judgment..."})
    )
    plan = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'input-field', 'placeholder': 'Interventions, patient education, follow-up...'})
    )

    def clean(self):
        cleaned_data = super().clean()
        s = cleaned_data.get('subjective', '')
        o = cleaned_data.get('objective', '')
        a = cleaned_data.get('assessment', '')
        p = cleaned_data.get('plan', '')
        if not any([s, o, a, p]):
            raise forms.ValidationError('At least one SOAP field is required.')
        return cleaned_data

    def process(self, user=None):
        from .models import ProgressNote
        visit = Visit.objects.get(id=self.cleaned_data['visit_id'], is_deleted=False)
        encounter = Encounter.objects.filter(visit=visit).order_by('-encounter_date').first()
        if not encounter:
            encounter = Encounter.objects.create(
                visit=visit,
                patient=visit.patient,
                encounter_type=visit.visit_type if visit.visit_type in ['opd', 'ipd', 'er'] else 'ipd',
                status='in_progress',
                created_by=user.id if user else None,
            )
        s = self.cleaned_data.get('subjective', '')
        o = self.cleaned_data.get('objective', '')
        a = self.cleaned_data.get('assessment', '')
        p = self.cleaned_data.get('plan', '')
        note_text = '\n\n'.join(filter(None, [
            f"[S] {s}" if s else '',
            f"[O] {o}" if o else '',
            f"[A] {a}" if a else '',
            f"[P] {p}" if p else '',
        ]))
        note = ProgressNote.objects.create(
            encounter=encounter,
            patient=visit.patient,
            visit=visit,
            note_type='nursing',
            subjective=s or None,
            objective=o or None,
            assessment=a or None,
            plan=p or None,
            note_text=note_text,
            author=user if user and user.is_authenticated else None,
        )
        return note
