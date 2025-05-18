from django import forms
from django.forms import modelformset_factory
from .models import MembershipPayment, BankDetail, MobileBankingDetail, CommitteeDonation, DonationType

# Form for BankDetail
class BankDetailForm(forms.ModelForm):
    class Meta:
        model = BankDetail
        fields = ['bank_name', 'branch_name', 'account_type', 'account_number', 'routing_number', 'contact_number', 'email_address']

    def __init__(self, *args, **kwargs):
        super(BankDetailForm, self).__init__(*args, **kwargs)

        self.fields['bank_name'].widget.attrs.update({'class':'form-control'})
        self.fields['branch_name'].widget.attrs.update({'class':'form-control'})
        self.fields['account_type'].widget.attrs.update({'class':'form-control'})
        self.fields['account_number'].widget.attrs.update({'class':'form-control'})
        self.fields['routing_number'].widget.attrs.update({'class':'form-control'})
        self.fields['contact_number'].widget.attrs.update({'class':'form-control'})
        self.fields['email_address'].widget.attrs.update({'class':'form-control'})

# Form for MobileBankingDetail
class MobileBankingDetailForm(forms.ModelForm):
    class Meta:
        model = MobileBankingDetail
        fields = ['mobile_banking_id', 'banking_name', 'mobile_number', 'personal_account', 'merchant_account']

    def __init__(self, *args, **kwargs):
        super(MobileBankingDetailForm, self).__init__(*args, **kwargs)

        self.fields['banking_name'].widget.attrs.update({'class':'form-control'})
        self.fields['mobile_banking_id'].widget.attrs.update({'class':'form-control'})
        self.fields['mobile_number'].widget.attrs.update({'class':'form-control'})
        

# Create formsets with an "extra=1" to allow adding one initial form dynamically.
BankDetailFormSet = modelformset_factory(BankDetail, form=BankDetailForm, extra=1)
MobileBankingDetailFormSet = modelformset_factory(MobileBankingDetail, form=MobileBankingDetailForm, extra=1)

class MembershipPaymentForm(forms.ModelForm):
    class Meta:
        model = MembershipPayment
        fields = ['payment_method', 'transaction_id', 'proof_of_payment', 'payment_notes', 'bank_details', 'mobile_banking_details']
        
    # Dynamically show the relevant payment method options
    payment_method = forms.ChoiceField(choices=[('BANK_TRANSFER', 'Bank Transfer'), ('MOBILE_BANKING', 'Mobile Banking')])
    transaction_id = forms.CharField(max_length=50, required=False)
    proof_of_payment = forms.ImageField(required=False)
    payment_notes = forms.CharField(widget=forms.Textarea, required=False)
    bank_details = forms.ModelChoiceField(queryset=BankDetail.objects.all(), empty_label="Select Bank")
    mobile_banking_details = forms.ModelChoiceField(queryset=MobileBankingDetail.objects.all(), empty_label="Select Mobile Banking", required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_method'].widget.attrs.update({'class': 'form-control'})
        self.fields['transaction_id'].widget.attrs.update({'class': 'form-control'})
        self.fields['proof_of_payment'].widget.attrs.update({'class': 'form-control'})
        self.fields['payment_notes'].widget.attrs.update({'class': 'form-control'})
        self.fields['bank_details'].widget.attrs.update({'class': 'form-control'})
        self.fields['mobile_banking_details'].widget.attrs.update({'class': 'form-control'})

    def clean_amount(self):
        # Calculate amount based on the selected fee structure
        fee_structure = self.instance.fee_structure
        if fee_structure:
            return fee_structure.amount
        return 0.00

class DateRangeForm(forms.Form):
    start_date = forms.DateField(widget=forms.SelectDateWidget())
    end_date = forms.DateField(widget=forms.SelectDateWidget())


class CommitteeDonationForm(forms.ModelForm):
    class Meta:
        model = CommitteeDonation
        exclude = ['committee', 'donor', 'is_member', 'status']

        widgets = {
            'donation_date': forms.DateInput(attrs={'type': 'date'}),
        }

    bank_detail = forms.ModelChoiceField(queryset=BankDetail.objects.all(), required=False)
    mobile_banking_detail = forms.ModelChoiceField(queryset=MobileBankingDetail.objects.all(), required=False)
        

class CommitteeDonationForm(forms.ModelForm):
    class Meta:
        model = CommitteeDonation
        exclude = ['committee', 'is_member', 'donor', 'status']
        widgets = {
            'donation_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'donation_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.committee = kwargs.pop('committee', None)
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Add form-control class to all fields
        for field_name, field in self.fields.items():
            if field_name != 'proof_of_payment':
                field.widget.attrs['class'] = 'form-control'
        
        # Handle authenticated users
        if self.request and self.request.user.is_authenticated:
            user = self.request.user
            self.fields['name'].initial = user.full_name
            self.fields['email'].initial = user.email
            self.fields['phone'].initial = user.phone_number
            if hasattr(user, 'profile'):
                self.fields['address'].initial = user.profile.present_address
            
            # Hide donor info fields
            for field in ['name', 'email', 'phone', 'address']:
                self.fields[field].widget = forms.HiddenInput()
        
        # Initialize field visibility based on donation type
        if self.instance.pk and self.instance.donation_type:
            self.update_fields_based_on_type(self.instance.donation_type)
        
        # Hide all payment fields by default
        self.hide_all_payment_fields()
    
    def hide_all_payment_fields(self):
        payment_fields = [
            'payment_method', 'bank_detail', 
            'mobile_banking_detail', 'transaction_id',
            'proof_of_payment'
        ]
        for field in payment_fields:
            self.fields[field].required = False
            self.fields[field].widget.attrs['style'] = 'display:none;'
    
    def update_fields_based_on_type(self, donation_type):
        """Update field requirements based on donation type"""
        # Donation fields
        self.fields['amount'].required = donation_type.amount
        self.fields['quantity'].required = donation_type.quantity
        self.fields['quantity_unit'].required = donation_type.quantity_unit
        
        # Payment fields
        show_payment = any([
            donation_type.bank_detail,
            donation_type.mobile_banking_detail,
            donation_type.payment_method,
            donation_type.transaction_id,
            donation_type.proof_of_payment
        ])
        
        if show_payment:
            self.fields['payment_method'].required = donation_type.payment_method
            self.fields['bank_detail'].required = donation_type.bank_detail
            self.fields['mobile_banking_detail'].required = donation_type.mobile_banking_detail
            self.fields['transaction_id'].required = donation_type.transaction_id
            self.fields['proof_of_payment'].required = donation_type.proof_of_payment

class DonationTypeForm(forms.ModelForm):
    class Meta:
        model = DonationType
        fields = ['name', 'description', 'unit_of_measure', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Donation Type Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'unit_of_measure': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unit of Measure'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }