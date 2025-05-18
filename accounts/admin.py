from django.contrib import admin
from .models import User, Profile, FamilyMember, Team, TeamRegistration, RoleChangeRequest, Relationship, MembershipType, FeeStructure, FeeName



class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'membership_id', 'joining_date', 'is_approved')
    search_fields = ('user__username', 'membership_id')
    list_filter = ('is_approved', 'joining_date')

class FamilyAdmin(admin.ModelAdmin):
    list_display = ('primary_member', 'relationship', 'age', 'is_nominee', 'percentage', 'membership_id')
    # Optional: Add filtering for nominee status
    list_filter = ('is_nominee',)


class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_on', 'is_active')
    search_fields = ('name',)
    list_filter = ('is_active',)

class TeamRegistrationAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'team', 'role', 'joined_on')
    search_fields = ('volunteer__username', 'team__name')
    list_filter = ('team', 'role')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "volunteer":
            # Ensure only volunteers (Users with role 'Volunteer') appear
            kwargs["queryset"] = User.objects.filter(role="Volunteer")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    

class MembershipTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'status')  # Correct attributes
    search_fields = ('name',)

# Membership Free Inline (for use in MembershipTypeAdmin)
class MembershipTypeRegisterInline(admin.TabularInline):
    model = FeeStructure
    extra = 1  # Add one empty registration by default

admin.site.register(User)
admin.site.register(Profile, MemberAdmin)
admin.site.register(FamilyMember, FamilyAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(TeamRegistration, TeamRegistrationAdmin)
admin.site.register(RoleChangeRequest)
admin.site.register(Relationship)
# Register MembershipType with Inline
@admin.register(MembershipType)
class MembershipTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'status')
    inlines = [MembershipTypeRegisterInline]  # Add inline here

# Register MembershipFree separately (if needed)
@admin.register(FeeStructure)
class MembershipFreeAdmin(admin.ModelAdmin):
    list_display = ('membership', 'is_active')

admin.site.register(FeeName)