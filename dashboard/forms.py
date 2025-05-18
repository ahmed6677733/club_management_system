from django import forms
from club.models import CommitteeExpense
from payment.models import CommitteeDonation, MembershipPayment, BankDetail, MobileBankingDetail
from django.contrib.auth import get_user_model
from accounts.models import FamilyMember, Profile, MembershipType, User, FeeStructure
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

class CommitteeExpenseFormDashboard(forms.ModelForm):
    class Meta:
        model = CommitteeExpense
        fields = '__all__'
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank_detail'].required = False
        self.fields['mobile_banking_detail'].required = False

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


User = get_user_model()

class CommitteeDonationFormDashboard(forms.ModelForm):
    class Meta:
        model = CommitteeDonation
        exclude = ['created_by', 'updated_by', 'created_at', 'updated_at']
        widgets = {
            'donation_date': forms.DateInput(attrs={'type': 'date'}),
            'donation_notes': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make non-essential fields not required
        optional_fields = ['donor', 'name', 'email', 'phone', 'address',
                         'bank_detail', 'mobile_banking_detail', 'quantity',
                         'quantity_unit', 'transaction_id', 'proof_of_payment']
        for field in optional_fields:
            if field in self.fields:
                self.fields[field].required = False
        
        # Customize donor queryset
        if 'donor' in self.fields:
            self.fields['donor'].queryset = User.objects.all().order_by('first_name')
            
        # Set date format
        self.fields['donation_date'].widget.format = '%Y-%m-%d'



class DashboardFamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = ['relationship', 'age', 'is_nominee', 'percentage', 'primary_member']
        widgets = {
            'is_nominee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'primary_member': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(DashboardFamilyMemberForm, self).__init__(*args, **kwargs)
        # Filter the primary member queryset to show eligible members
        self.fields['primary_member'].queryset = Profile.objects.filter(
            user__role__in=['Member', 'Admin']
        ).select_related('user')
        
        for name, field in self.fields.items():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})


class AdminMembershipPaymentForm(forms.ModelForm):
    MONTH_CHOICES = [
        ('January', 'January'),
        ('February', 'February'),
        ('March', 'March'),
        ('April', 'April'),
        ('May', 'May'),
        ('June', 'June'),
        ('July', 'July'),
        ('August', 'August'),
        ('September', 'September'),
        ('October', 'October'),
        ('November', 'November'),
        ('December', 'December'),
    ]
    
    YEAR_CHOICES = [
        (str(year), str(year)) for year in range(timezone.now().year - 4, timezone.now().year + 2)
    ]

    profile = forms.ModelChoiceField(
        queryset=Profile.objects.select_related('user'),
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Select member...',
            'id': 'id_profile'
        })
    )
    
    payment_months = forms.MultipleChoiceField(
        choices=MONTH_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    payment_year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        initial=str(timezone.now().year),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = MembershipPayment
        fields = [
            'profile',
            'membership_type',
            'fee_structure',
            'payment_method',
            'bank_details',
            'mobile_banking_details',
            'transaction_id',
            'proof_of_payment',
            'amount',
            'payment_months',
            'payment_year',
            'payment_notes',
            'status'
        ]
        widgets = {
            'amount': forms.HiddenInput(),
            'membership_type': forms.Select(attrs={'class': 'form-control'}),
            'fee_structure': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'transaction_id': forms.TextInput(attrs={'class': 'form-control'}),
            'proof_of_payment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'payment_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['membership_type'].queryset = MembershipType.objects.filter(status=True)
        
        if 'membership_type' in self.initial:
            self.fields['fee_structure'].queryset = FeeStructure.objects.filter(
                membership=self.initial['membership_type'],
                is_active=True
            )
        else:
            self.fields['fee_structure'].queryset = FeeStructure.objects.none()
        
        self.fields['status'].initial = 'COMPLETED'

    def clean(self):
        cleaned_data = super().clean()
        fee_structure = cleaned_data.get('fee_structure')
        payment_months = cleaned_data.get('payment_months')
        payment_year = cleaned_data.get('payment_year')
        
        if fee_structure:
            if fee_structure.is_one_time:
                cleaned_data['amount'] = fee_structure.amount
                cleaned_data['payment_months'] = None
            else:
                if not payment_months:
                    self.add_error('payment_months', 'Please select at least one month')
                if not payment_year:
                    self.add_error('payment_year', 'Please select a year')
                
                if payment_months and payment_year:
                    months_with_year = [
                        f"{month} {payment_year}" 
                        for month in payment_months
                    ]
                    cleaned_data['payment_months'] = ", ".join(months_with_year)
                    month_count = len(payment_months)
                    cleaned_data['amount'] = fee_structure.amount * month_count
        
        return cleaned_data