from django.db import models
from django.utils import timezone
from accounts.models import MembershipType, User, Profile, FeeStructure
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class BankDetail(models.Model):
    bank_name = models.CharField(max_length=255)
    branch_name = models.CharField(max_length=255)
    account_type = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20, unique=True)
    routing_number = models.CharField(max_length=9, null=True, blank=True)
    contact_number = models.CharField(max_length=15, null=True, blank=True)
    email_address = models.EmailField(null=True, blank=True)
    currencey = models.CharField(max_length=5, default="BDT")  # e.g., BDT for Bangladeshi Taka
    is_active = models.BooleanField(default=True)  # To mark the account as active or deactivated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bank_name} - {self.branch_name}"

class MobileBankingDetail(models.Model):
    mobile_banking_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    banking_name = models.CharField(max_length=20, unique=True, null=True, blank=True)
    mobile_number = models.CharField(max_length=11)
    personal_account = models.BooleanField(default=False)
    merchant_account = models.BooleanField(default=False)
    last_transaction_date = models.DateTimeField(null=True, blank=True)
    currency = models.CharField(max_length=5, default="BDT")  # Currency for mobile banking
    is_active = models.BooleanField(default=True)  # To mark the account as active or deactivated
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.banking_name} - {'Merchant' if self.merchant_account else 'Personal'}"

    def get_instructions(self):
        """
        Returns specific instructions based on the account type:
        - Personal Account: instructions related to sending money.
        - Merchant Account: instructions related to making payments.
        """
        if self.personal_account:
            return _(
                "Instructions for Personal Account:\n"
                "1. Ensure your mobile number is verified before sending money.\n"
                "2. To send money, select the recipient's mobile number and the amount to send.\n"
                "3. Make sure you have sufficient balance in your account.\n"
                "4. Always check the transaction details before confirming.\n"
                "5. For added security, use PIN or OTP for confirming transactions."
            )
        elif self.merchant_account:
            return _(
                "Instructions for Merchant Account:\n"
                "1. To make a payment, ensure that you have an active merchant account.\n"
                "2. Enter the payment details correctly, including the amount and recipient.\n"
                "3. You can make payments for services, goods, or bills directly from your account.\n"
                "4. Ensure that the payment gateway is properly configured and functional.\n"
                "5. Always check transaction history to monitor completed payments."
            )
        else:
            return _("No account type selected. Please choose either a personal or merchant account.")

    def __str__(self):
        return f"{self.mobile_banking_id} - {'Merchant' if self.merchant_account else 'Personal'}"



from django.utils import timezone

class MembershipPayment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('----', 'Select Payment Method'),
        ('CASH', 'Cash'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('MOBILE_BANKING', 'Mobile Banking')
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed')
    ]

    REFUND_STATUS_CHOICES = [
        ('NOT_REFUNDED', 'Not Refunded'),
        ('REFUNDED', 'Refunded')
    ]

    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="membership_payments")
    membership_type = models.ForeignKey(MembershipType, on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=7, decimal_places=2, default=0.00)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='----')
    bank_details = models.ForeignKey(BankDetail, on_delete=models.CASCADE, null=True, blank=True)
    mobile_banking_details = models.ForeignKey(MobileBankingDetail, on_delete=models.CASCADE, null=True, blank=True)
    transaction_id = models.CharField(max_length=50, null=True, blank=True)
    proof_of_payment = models.ImageField(upload_to="payment_proofs/", null=True, blank=True)
    payment_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_months = models.TextField(null=True, blank=True)  # Stores months as a comma-separated string
    payment_notes = models.TextField(null=True, blank=True)
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='NOT_REFUNDED')

    def get_payment_months_list(self):
        """Returns paid months as list of 'Month Year' strings"""
        if not self.payment_months:
            return []
        return [month.strip() for month in self.payment_months.split(",")]

    def has_paid_for_month(self, month, year):
        """Check if a specific month-year is paid for"""
        return f"{month} {year}" in self.get_payment_months_list()

    @staticmethod
    def get_paid_months_for_user(user):
        """Get all unique paid months for a user"""
        payments = MembershipPayment.objects.filter(profile__user=user, status="COMPLETED")
        paid_months = []
        for payment in payments:
            paid_months.extend(payment.get_payment_months_list())
        return sorted(set(paid_months))

    def __str__(self):
        return f"Payment {self.profile.user.username} - {self.membership_type.name} - {self.fee_structure.fee_name.name} - Months: {self.payment_months} - Status: {self.status}"
    
class DonationType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=50, blank=True, null=True)
    amount = models.BooleanField(default=False)
    quantity = models.BooleanField(default=False)
    quantity_unit = models.BooleanField(default=False)
    bank_detail = models.BooleanField(default=False)
    mobile_banking_detail = models.BooleanField(default=False)
    payment_method = models.BooleanField(default=False)
    transaction_id = models.BooleanField(default=False)
    proof_of_payment = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class DonationUnit(models.Model):
    title = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.title

class CommitteeDonation(models.Model):
    committee = models.ForeignKey('club.Committee', on_delete=models.CASCADE, related_name='donations')
    donor = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='committee_donations', null=True, blank=True)
    donation_type = models.ForeignKey(DonationType, on_delete=models.CASCADE, related_name='committee_donations', null=True, blank=True)
    is_member = models.BooleanField(default=False)
    
    # Donor details
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    # Donation-specific fields
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="For monetary donations")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="For non-cash donations like rice or blood (bags/kg/etc.)")
    quantity_unit = models.ForeignKey(DonationUnit, on_delete=models.SET_NULL, null=True, blank=True, help_text="Unit of measurement for quantity")

    # Payment info
    bank_detail = models.ForeignKey(BankDetail, on_delete=models.SET_NULL, null=True, blank=True)
    mobile_banking_detail = models.ForeignKey(MobileBankingDetail, on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField(max_length=20, choices=MembershipPayment.PAYMENT_METHOD_CHOICES, default='----')
    transaction_id = models.CharField(max_length=50, null=True, blank=True)
    proof_of_payment = models.ImageField(upload_to="donation_proofs/", null=True, blank=True)

    donation_date = models.DateField(default=timezone.now)
    donattion_notes = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=MembershipPayment.PAYMENT_STATUS_CHOICES, default='PENDING', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='donation_created_by')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='donation_updated_by')

    def __str__(self):
        return f"Donation ({self.donation_type}) - {self.committee.name} - {self.name or 'Anonymous'}"
