from django.db import models
from django.core.exceptions import ValidationError
from datetime import date

class Club(models.Model):
    club_name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    club_est = models.DateField()
    club_logo = models.ImageField(upload_to='club_logo/', null=True, blank=True, default='default/club-default.jpg')
    contact_name = models.CharField(max_length=255)  # Contact person for the registration
    contact_email = models.EmailField()  # Contact email
    contact_phone = models.CharField(max_length=20)  # Contact phone number
    created_at = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return self.club_name

    def clean(self):
        if Club.objects.exists() and not self.pk:
            raise ValidationError("Only one club can exist.")

    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure validation before saving
        super().save(*args, **kwargs)
    

class OrganizationRegistrationInfo(models.Model):
    REGISTRATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    # Fields for the registration information
    registration_number = models.CharField(max_length=100, unique=True)  # Unique registration number
    registration_date = models.DateTimeField(auto_now_add=True)  # Date of registration
    registration_status = models.CharField(
        max_length=50,
        choices=REGISTRATION_STATUS_CHOICES,
        default='pending'
    )  # Status of the registration
    license_number = models.CharField(max_length=100, null=True, blank=True)  # Optional license number
    license_expiry_date = models.DateField(null=True, blank=True)  # Optional license expiry date
    organization_name = models.CharField(max_length=255)  # Name of the organization or ministry
    licence_name = models.CharField(max_length=255)
    upload_file = models.ImageField(upload_to='licence/', null=True, blank=True)
    
    registration_notes = models.TextField(null=True, blank=True)  # Any notes related to the registration

    def __str__(self):
        return f"Registration Info for {self.organization_name} (Status: {self.registration_status})"
    
class Committee(models.Model):
    name = models.CharField(max_length=255, unique=True)  # Name of the committee
    description = models.TextField()  # Description of the committee
    start_date = models.DateField()  # Date when the committee started
    end_date = models.DateField(null=True, blank=True)  # Date when the committee ended (nullable)
    is_active = models.BooleanField(default=True)  # Whether the committee is currently active

    def save(self, *args, **kwargs):
        # Auto-deactivate if end_date has passed
        if self.end_date and self.end_date < date.today():
            self.is_active = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    

class Designation(models.Model):
    name = models.CharField(max_length=255)  # Role name (e.g., Chairperson, Secretary)
    description = models.TextField()  # A brief description of the role
    is_active = models.BooleanField(default=True)  # Whether the designation is still active
    created_on = models.DateTimeField(auto_now_add=True)  # Track when the designation was created

    def __str__(self):
        return f"Designation: {self.name} ({'Active' if self.is_active else 'Inactive'})"
    
class Activity(models.Model):
    title = models.CharField(max_length=255)  # Title of the activity
    description = models.TextField()  # Description of the activity
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp when the activity was created

    def __str__(self):
        return self.title
    
    
class CommitteeMember(models.Model):
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='members')  # Reference to the committee
    member = models.ForeignKey('accounts.Profile', on_delete=models.CASCADE)  # The member (User model)
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE, null=True, blank=True)  # Role/designation of the member
    activities = models.ManyToManyField(Activity, blank=True)
    joined_on = models.DateField(auto_now_add=True)  # Date the member joined the committee
    is_active = models.BooleanField(default=True)  # Status of the membership (active/inactive)

    def __str__(self):
        return f"{self.member} in {self.committee.name}"
    
class CommitteeTask(models.Model):
    committee = models.ForeignKey('Committee', on_delete=models.CASCADE, related_name='tasks')  # Reference to the committee
    title = models.CharField(max_length=255)  # Task title
    description = models.TextField()  # Task description
    deadline = models.DateField()  # Task deadline
    status = models.CharField(
        max_length=50,
        choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed')],
        default='pending'
    )  # Task status

    def __str__(self):
        return f"Task: {self.title} (Status: {self.status})"


class CommitteeTaskAssignment(models.Model):
    task = models.ForeignKey(CommitteeTask, on_delete=models.CASCADE, related_name="assignments")
    volunteer = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE, null=True, blank=True,
        related_name="task_assignments"
    )
    team = models.ForeignKey('accounts.Team', on_delete=models.CASCADE, null=True, blank=True, related_name="task_assignments")
    assigned_on = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("in_progress", "In Progress"), ("completed", "Completed")],
        default="pending"
    )

    class Meta:
        unique_together = ('task', 'volunteer', 'team')  # Prevent duplicate assignments

    def __str__(self):
        return f"Task {self.task.title} assigned to {self.volunteer if self.volunteer else self.team.name}"
    
class ExpenseType(models.Model):
    """
    Model to define types of expenses for a committee.
    """
    name = models.CharField(max_length=255)  # Name of the expense type
    description = models.TextField(null=True, blank=True)  # Description of the expense type

    def __str__(self):
        return self.name  # Return the name of the expense type for better readability
    
class CommitteeExpense(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]
    """
    Model to track expenses made by a committee.
    """
    members = models.ForeignKey(CommitteeMember, on_delete=models.CASCADE, related_name='expenses')
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='expenses')
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.CASCADE, related_name='committee_expenses')
    donation_type = models.ForeignKey('payment.DonationType', on_delete=models.CASCADE, related_name='committee_expenses', null=True, blank=True)
    title = models.CharField(max_length=255)  # Title of the expense
    description = models.TextField()  # Description of the expense
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity_unit = models.ForeignKey('payment.DonationUnit', on_delete=models.SET_NULL, null=True, blank=True)
    bank_detail = models.ForeignKey('payment.BankDetail', on_delete=models.SET_NULL, null=True, blank=True)
    mobile_banking_detail = models.ForeignKey('payment.MobileBankingDetail', on_delete=models.SET_NULL, null=True, blank=True)
    expense_date = models.DateField(default=date.today)
    payment_method = models.CharField(max_length=20, choices=[("bank_transfer", "Bank Transfer"), ("mobile_banking", "Mobile Banking")], default='bank_transfer', null=True, blank=True)
    transaction_id = models.CharField(max_length=50, null=True, blank=True)
    proof_of_payment = models.ImageField(upload_to="expense_proofs/", null=True, blank=True)
    expense_notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Timestamp when the expense was created
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)  # Timestamp when the expense was last updated
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='created_expenses', null=True, blank=True)
    updated_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='updated_expenses', null=True, blank=True)


class CommitteePermission(models.Model):
    """
    Model to define permissions for committee members.
    """
    committee = models.ForeignKey(Committee, on_delete=models.CASCADE, related_name='permissions')
    member = models.ForeignKey(CommitteeMember, on_delete=models.CASCADE, related_name='permissions')
    can_approve_expense = models.BooleanField(default=False)  # Permission to approve expenses
    can_reject_expense = models.BooleanField(default=False)  # Permission to reject expenses
    can_approve_donation = models.BooleanField(default=False)  # Permission to approve donations
    can_reject_donation = models.BooleanField(default=False)  # Permission to reject donations

    def __str__(self):
        return f"{self.member} permissions in {self.committee.name}"