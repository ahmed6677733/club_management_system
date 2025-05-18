from django import forms
from django.forms import inlineformset_factory
from django.forms import modelformset_factory
from accounts.models import User, Team
from django.forms import CheckboxSelectMultiple
from .models import CommitteeTaskAssignment, Club, OrganizationRegistrationInfo, Committee, CommitteeTask, CommitteeMember, CommitteeExpense, ExpenseType, Designation, Activity, CommitteePermission
#from .models import Activity

class ClubForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ['club_name', 'description', 'club_est', 'club_logo', 'contact_name', 'contact_email', 'contact_phone']

    def __init__(self, *args, **kwargs):
        super(ClubForm, self).__init__(*args, **kwargs)

        self.fields['club_est'].widget = forms.DateInput(attrs={
            'class': 'form-control datepicker',  # Apply Bootstrap classes and a specific class for JS
            'type': 'text',  # We'll initialize the picker with JS
        })
        self.fields['club_name'].widget.attrs.update({'class':'form-control'})
        self.fields['description'].widget.attrs.update({'class':'form-control'})
        self.fields['club_logo'].widget.attrs.update({'class':'form-control'})
        self.fields['contact_name'].widget.attrs.update({'class':'form-control'})
        self.fields['contact_email'].widget.attrs.update({'class':'form-control'})
        self.fields['contact_phone'].widget.attrs.update({'class':'form-control'})

class OrganizationRegistrationForm(forms.ModelForm):
    class Meta:
        model = OrganizationRegistrationInfo
        fields = [
            'registration_number', 'organization_name', 'upload_file',
            'licence_name', 'registration_status', 'license_number',
            'license_expiry_date', 'registration_notes'
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        # Set HTML5 date input type for expiry date
        self.fields['license_expiry_date'].widget = forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        )

# Create a FormSet to handle multiple organization registrations
OrganizationRegistrationFormSet = modelformset_factory(
    OrganizationRegistrationInfo,
    form=OrganizationRegistrationForm,
    extra=1,  # Number of empty forms to display initially
    can_delete=True  # Allow deletion of forms
)
        
class CommitteeForm(forms.ModelForm):
    class Meta:
        model = Committee
        fields = ['name', 'description', 'start_date', 'end_date']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter committee name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class CommitteeMemberForm(forms.ModelForm):
    class Meta:
        model = CommitteeMember
        fields = ['member', 'designation', 'activities', 'is_active']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select select2'}),
            'designation': forms.Select(attrs={'class': 'form-select select2'}),
            'activities': forms.SelectMultiple(attrs={'class': 'form-select select2-multiple', 'data-activities': True}),
        }
    

CommitteeMemberFormSet = inlineformset_factory(
    Committee,
    CommitteeMember,
    form=CommitteeMemberForm,
    extra=1,  # Set to 1 for one empty form by default
    can_delete=True  # Allow deletion of committee members
)

class CommitteeTaskForm(forms.ModelForm):
    class Meta:
        model = CommitteeTask
        fields = ['committee', 'title', 'description', 'deadline', 'status']

class CommitteeTaskAssignmentForm(forms.ModelForm):
    volunteer = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(role="Volunteer"),  # Fetch only volunteers
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )
    team = forms.ModelMultipleChoiceField(
        queryset=Team.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CommitteeTaskAssignment
        fields = ['volunteer', 'team', 'due_date', 'status']

class CommitteeExpenseForm(forms.ModelForm):
    class Meta:
        model = CommitteeExpense
        fields = '__all__'
        exclude = ['committee', 'members']  # Exclude committee and members fields

        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['bank_detail'].required = False
        self.fields['mobile_banking_detail'].required = False

        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'


class ExpenseTypeForm(forms.ModelForm):
    class Meta:
        model = ExpenseType
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter expense type name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
        }

class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designation
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter designation name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
        }

# class ActivityForm(forms.ModelForm):
#     class Meta:
#         model = Activity
#         fields = ['name', 'description']
#         widgets = {
#             'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter activity name'}),
#             'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter description'}),
#         }


class CommitteePermissionForm(forms.ModelForm):
    class Meta:
        model = CommitteePermission
        fields = ['committee', 'member', 'can_approve_expense', 'can_reject_expense', 'can_approve_donation', 'can_reject_donation']
        widgets = {
            'committee': forms.Select(attrs={'class': 'form-control'}),
            'member': forms.Select(attrs={'class': 'form-control'}),
            'can_approve_expense': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_reject_expense': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_approve_donation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_reject_donation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        