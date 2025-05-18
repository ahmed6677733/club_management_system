from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from uuid import uuid4
from django.db import transaction

class User(AbstractUser):
    SELECT = 'Select'
    ADMIN = 'Admin'
    MEMBER = 'Member'
    VOLUNTEER = 'Volunteer'

    ROLE_CHOICES = [
        (SELECT, 'Select'),
        (ADMIN, 'Administrator'),
        (MEMBER, 'Member'),
        (VOLUNTEER, 'Volunteer'),
    ]

    full_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=11, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='default/profile-default.jpg')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=MEMBER)

    is_email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid4, editable=False, null=True)

    def __str__(self):
        return self.username
    
class MembershipType(models.Model):
    mmtcode = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    status = models.BooleanField()

    def __str__(self):
        return f"{self.name}"

class FeeName(models.Model):
    name = models.CharField(max_length=200, unique=True)
    def __str__(self):
        return f"{self.name}"

    
class FeeStructure(models.Model):
    membership = models.ForeignKey(MembershipType, on_delete=models.CASCADE, null=True, blank=True)
    fee_name = models.ForeignKey(FeeName, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True)  # Monthly/annual fee
    counter = models.IntegerField(default=1)
    is_one_time = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.fee_name}"

class Profile(models.Model):
    GENDER = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('others', 'Others'),
    ]
    BLOODGROUP = [
        ('a+', 'A+'),
        ('a-', 'A-'),
        ('b+', 'B+'),
        ('b-', 'B-'),
        ('ab+', 'AB+'),
        ('ab-', 'AB-'),
        ('o+', 'O+'),
        ('o-', 'O-'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    father_name = models.CharField(max_length=255, blank=True, null=True)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    present_address = models.TextField(blank=True, null=True)
    permanent_address = models.TextField(blank=True, null=True)
    nid = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    blood_group = models.CharField(max_length=10, blank=True, null=True, choices=BLOODGROUP)
    gender = models.CharField(max_length=10, choices=GENDER, blank=True, null=True)
    membership_id = models.CharField(max_length=12, unique=True, blank=True, null=True, editable=False)
    joining_date = models.DateField(default=timezone.now)
    is_approved = models.BooleanField(default=False)
    membership_type = models.OneToOneField(MembershipType, null=True, blank=True, on_delete=models.SET_NULL)
    

    def save(self, *args, **kwargs):
        if not self.membership_id:
            self.membership_id = self.generate_membership_id()
        super().save(*args, **kwargs)

    def generate_membership_id(self):
        """Generate a unique membership ID based on the user's role."""
        role_prefix = {
            'Member': '101',
            'Volunteer': '102',
            'Admin': '103'
        }

        prefix = role_prefix.get(self.user.role, '101')  # Default to '101' if role is not found
        last_member = Profile.objects.filter(user__role=self.user.role).order_by('-joining_date').first()
        next_number = last_member.id + 1 if last_member else 1  # ✅ Fixed: Avoid gaps in IDs

        membership_id = f"{prefix}-{str(next_number).zfill(6)}"

        # Check if the generated membership_id already exists, and if it does, increment the number
        while Profile.objects.filter(membership_id=membership_id).exists():
            next_number += 1
            membership_id = f"{prefix}-{str(next_number).zfill(6)}"

        return membership_id

    def __str__(self):
        return f"Profile {self.user.username}"
    
class RoleChangeRequest(models.Model):
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]

    ROLE_CHOICES = [
        (User.ADMIN, 'Administrator'),
        (User.MEMBER, 'Member'),
        (User.VOLUNTEER, 'Volunteer'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="role_change_requests")
    requested_on = models.DateTimeField(auto_now_add=True)
    new_role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    reason_for_change = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)

    def __str__(self):
        return f"Role Change Request for {self.user.username} - {self.status}"

    def approve(self):
        """Approve the request and update the user's role and membership ID."""
        if self.status != self.APPROVED:
            self.status = self.APPROVED
            self.save()

            # Update user's role
            self.user.role = self.new_role
            self.user.save()

            # Update profile's role and regenerate membership ID
            profile = self.user.profile
            profile.role = self.new_role
            profile.membership_id = profile.generate_membership_id()  # Regenerate the membership ID
            profile.save()

    def reject(self):
        """Reject the role change request."""
        if self.status != self.REJECTED:
            self.status = self.REJECTED
            self.save()

class Relationship(models.Model):
    name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

class FamilyMember(models.Model):
    relationship = models.ForeignKey(Relationship, null=True, blank=True, on_delete=models.SET_NULL)
    age = models.IntegerField()
    primary_member = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='family_members', null=True, blank=True)
    
    is_nominee = models.BooleanField(default=False, verbose_name=_('Is Nominee'))
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name=_('Percentage'), null=True, blank=True)

    is_existing_member = models.BooleanField(default=False, verbose_name=_('Is Existing Member'))
    membership_id = models.CharField(max_length=12, unique=True, editable=False, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    # Reference to the selected existing member
    existing_member = models.ForeignKey(Profile, null=True, blank=True, on_delete=models.SET_NULL, related_name='family_member_reference')

    # Save method to assign a custom membership_id
    def save(self, *args, **kwargs):
        if not self.pk and not self.is_existing_member:
            with transaction.atomic():
                last_family_member = FamilyMember.objects.select_for_update().order_by('-id').first()
                if last_family_member and last_family_member.membership_id:
                    try:
                        last_id_number = int(last_family_member.membership_id.split('-')[1])
                    except (IndexError, ValueError):
                        last_id_number = 0
                else:
                    last_id_number = 0

                # Loop until a unique ID is found
                while True:
                    last_id_number += 1
                    new_membership_id = f"104-{last_id_number:06d}"
                    if not FamilyMember.objects.filter(membership_id=new_membership_id).exists():
                        self.membership_id = new_membership_id
                        break

        super(FamilyMember, self).save(*args, **kwargs)

    def __str__(self):
        return self.user.username if self.user else f"Family Member {self.pk}"

    class Meta:
        verbose_name = _('Family Member')
        verbose_name_plural = _('Family Members')


class Team(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class TeamRegistration(models.Model):
    volunteer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_registrations')
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=100, blank=True, null=True)
    joined_on = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('volunteer', 'team')  # Prevent duplicate registrations

    def save(self, *args, **kwargs):
        # Ensure that the selected volunteer is of role "volunteer"
        if self.volunteer.role != "Volunteer":  
            raise ValueError("Only volunteers can be registered in a team.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.volunteer.username} - {self.team.name} ({self.role})"