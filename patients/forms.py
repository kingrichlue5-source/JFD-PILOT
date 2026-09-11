from django import forms
from .models import Patient


class PatientRegistrationForm(forms.ModelForm):
    visit_type = forms.ChoiceField(
        choices=[('opd', 'OPD'), ('er', 'Emergency'), ('pediatric', 'Pediatric'), ('obgyn', 'OBGYN'), ('surgery', 'Surgery')],
        initial='opd',
        widget=forms.Select(attrs={'class': 'input-field'})
    )
    chief_complaint = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'input-field', 'rows': 2, 'placeholder': 'Chief complaint...'})
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'input-field', 'accept': 'image/*', 'capture': 'user', 'id': 'photo-input'})
    )

    class Meta:
        model = Patient
        fields = [
            'first_name', 'middle_name', 'last_name', 'date_of_birth', 'gender',
            'blood_type', 'marital_status', 'phone', 'email',
            'address_line1', 'city', 'country',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship',
            'payer_category', 'insurance_provider', 'insurance_policy_number',
            'photo',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'First name'}),
            'middle_name': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Middle name (optional)'}),
            'last_name': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Last name'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'input-field', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'input-field'}, choices=[('', 'Select...'), ('M', 'Male'), ('F', 'Female')]),
            'blood_type': forms.Select(attrs={'class': 'input-field'}),
            'marital_status': forms.Select(attrs={'class': 'input-field'}),
            'phone': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Phone number'}),
            'email': forms.EmailInput(attrs={'class': 'input-field', 'placeholder': 'Email (optional)'}),
            'address_line1': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Address'}),
            'city': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'City'}),
            'country': forms.TextInput(attrs={'class': 'input-field', 'id': 'country-select', 'list': 'country-list', 'placeholder': 'Type to search country...', 'value': 'Liberia'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Emergency contact name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Emergency contact phone'}),
            'emergency_contact_relationship': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Relationship'}),
            'payer_category': forms.Select(attrs={'class': 'input-field'}, choices=[
                ('', 'Select payer...'),
                ('Private Cash', 'Private Cash'),
                ('Insurance', 'Insurance'),
                ('Government', 'Government'),
                ('Maternal Free Care', 'Maternal Free Care'),
                ('Emergency Care', 'Emergency Care'),
            ]),
            'insurance_provider': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Insurance provider'}),
            'insurance_policy_number': forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Policy number'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        first_name = cleaned_data.get('first_name', '').strip().lower()
        last_name = cleaned_data.get('last_name', '').strip().lower()
        dob = cleaned_data.get('date_of_birth')
        phone = cleaned_data.get('phone', '').strip()

        if first_name and last_name and dob:
            matches = Patient.objects.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
                date_of_birth=dob
            )
            if matches.exists():
                existing = matches.first()
                self.add_error(None, f'Potential duplicate found: {existing.mrn} - {existing.first_name} {existing.last_name} (DOB: {existing.date_of_birth}). Please verify before registering.')

        elif phone and len(phone) >= 7:
            matches = Patient.objects.filter(phone=phone)
            if matches.exists():
                existing = matches.first()
                self.add_error(None, f'Potential duplicate found: {existing.mrn} - {existing.first_name} {existing.last_name} (Phone: {existing.phone}). Please verify before registering.')

        return cleaned_data


class VisitForm(forms.Form):
    visit_type = forms.ChoiceField(
        choices=[('opd', 'OPD'), ('er', 'Emergency'), ('pediatric', 'Pediatric'), ('obgyn', 'OBGYN'), ('surgery', 'Surgery'), ('ipd', 'IPD')],
        widget=forms.Select(attrs={'class': 'input-field'})
    )
    chief_complaint = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'input-field', 'rows': 3, 'placeholder': 'Describe the chief complaint...'})
    )
