from django.contrib import admin
from .models import MembershipPayment, BankDetail, MobileBankingDetail, CommitteeDonation, DonationType, DonationUnit


class BankDetailsAdmin(admin.ModelAdmin):
    list_display = ('bank_name', 'branch_name', 'account_type', 'account_number', 'created_at', 'updated_at')
    search_fields = ('bank_name', 'branch_name', 'account_number')
    list_filter = ('account_type',)
    ordering = ('created_at',)

class MobileBankingDetailAdmin(admin.ModelAdmin):
    list_display = ('banking_name', 'mobile_banking_id', 'mobile_number', 'personal_account', 'merchant_account', 'get_instructions', 'created_at', 'updated_at')
    search_fields = ('mobile_banking_id', 'mobile_number')
    list_filter = ('personal_account', 'merchant_account')
    ordering = ('created_at',)

@admin.register(CommitteeDonation)
class CommitteeDonationAdmin(admin.ModelAdmin):
    list_display = ('name', 'donation_type', 'committee', 'amount', 'quantity', 'status')
    list_filter = ('donation_type', 'committee', 'status')
    search_fields = ('name', 'email', 'phone', 'transaction_id')


admin.site.register(MembershipPayment)
admin.site.register(BankDetail, BankDetailsAdmin)
admin.site.register(MobileBankingDetail, MobileBankingDetailAdmin)

admin.site.register(DonationType)
admin.site.register(DonationUnit)