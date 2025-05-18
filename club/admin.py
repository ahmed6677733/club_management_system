from django.contrib import admin
from django.db.models import Q

from .models import Club, OrganizationRegistrationInfo, Committee, CommitteeTask, CommitteeTaskAssignment, CommitteeMember, Designation, ExpenseType, CommitteeExpense, Activity, CommitteePermission
from accounts.models import User


class ClubAdmin(admin.ModelAdmin):
    list_display = ('club_name', 'description', 'contact_name', 'contact_email', 'created_at')

    def has_add_permission(self, request):
        return not Club.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False  # Prevent deletion

class OrganizationRegistrationInfoAdmin(admin.ModelAdmin):
    list_display = ('organization_name', 'registration_number', 'registration_status', 'license_number', 'registration_date')
    list_filter = ('registration_status', 'license_expiry_date')
    search_fields = ('organization_name', 'registration_number', 'contact_email')

class CommitteeMemberInline(admin.TabularInline):
    model = CommitteeMember
    extra = 1  # Add one empty registration by default

class CommitteeAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_active')  # Use start_date instead of formed_on
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    inlines = [CommitteeMemberInline]

class CommitteeTaskRegistrationInline(admin.TabularInline):
    model = CommitteeTaskAssignment
    extra = 1  # Add one empty registration by default

    def get_queryset(self, request):
        """
        Filter the volunteers to only show those who are volunteers (and not assigned to any task yet).
        """
        queryset = super().get_queryset(request)
        # Get volunteers (filtered by role) who are not assigned to any task
        assigned_volunteers = CommitteeTaskAssignment.objects.values('volunteer')
        unassigned_volunteers = User.objects.filter(role=User.VOLUNTEER).exclude(id__in=assigned_volunteers)
        return queryset.filter(volunteer__in=unassigned_volunteers)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Only show volunteers in the 'volunteer' field.
        """
        if db_field.name == "volunteer":
            kwargs["queryset"] = User.objects.filter(role=User.VOLUNTEER)  # Filter only volunteers
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CommitteeTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'committee', 'status', 'deadline')
    list_filter = ('status', 'committee')
    search_fields = ('title', 'committee__name')
    inlines = [CommitteeTaskRegistrationInline]  # Inline for member registration

class CommitteeTaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ('task', 'volunteer', 'team', 'status', 'assigned_on', 'due_date')
    list_filter = ('status', 'assigned_on', 'due_date')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "volunteer":
            kwargs["queryset"] = User.objects.filter(role=User.VOLUNTEER)  # Filtering users with role 'Volunteer'
        return super().formfield_for_foreignkey(db_field, request, **kwargs)



admin.site.register(Club, ClubAdmin)
admin.site.register(OrganizationRegistrationInfo, OrganizationRegistrationInfoAdmin)

admin.site.register(Committee, CommitteeAdmin)
admin.site.register(CommitteeTask, CommitteeTaskAdmin)
admin.site.register(CommitteeTaskAssignment, CommitteeTaskAssignmentAdmin)
admin.site.register(Designation)
admin.site.register(ExpenseType)
admin.site.register(CommitteeMember)
admin.site.register(CommitteeExpense)
admin.site.register(Activity)
admin.site.register(CommitteePermission)
