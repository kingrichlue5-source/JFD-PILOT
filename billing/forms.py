from django import forms


class PaymentForm(forms.Form):
    invoice_id = forms.UUIDField(widget=forms.HiddenInput)
    payment_method = forms.ChoiceField(choices=[
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('insurance', 'Insurance'),
        ('credit', 'Credit'),
    ], widget=forms.Select(attrs={'class': 'input-field'}))
    amount = forms.DecimalField(max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'input-field', 'placeholder': 'Amount'}))
    reference_number = forms.CharField(required=False, max_length=100, widget=forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Reference #'}))

    def process(self, user=None):
        from .models import Invoice, Payment, CashierShift
        from .services import recalculate_invoice_totals, generate_receipt_number
        from django.utils import timezone

        invoice = Invoice.objects.get(id=self.cleaned_data['invoice_id'], is_deleted=False)
        amount = self.cleaned_data['amount']
        method = self.cleaned_data['payment_method']
        ref = self.cleaned_data.get('reference_number', '') or f'POS-{timezone.now().timestamp()}'

        shift = CashierShift.objects.filter(status='open', cashier=user).first() if user else None

        receipt_number = generate_receipt_number()
        payment = Payment.objects.create(
            invoice=invoice,
            patient=invoice.patient,
            amount=amount,
            payment_method=method,
            reference_number=ref,
            receipt_number=receipt_number,
            received_by=user if user and user.is_authenticated else None,
            cashier_shift=shift
        )

        recalculate_invoice_totals(invoice)

        return payment


class WaiveForm(forms.Form):
    invoice_id = forms.UUIDField(widget=forms.HiddenInput)
    reason = forms.CharField(required=False, max_length=255, widget=forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Reason for waiver'}))

    def process(self, user=None):
        from .models import Invoice, Payment
        from .services import generate_receipt_number
        from django.utils import timezone

        invoice = Invoice.objects.get(id=self.cleaned_data['invoice_id'], is_deleted=False)
        reason = self.cleaned_data.get('reason', 'Government Free Care')

        payment = Payment.objects.create(
            invoice=invoice,
            patient=invoice.patient,
            amount=0,
            payment_method='waiver',
            reference_number=reason,
            receipt_number=generate_receipt_number(),
            received_by=user if user and user.is_authenticated else None
        )

        invoice.status = 'waived'
        invoice.save()

        return payment


class CashierShiftForm(forms.Form):
    starting_float = forms.DecimalField(max_digits=12, decimal_places=2, initial=10000, widget=forms.NumberInput(attrs={'class': 'input-field'}))
    terminal_id = forms.CharField(max_length=50, initial='POS-01', widget=forms.TextInput(attrs={'class': 'input-field'}))

    def process(self, user=None):
        from .models import CashierShift
        from django.utils import timezone

        shift = CashierShift.objects.create(
            cashier=user if user and user.is_authenticated else None,
            opening_balance=self.cleaned_data['starting_float'],
            status='open',
            shift_start=timezone.now()
        )
        return shift
