from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, FamilyMember, User, RoleChangeRequest, Team, TeamRegistration, MembershipType, FeeName, FeeStructure

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'profile_pic', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)

        self.fields['full_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Full Name'})
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Email'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Phone Number'})
        self.fields['profile_pic'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'type': 'password', 'placeholder': 'Enter your Password'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'type': 'password', 'placeholder': 'Confirm Password'})
    def save(self, commit=True):
        full_name = self.cleaned_data.get('full_name')
        username = full_name.lower().replace(" ", "_")

        # Ensure unique username
        count = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}_{count}"
            count += 1

        user = super().save(commit=False)
        user.username = username  # ✅ Fixed: Assign unique username
        if commit:
            user.save()
        return user

class UpdateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'profile_pic']

    def __init__(self, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        # Custom widget styling
        self.fields['full_name'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Full Name'})
        self.fields['email'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Email'})
        self.fields['phone_number'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Phone Number'})
        self.fields['profile_pic'].widget.attrs.update({'class': 'form-control'})


class MemberForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['present_address', 'permanent_address',
                  'nid', 'date_of_birth', 'blood_group', 'gender', 'membership_type']

    def __init__(self, *args, **kwargs):
        super(MemberForm, self).__init__(*args, **kwargs)
        self.fields['present_address'].widget.attrs.update({'class': 'form-control'})
        self.fields['permanent_address'].widget.attrs.update({'class': 'form-control'})
        self.fields['nid'].widget.attrs.update({'class': 'form-control'})
        self.fields['date_of_birth'].widget.attrs.update({'class': 'form-control'})
        self.fields['blood_group'].widget.attrs.update({'class': 'form-control'})
        self.fields['gender'].widget.attrs.update({'class': 'form-control'})
        self.fields['membership_type'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        if user and not instance.user_id:
            instance.user = user
        if commit:
            instance.save()
        return instance
    
class UpdateMemberForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['father_name', 'mother_name', 'present_address', 'permanent_address',
                  'nid', 'date_of_birth', 'blood_group', 'gender', 'membership_type']

    def __init__(self, *args, **kwargs):
        super(UpdateMemberForm, self).__init__(*args, **kwargs)
        # Custom widget styling
        self.fields['father_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['mother_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['present_address'].widget.attrs.update({'class': 'form-control'})
        self.fields['permanent_address'].widget.attrs.update({'class': 'form-control'})
        self.fields['nid'].widget.attrs.update({'class': 'form-control'})
        self.fields['date_of_birth'].widget.attrs.update({'class': 'form-control'})
        self.fields['blood_group'].widget.attrs.update({'class': 'form-control'})
        self.fields['gender'].widget.attrs.update({'class': 'form-control'})
        self.fields['membership_type'].widget.attrs.update({'class': 'form-control'})


class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        exclude = ['membership_id', 'user', 'existing_member', 'is_existing_member']
        widgets = {
            'is_nominee': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super(FamilyMemberForm, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})



class RoleChangeRequestForm(forms.ModelForm):
    class Meta:
        model = RoleChangeRequest
        fields = ['new_role', 'reason_for_change']

    def __init__(self, *args, **kwargs):
        super(RoleChangeRequestForm, self).__init__(*args, **kwargs)
        # Custom widget styling
        self.fields['new_role'].widget.attrs.update({'class': 'form-control'})
        self.fields['reason_for_change'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Enter Reason for Role Change'})

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name', 'description', 'is_active']

class TeamRegistrationForm(forms.ModelForm):
    class Meta:
        model = TeamRegistration
        fields = ['volunteer', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter to show only users with role 'Volunteer'
        self.fields['volunteer'].queryset = User.objects.filter(role="Volunteer")

# Formset to handle multiple registrations at once
TeamRegistrationFormSet = inlineformset_factory(
    Team, TeamRegistration, form=TeamRegistrationForm, extra=1, can_delete=True
)


class MembershipTypeForm(forms.ModelForm):
    class Meta:
        model = MembershipType
        fields = ['mmtcode', 'name', 'description', 'status']
        widgets = {
            'mmtcode': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'status': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class FeeNameForm(forms.ModelForm):
    class Meta:
        model = FeeName
        fields = ['name']

        widgets = {
            'name': forms.DateInput(attrs={'class': 'form-control'}),
        }

class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['fee_name', 'start_date', 'end_date', 'amount', 'counter', 'is_one_time', 'is_active']
        widgets = {
            'membership': forms.Select(attrs={'class': 'form-control'}),
            'fee_name': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'counter': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_one_time': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

FeeStructureFormSet = inlineformset_factory(
    MembershipType, FeeStructure, form=FeeStructureForm, extra=1, can_delete=True
)