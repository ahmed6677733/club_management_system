from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date
from datetime import datetime
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse
from django.forms import modelformset_factory
from django.utils import timezone
from django.db import transaction
from django.forms import inlineformset_factory
from django.utils.timezone import now
from datetime import timedelta
from django.views.decorators.http import require_POST

from club.models import Club, OrganizationRegistrationInfo, Committee, CommitteeTask, Designation, CommitteeMember
from club.forms import ClubForm, OrganizationRegistrationForm, CommitteeForm, CommitteeTaskAssignment, CommitteeMemberFormSet
from club.forms import OrganizationRegistrationFormSet, CommitteeTaskForm, CommitteeTaskAssignmentForm
from accounts.models import RoleChangeRequest, Profile, User, Team, TeamRegistration, MembershipType, FeeName, FeeStructure
from accounts.forms import TeamForm, TeamRegistrationFormSet, MembershipTypeForm, FeeNameForm, FeeStructureForm, FeeStructureFormSet

from django.http import HttpResponseForbidden
from club.models import Committee, CommitteeMember, CommitteeExpense, ExpenseType, Designation, CommitteeTaskAssignment, Activity, CommitteePermission
from club.forms import CommitteeExpenseForm, ExpenseTypeForm, DesignationForm, CommitteePermissionForm

from payment.models import DonationType
from payment.forms import DonationTypeForm

@login_required
def dashboard(request):

    # Total Committees, Active Committees, and Inactive Committees
    total_committees = Committee.objects.count()
    active_committees = Committee.objects.filter(is_active=True).count()
    inactive_committees = Committee.objects.filter(is_active=False).count()

    # Task statuses (Pending, In Progress, Completed)
    total_tasks = CommitteeTask.objects.count()
    pending_tasks = CommitteeTask.objects.filter(status='pending').count()
    in_progress_tasks = CommitteeTask.objects.filter(status='in_progress').count()
    completed_tasks = CommitteeTask.objects.filter(status='completed').count()

    return render(request, 'dashboard/dashboard.html', {
        'total_committees': total_committees,
        'active_committees': active_committees,
        'inactive_committees': inactive_committees,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
    })

@login_required
def get_dashboard_data(request):
    # Fetch the real-time data from the database
    total_committees = Committee.objects.count()
    active_committees = Committee.objects.filter(is_active=True).count()
    inactive_committees = Committee.objects.filter(is_active=False).count()

    total_tasks = CommitteeTask.objects.count()
    pending_tasks = CommitteeTask.objects.filter(status='pending').count()
    in_progress_tasks = CommitteeTask.objects.filter(status='in_progress').count()
    completed_tasks = CommitteeTask.objects.filter(status='completed').count()

    # Return data as a JSON response
    return JsonResponse({
        'total_committees': total_committees,
        'active_committees': active_committees,
        'inactive_committees': inactive_committees,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'completed_tasks': completed_tasks,
    })


@login_required
def club_profile(request):
    try:
        club = Club.objects.first()  # Assuming only one club can exist
    except Club.DoesNotExist:
        club = None

    if request.method == "POST":
        formset = OrganizationRegistrationFormSet(request.POST, request.FILES)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Organizations registered successfully!")
            return redirect("club_profile")
        else:
            messages.error(request, "Some entries have errors. Please fix them.")
    else:
        formset = OrganizationRegistrationFormSet(queryset=OrganizationRegistrationInfo.objects.none())

    org_info_list = OrganizationRegistrationInfo.objects.all()

    return render(request, "dashboard/club_profile.html", {
        "club": club,
        "formset": formset,
        "org_info_list": org_info_list
    })

def committee_list(request):
    committees = Committee.objects.all()
    expense_types = ExpenseType.objects.all()
    committee_designations = Designation.objects.all()
    donation_types = DonationType.objects.all()
    return render(request, 'dashboard/committee_list.html', {
        'committees': committees,
        'expense_types': expense_types,
        'committee_designations': committee_designations,
        'donation_types': donation_types,
    })

def create_committee_with_members(request):
    if request.method == 'POST':
        form = CommitteeForm(request.POST)
        formset = CommitteeMemberFormSet(request.POST, queryset=CommitteeMember.objects.none())

        if form.is_valid() and formset.is_valid():
            committee = form.save()

            # Save committee members
            instances = formset.save(commit=False)
            for instance in instances:
                instance.committee = committee
                instance.save()

            # Save many-to-many fields (e.g., activities)
            formset.save_m2m()

            return redirect('success_url')  # change to your actual redirect
    else:
        form = CommitteeForm()
        formset = CommitteeMemberFormSet(queryset=CommitteeMember.objects.none())

    return render(request, 'dashboard/committee_form.html', {'form': form, 'formset': formset})


def edit_committee(request, committee_id):
    committee = get_object_or_404(Committee, id=committee_id)

    if request.method == 'POST':
        form = CommitteeForm(request.POST, instance=committee)
        formset = CommitteeMemberFormSet(request.POST, instance=committee)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('committee_list')
    else:
        form = CommitteeForm(instance=committee)
        formset = CommitteeMemberFormSet(instance=committee)

    return render(request, 'dashboard/committee_edit.html', {'form': form, 'formset': formset, 'committee': committee})

@login_required
def register_member(request, committee_id):
    committee = get_object_or_404(Committee, id=committee_id)
    
    if request.method == 'POST':
        members = request.POST.getlist('members[]')
        designations = request.POST.getlist('designation[]')

        # Debugging step: Print the selected members and designations
        print(f"Members: {members}")
        print(f"Designations: {designations}")

        # Ensure members and designations match in length
        if len(members) != len(designations):
            print(f"Mismatch: Members count = {len(members)}, Designations count = {len(designations)}")
            return render(request, 'dashboard/committee_detail.html', {'committee': committee, 'error': 'Mismatch in members and designations count.'})

        # Process registration for each member and designation
        for member_id, designation_id in zip(members, designations):
            committee_registration = Committee(
                committee=committee,
                member_id=member_id,
                designation_id=designation_id,
                is_active=True  # Assuming the default status is active
            )
            committee_registration.save()

        return redirect('committee_detail', committee.id)

    return render(request, 'dashboard/committee_detail.html', {'committee': committee})


@login_required
def role_change_request_list(request):
    # List all pending requests
    pending_requests = RoleChangeRequest.objects.filter(status=RoleChangeRequest.PENDING)
    pending_count = RoleChangeRequest.objects.filter(status=RoleChangeRequest.PENDING).count()

    return render(request, 'dashboard/role_change_request_list.html', {
        'pending_requests': pending_requests,
        'pending_count': pending_count
    })


def approve_role_change(request, request_id):
    """Approve the role change request and notify the user."""
    # Get the RoleChangeRequest by ID
    role_change_request = get_object_or_404(RoleChangeRequest, id=request_id)

    if role_change_request.status != role_change_request.APPROVED:
        # Update status to approved
        role_change_request.status = role_change_request.APPROVED
        role_change_request.save()

        # Update user's role and regenerate membership ID
        user = role_change_request.user
        new_role = role_change_request.new_role
        
        # Update the user's role
        user.role = new_role
        user.save()

        # Update the profile's role and regenerate membership ID
        profile = user.profile
        profile.role = new_role
        profile.membership_id = profile.generate_membership_id()  # Regenerate the membership ID
        profile.save()

        # Send email notification to the user
        send_role_change_email(user, new_role)

        # Display success message
        messages.success(request, f"Role change request approved for {user.username}. A confirmation email has been sent.")

    return redirect('role_change_request_list')  # Redirect to the list of requests (or any page you prefer)


def send_role_change_email(user, new_role):
    """Send an email notification to the user about their role change and new membership ID."""
    subject = f"Your Role Change Request Approved"
    message = f"Dear {user.username},\n\n" \
              f"Congratulations! Your role has been updated to {new_role}.\n" \
              f"Your new membership ID is: {user.profile.membership_id}.\n\n" \
              f"Thank you for being a part of our community.\n\n" \
              f"Best Regards,\nThe Team"

    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, email_from, recipient_list)

@login_required
def reject_role_change(request, request_id):
    """Reject a role change request."""
    # Check if the user is an admin (only admins can reject requests)
    if not request.user.is_superuser:
        return redirect('home')  # Redirect non-admin users to home page

    # Get the RoleChangeRequest object by ID
    role_change_request = get_object_or_404(RoleChangeRequest, id=request_id)

    if role_change_request.status == RoleChangeRequest.PENDING:
        role_change_request.status = RoleChangeRequest.REJECTED  # Mark the request as rejected
        role_change_request.save()

        # Send an email notification to the user
        send_role_change_rejection_email(role_change_request.user)

        # Display a success message
        messages.success(request, f"Role change request for {role_change_request.user.username} has been rejected.")

    return redirect('role_change_request_list')  # Redirect to the list of role change requests

def send_role_change_rejection_email(user):
    """Send an email notification to the user about their rejected role change request."""
    subject = f"Your Role Change Request Rejected"
    message = f"Dear {user.username},\n\n" \
              f"We regret to inform you that your role change request has been rejected.\n\n" \
              f"If you have any questions or would like to reapply, please contact the administration.\n\n" \
              f"Best Regards,\nThe Team"

    email_from = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, message, email_from, recipient_list)


@login_required
def membership_applications(request):
    if request.user.role != 'Admin':  # Only Admins should manage applications
        return redirect('dashboard')

    applications = Profile.objects.filter(is_approved=False)  # Pending applications
    return render(request, 'dashboard/membership_applications.html', {'applications': applications})

@login_required
def approve_membership(request, profile_id):
    if request.user.role != 'Admin':
        return redirect('dashboard')

    profile = get_object_or_404(Profile, id=profile_id)
    profile.is_approved = True
    profile.save()

    # Send email notification
    send_mail(
        'Membership Approved',
        f'Dear {profile.user.full_name},\n\nYour membership has been approved.\n\nWelcome!',
        settings.DEFAULT_FROM_EMAIL,
        [profile.user.email],
        fail_silently=True,
    )

    return redirect('membership_applications')


@login_required
def reject_membership(request, profile_id):
    if request.user.role != 'Admin':
        return redirect('dashboard')

    profile = get_object_or_404(Profile, id=profile_id)
    user_email = profile.user.email
    profile.delete()  # Remove rejected application

    # Send email notification
    send_mail(
        'Membership Rejected',
        f'Dear Applicant,\n\nUnfortunately, your membership application has been rejected.',
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=True,
    )

    return redirect('membership_applications')

@login_required
def volunteer_dashboard(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Check if AJAX request
        total_tasks = CommitteeTask.objects.count()
        pending_tasks = CommitteeTask.objects.filter(status='pending').count()
        in_progress_tasks = CommitteeTask.objects.filter(status='in_progress').count()
        completed_tasks = CommitteeTask.objects.filter(status='completed').count()

        # Query the logged-in user instance
        user_instance = request.user

        # Fetch committees where the user is registered
        committees = Committee.objects.filter(registrations__in=user_registrations).values("name")

        # Fetch recent tasks assigned to the logged-in user (only their tasks)
        recent_tasks = CommitteeTaskAssignment.objects.filter(volunteer=user_instance).order_by('-assigned_on')[:5].values("task__title", "task__status", "due_date")

        return JsonResponse({
            'total_tasks': total_tasks,
            'pending_tasks': pending_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completed_tasks': completed_tasks,
            'committees': list(committees),
            'recent_tasks': list(recent_tasks),
        })

    return render(request, 'dashboard/volunteer_dashboard.html')

def task_list(request):
    tasks = CommitteeTask.objects.all()

    task_assignments = []
    for task in tasks:
        assignments = CommitteeTaskAssignment.objects.filter(task=task)
        assigned_volunteers = [a.volunteer.username for a in assignments if a.volunteer]
        assigned_teams = [a.team.name for a in assignments if a.team]

        task_assignments.append({
            "task": task,
            "volunteers": assigned_volunteers,
            "teams": assigned_teams,
        })

    context = {
        "task_assignments": task_assignments
    }
    return render(request, 'dashboard/task_list.html', context)


def create_and_assign_task(request):
    if request.method == 'POST':
        # Initialize the task form with POST data
        task_form = CommitteeTaskForm(request.POST)
        
        # Get the list of selected volunteers and teams
        volunteers = request.POST.getlist('volunteers')
        teams = request.POST.getlist('teams')

        if task_form.is_valid():
            # Create the task object (don't save yet)
            task = task_form.save(commit=False)
            
            # Optionally, add more data to the task before saving
            task.save()  # Save the task to the database once
            
            # Begin atomic transaction to handle task assignments
            with transaction.atomic():
                # Assign task to selected volunteers
                if volunteers:
                    assign_to_volunteers(task, volunteers)
                
                # Assign task to selected teams
                if teams:
                    assign_to_teams(task, teams)

            # Show a success message to the user
            messages.success(request, "Task created and assignments completed successfully.")

            # Redirect to a success page or the task list page
            return redirect('dashboard')  # Change this to your actual success page URL

    else:
        # If the request is GET, just render the form without pre-filling data
        task_form = CommitteeTaskForm()

    # Provide volunteers and teams to select in the form
    context = {
        'task_form': task_form,
        'volunteers': User.objects.filter(role='Volunteer'),
        'teams': Team.objects.all()
    }
    
    # Render the task creation form with volunteers and teams
    return render(request, 'dashboard/create_task_and_assign.html', context)

def assign_to_volunteers(task, volunteer_ids):
    """
    Assign the task to volunteers and send email notifications.
    """
    volunteers = User.objects.filter(id__in=volunteer_ids, role='Volunteer')

    for volunteer in volunteers:
        # Check if the task is already assigned to the volunteer
        existing_assignment = CommitteeTaskAssignment.objects.filter(task=task, volunteer=volunteer).exists()
        
        if not existing_assignment:  # Only assign if not already assigned
            # Create task assignment for each volunteer
            CommitteeTaskAssignment.objects.create(
                task=task,
                volunteer=volunteer,
                assigned_on=timezone.now()
            )
            
            # Send email notification to the volunteer
            send_task_notification(volunteer.email, volunteer.username, task.title)

def assign_to_teams(task, team_ids):
    """
    Assign the task to teams and send email notifications to all members of the teams.
    """
    teams = Team.objects.filter(id__in=team_ids)

    for team in teams:
        # Fetch TeamRegistration to get all registered volunteers for the team
        team_registrations = TeamRegistration.objects.filter(team=team)

        for registration in team_registrations:
            volunteer = registration.volunteer  # This is the User object (volunteer)

            # Check if the task is already assigned to the volunteer for this team
            existing_assignment = CommitteeTaskAssignment.objects.filter(task=task, volunteer=volunteer, team=team).exists()
            
            if not existing_assignment:  # Only assign if not already assigned
                # Create task assignment for each team member
                CommitteeTaskAssignment.objects.create(
                    task=task,
                    team=team,
                    volunteer=volunteer,
                    assigned_on=timezone.now()
                )

                # Send email notification to the team member (volunteer)
                send_task_notification(volunteer.email, volunteer.username, task.title)

def send_task_notification(email, username, task_title):
    """
    Send a task notification email to a user.
    """
    subject = 'New Task Assigned'
    message = f'Hello {username},\n\nYou have been assigned a new task: {task_title}.'
    
    # Send the email using the default email configuration in settings
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email]
    )

def create_team(request):
    if request.method == "POST":
        team_form = TeamForm(request.POST)
        formset = TeamRegistrationFormSet(request.POST)

        if team_form.is_valid() and formset.is_valid():
            team = team_form.save()
            registrations = formset.save(commit=False)
            for registration in registrations:
                registration.team = team
                registration.save()
            messages.success(request, "Team and registrations created successfully!")
            return redirect("team_list")

    else:
        team_form = TeamForm()
        formset = TeamRegistrationFormSet()

    return render(request, "dashboard/create_team.html", {"team_form": team_form, "formset": formset})


def list_teams(request):
    teams = Team.objects.all()
    return render(request, "dashboard/team_list.html", {"teams": teams})


def edit_team(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    if request.method == "POST":
        team_form = TeamForm(request.POST, instance=team)
        formset = TeamRegistrationFormSet(request.POST, instance=team)

        if team_form.is_valid() and formset.is_valid():
            team_form.save()
            formset.save()
            messages.success(request, "Team and registrations updated successfully!")
            return redirect("team_list")

    else:
        team_form = TeamForm(instance=team)
        formset = TeamRegistrationFormSet(instance=team)

    return render(request, "dashboard/create_team.html", {"team_form": team_form, "formset": formset})


def delete_team(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    team.delete()
    messages.success(request, "Team deleted successfully!")
    return redirect("team_list")

def create_membership(request):
    if request.method == "POST":
        membership_form = MembershipTypeForm(request.POST)
        fee_formset = FeeStructureFormSet(request.POST)

        if membership_form.is_valid() and fee_formset.is_valid():
            membership = membership_form.save()
            fee_instances = fee_formset.save(commit=False)
            for fee in fee_instances:
                fee.membership = membership  # Link to newly created membership
                fee.save()
            return redirect('membership_list')  # Redirect to success page

    else:
        membership_form = MembershipTypeForm()
        fee_formset = FeeStructureFormSet()

    return render(request, 'dashboard/create_membership.html', {
        'membership_form': membership_form,
        'fee_formset': fee_formset
    })

def membership_list(request):
    memberships = MembershipType.objects.all()  # Fetch all membership types
    fees = FeeName.objects.all()
    return render(request, 'dashboard/membership_list.html', {'memberships': memberships, "fees": fees})

def edit_membership(request, membership_id):
    membership = get_object_or_404(MembershipType, id=membership_id)

    # Creating form instance with existing data
    membership_form = MembershipTypeForm(instance=membership)

    # Creating a formset for Fee Structure
    FeeStructureFormSet = modelformset_factory(FeeStructure, form=FeeStructureForm, extra=1, can_delete=True)
    fee_formset = FeeStructureFormSet(queryset=FeeStructure.objects.filter(membership=membership))

    if request.method == 'POST':
        membership_form = MembershipTypeForm(request.POST, instance=membership)
        fee_formset = FeeStructureFormSet(request.POST)

        if membership_form.is_valid() and fee_formset.is_valid():
            membership_form.save()

            # Save Fee Structure Formset
            fee_instances = fee_formset.save(commit=False)
            for fee in fee_instances:
                fee.membership = membership
                fee.save()

            # Delete removed fee structures
            for fee in fee_formset.deleted_objects:
                fee.delete()

            return redirect('membership_list')  # Change to your membership list view

    return render(request, 'dashboard/edit_membership.html', {
        'membership_form': membership_form,
        'fee_formset': fee_formset,
    })

def create_fee_name(request):
    if request.method == 'POST':
        form = FeeNameForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('fee_name_list')  # Redirect to the list of Fee Names or another page
    else:
        form = FeeNameForm()
    
    return render(request, 'dashboard/create_fee_name.html', {'form': form})

def edit_fee_name(request, fee_name_id):
    fee_name = get_object_or_404(FeeName, id=fee_name_id)

    if request.method == 'POST':
        form = FeeNameForm(request.POST, instance=fee_name)
        if form.is_valid():
            form.save()
            return redirect('fee_name_list')  # Redirect to Fee Name list or another page
    else:
        form = FeeNameForm(instance=fee_name)
    
    return render(request, 'dashboard/edit_fee_name.html', {'form': form, 'fee_name': fee_name})

from .forms import CommitteeExpenseFormDashboard
@login_required
def add_committee_expense(request):
    if request.method == 'POST':
        form = CommitteeExpenseFormDashboard(request.POST, request.FILES)
        if form.is_valid():
            try:
                expense = form.save(commit=False)
                expense.members = request.user.profile  # Use the logged-in user's profile
                expense.committee = request.user.profile.committee  # Assuming user has a related committee

                # Adjust payment method details
                if expense.payment_method == 'bank_transfer':
                    expense.mobile_banking_detail = None
                elif expense.payment_method == 'mobile_banking':
                    expense.bank_detail = None

                expense.save()
                return redirect('committee_expense_list')  # Assuming the URL name is correct
            except Exception as e:
                # Handle any unexpected errors during the save operation
                return render(request, 'dashboard/committee_expense_form.html', {'form': form, 'error': str(e)})
        else:
            # Return the form with validation errors if it's not valid
            return render(request, 'dashboard/committee_expense_form.html', {'form': form})

    else:
        # For GET requests, initialize an empty form
        form = CommitteeExpenseFormDashboard()

    return render(request, 'dashboard/committee_expense_form.html', {'form': form})


# def committee_expense_list(request):
#     expenses = CommitteeExpense.objects.all()
#     return render(request, 'dashboard/committee_expense_list.html', {'expenses': expenses})


def expense_type_form(request, pk=None):
    if pk:
        expense_type = get_object_or_404(ExpenseType, pk=pk)
    else:
        expense_type = None

    if request.method == 'POST':
        form = ExpenseTypeForm(request.POST, instance=expense_type)
        if form.is_valid():
            form.save()
            return redirect('committee_list')
    else:
        form = ExpenseTypeForm(instance=expense_type)

    return render(request, 'dashboard/create_expense_type.html', {
        'form': form,
        'is_edit': bool(pk)
    })

def delete_expense_type(request, pk):
    expense_type = get_object_or_404(ExpenseType, pk=pk)
    expense_type.delete()
    messages.success(request, "Expense type deleted successfully!")
    return redirect('committee_list')  # Redirect to the committee list or any other page

def designation_form(request, pk=None):
    if pk:
        designation = get_object_or_404(Designation, pk=pk)
    else:
        designation = None

    if request.method == 'POST':
        form = DesignationForm(request.POST, instance=designation)
        if form.is_valid():
            form.save()
            return redirect('committee_list')  # Change to your desired redirect
    else:
        form = DesignationForm(instance=designation)

    return render(request, 'dashboard/create_designation.html', {
        'form': form,
        'is_edit': bool(pk)
    })

def activity_form(request, pk=None):
    # if pk:
    #     activity = get_object_or_404(Activity, pk=pk)
    # else:
    #     activity = None

    # if request.method == 'POST':
    #     form = ActivityForm(request.POST, instance=activity)
    #     if form.is_valid():
    #         form.save()
    #         return redirect('activity_list')  # Change to your desired redirect
    # else:
    #     form = ActivityForm(instance=activity)

    # return render(request, 'dashboard/create_activity.html', {
    #     'form': form,
    #     'is_edit': bool(pk)
    # })
    pass

def donation_type_list(request):
    donation_types = DonationType.objects.all().order_by('-created_at')
    return render(request, 'dashboard/donation_type_list.html', {
        'donation_types': donation_types
    })

def donation_type_create_or_edit(request, pk=None):
    if pk:
        donation_type = get_object_or_404(DonationType, pk=pk)
        title = "Edit Donation Type"
    else:
        donation_type = None
        title = "Create Donation Type"

    if request.method == 'POST':
        form = DonationTypeForm(request.POST, instance=donation_type)
        if form.is_valid():
            form.save()
            if pk:
                messages.success(request, "Donation Type updated successfully.")
            else:
                messages.success(request, "Donation Type created successfully.")
            return redirect('donation_type_list')  # Change this if your list view has a different name
    else:
        form = DonationTypeForm(instance=donation_type)

    return render(request, 'dashboard/create_edit_donation_type.html', {
        'form': form,
        'title': title
    })

@require_POST
def donation_type_delete(request, pk):
    donation_type = get_object_or_404(DonationType, pk=pk)
    donation_type.delete()
    messages.success(request, "Donation Type deleted successfully.")
    return redirect('donation_type_list')

from accounts.forms import UpdateUserForm, MemberForm, FamilyMemberForm, UserForm
from accounts.models import User, Profile, FamilyMember
from collections import defaultdict
from payment.models import CommitteeDonation



def user_list_view(request):
    users = User.objects.select_related('profile')
    admins = users.filter(role=User.ADMIN)
    volunteers = users.filter(role=User.VOLUNTEER)
    profile = Profile.objects.all()

    # Get users marked as MEMBER
    all_members = users.filter(role=User.MEMBER)

    # Get user IDs linked in FamilyMember
    family_member_user_ids = FamilyMember.objects.filter(user__isnull=False).values_list('user_id', flat=True)

    # Split members into primary and sub members
    primary_members = all_members.exclude(id__in=family_member_user_ids)
    sub_members = all_members.filter(id__in=family_member_user_ids)

    family_members = FamilyMember.objects.select_related('primary_member__user', 'relationship', 'user')

    # Group family members by their primary member's profile
    family_by_primary = defaultdict(list)
    for fm in family_members:
        if fm.primary_member:
            family_by_primary[fm.primary_member.id].append(fm)

    return render(request, 'dashboard/user_dashboard.html', {
        'user': users,
        'admins': admins,
        'volunteers': volunteers,
        'members': primary_members,
        'sub_members': sub_members,
        'family_by_primary': family_by_primary,
        'family_members': family_members,
    })

from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from io import BytesIO

@login_required
def generate_profile_pdf(request, profile_id):
    try:
        profile = get_object_or_404(Profile, id=profile_id)

        family_members = profile.family_members.all() if hasattr(profile, 'family_members') else []
        committee_memberships = CommitteeMember.objects.filter(member=profile)
        expenses = CommitteeExpense.objects.filter(members__member=profile)
        donations = CommitteeDonation.objects.filter(donor=profile.user) if hasattr(profile, 'user') else []

        context = {
            'user': profile.user if hasattr(profile, 'user') else None,
            'profile': profile,
            'family_members': family_members,
            'committee_memberships': committee_memberships,
            'expenses': expenses,
            'donations': donations,
        }

        template = get_template('dashboard/reports/profile_report.html')
        html_string = template.render(context, request)

        # Generate PDF
        pdf_file = BytesIO()
        HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(pdf_file)

        # Return response
        response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
        filename = f"{profile.user.username}_profile_report.pdf" if hasattr(profile, 'user') else f"profile_{profile_id}_report.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)

def profile_detail_view(request, profile_id):
    user = get_object_or_404(User, id=profile_id)
    profile = user.profile  # Assuming you have a OneToOne relationship with Profile
    return render(request, 'dashboard/profile_detail.html', {'user': user, 'profile': profile})

def profile_edit_view(request, profile_id):
    user = get_object_or_404(User, id=profile_id)
    profile = user.profile

    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, request.FILES, instance=user)
        profile_form = MemberForm(request.POST, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile_detail', profile_id=user.id)
    else:
        user_form = UpdateUserForm(instance=user)
        profile_form = MemberForm(instance=profile)

    context = {
        'user': user,
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'dashboard/profile_edit.html', context)

from .forms import DashboardFamilyMemberForm

def add_family_member_view(request):
    profile_id = request.GET.get('profile_id')
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES)
        family_member_form = DashboardFamilyMemberForm(request.POST)
        
        if user_form.is_valid() and family_member_form.is_valid():
            user = user_form.save()
            family_member = family_member_form.save(commit=False)
            family_member.user = user
            
            # Set primary_member from URL parameter if it exists
            if profile_id:
                try:
                    profile = Profile.objects.get(id=profile_id)
                    family_member.primary_member = profile
                except Profile.DoesNotExist:
                    pass
                    
            family_member.save()
            messages.success(request, 'Family member added successfully!')
            return redirect('user_dashboard')
    else:
        user_form = UserForm()
        family_member_form = DashboardFamilyMemberForm()
        
        # Pre-select the primary member if profile_id was provided
        if profile_id:
            try:
                profile = Profile.objects.get(id=profile_id)
                family_member_form.fields['primary_member'].initial = profile
            except Profile.DoesNotExist:
                pass

    context = {
        'user_form': user_form,
        'family_member_form': family_member_form,
        'title': 'Add Family Member'
    }
    return render(request, 'dashboard/add_family_member.html', context)

# def add_family_member_view(request):
#     if request.method == 'POST':
#         form = FamilyMemberForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('admin_family_member_success')  # Adjust as needed
#     else:
#         form = FamilyMemberForm()
#     return render(request, 'dashboard/add_family_member.html', {'form': form})

# def add_family_member_view(request, user_id):
#     user = get_object_or_404(User, id=user_id)
#     primary_member = get_object_or_404(Profile, user=user)

#     if request.method == 'POST':
#         form = FamilyMemberForm(request.POST)
#         user_form = UserForm(request.POST, request.FILES)

#         if form.is_valid():
#             family_member = form.save(commit=False)
#             family_member.primary_member = primary_member

#             if form.cleaned_data['is_existing_member']:
#                 # ✅ Assign the selected existing_member manually
#                 family_member.existing_member = form.cleaned_data.get('existing_member')
#             else:
#                 if user_form.is_valid():
#                     new_user = user_form.save()
#                     family_member.user = new_user

#             family_member.save()
#             return redirect('user_dashboard')
#     else:
#         form = FamilyMemberForm()
#         user_form = UserForm()

#     return render(request, 'dashboard/add_family_member.html', {
#         'form': form,
#         'user_form': user_form,
#         'primary_member': primary_member,
#     })

# def search_profiles(request):
#     query = request.GET.get('q', '').strip()
#     if not query:
#         return JsonResponse([], safe=False)

#     profiles = Profile.objects.filter(
#         Q(membership_id__icontains=query) |
#         Q(user__first_name__icontains=query) |
#         Q(user__last_name__icontains=query) |
#         Q(user__email__icontains=query)
#     ).select_related('user')[:10]

#     results = [{
#         'id': p.id,
#         'membership_id': p.membership_id or '',
#         'full_name': p.user.full_name,
#         'email': p.user.email
#     } for p in profiles]

#     return JsonResponse(results, safe=False)

@require_POST
@login_required
def change_donation_status(request, donation_id, new_status):
    valid_statuses = ['COMPLETED', 'FAILED']
    donation = get_object_or_404(CommitteeDonation, id=donation_id)

    if new_status not in valid_statuses:
        messages.error(request, "Invalid status change request.")
        return redirect('donation_list')

    # Optional: add permission logic here (e.g., only admins can change status)

    donation.status = new_status
    donation.updated_by = request.user
    # updated_at will automatically update because of auto_now=True
    donation.save()

    messages.success(request, f"Donation marked as {new_status}.")
    return redirect('donation_list')

def donations_by_status(request, status):
    status = status.upper()
    valid_statuses = ['PENDING', 'COMPLETED', 'FAILED']

    if status not in valid_statuses:
        status = 'PENDING'  # fallback

    donations = CommitteeDonation.objects.filter(status=status).order_by('-donation_date')
    return render(request, 'dashboard/donations_list.html', {
        'donations': donations,
        'status': status
    })

def donation_list(request):
    status = request.GET.get('status')  # get from ?status=completed
    donations = CommitteeDonation.objects.all().order_by('-donation_date')

    if status in ['PENDING', 'COMPLETED', 'FAILED']:
        donations = donations.filter(status=status)

    return render(request, 'dashboard/donations_list.html', {
        'donations': donations,
        'active_status': status or 'ALL',
    })

@require_POST
@login_required
def change_expense_status(request, expense_id, new_status):
    valid_statuses = ['COMPLETED', 'FAILED']
    expense = get_object_or_404(CommitteeExpense, id=expense_id)

    if new_status.upper() not in valid_statuses:
        messages.error(request, "Invalid status change request.")
        return redirect('expense_list')

    expense.status = new_status.upper()
    expense.updated_by = request.user
    expense.save()

    messages.success(request, f"Expense status updated to {new_status}.")
    return redirect('expense_list')

@login_required
def expenses_by_status(request, status):
    status = status.upper()
    valid_statuses = ['PENDING', 'COMPLETED', 'FAILED']

    if status not in valid_statuses:
        return redirect('expense_list')

    expenses = CommitteeExpense.objects.filter(status=status).order_by('-expense_date')
    return render(request, 'dashboard/expenses_list.html', {
        'expenses': expenses,
        'active_status': status
    })

@login_required
def expense_list(request):
    status = request.GET.get('status', '').upper()
    valid_statuses = ['PENDING', 'COMPLETED', 'FAILED']

    if status in valid_statuses:
        expenses = CommitteeExpense.objects.filter(status=status).order_by('-expense_date')
        active_status = status
    else:
        expenses = CommitteeExpense.objects.all().order_by('-expense_date')
        active_status = 'ALL'

    return render(request, 'dashboard/expenses_list.html', {
        'expenses': expenses,
        'active_status': active_status,
    })

from .forms import CommitteeDonationFormDashboard

@login_required
def add_committee_donation(request):
    if request.method == 'POST':
        form = CommitteeDonationFormDashboard(request.POST, request.FILES)
        if form.is_valid():
            try:
                donation = form.save(commit=False)
                donation.created_by = request.user
                
                # Set donor information
                if donation.donor:
                    donation.is_member = True
                    donation.name = f"{donation.donor.first_name} {donation.donor.last_name}"
                    donation.email = donation.donor.email
                    
                    # Try to get profile info if exists
                    if hasattr(donation.donor, 'profile'):
                        profile = donation.donor.profile
                        donation.phone = getattr(profile, 'phone', '')
                        donation.address = getattr(profile, 'address', '')
                
                # Handle payment method details
                if donation.payment_method == 'bank_transfer':
                    donation.mobile_banking_detail = None
                elif donation.payment_method == 'mobile_banking':
                    donation.bank_detail = None
                
                donation.save()
                return redirect('committee_donation_list')
                
            except Exception as e:
                return render(request, 'dashboard/committee_donation_form.html', 
                           {'form': form, 'error': str(e)})
        else:
            return render(request, 'dashboard/committee_donation_form.html', 
                        {'form': form})
    else:
        initial_data = {}
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'committee'):
            initial_data['committee'] = request.user.profile.committee
            
        form = CommitteeDonationFormDashboard(initial=initial_data)
        
    return render(request, 'dashboard/committee_donation_form.html', 
                {'form': form})


def toggle_user_status(request, user_id):
    # Get user or return 404
    user = get_object_or_404(User, id=user_id)
    
    # Toggle status
    user.is_active = not user.is_active
    user.save()
    
    # Set message
    status = 'activated' if user.is_active else 'deactivated'
    messages.success(request, f'User {user.username} has been {status}')
    
    # Redirect back to user list
    return redirect('user_dashboard')  # Change 'user_list' to your URL name

from django.views.generic import ListView
class CommitteePermissionListView(ListView):
    model = CommitteePermission
    template_name = 'dashboard/committee_permission_list.html'
    context_object_name = 'permissions'
    
    def get_queryset(self):
        # You might want to filter permissions based on some criteria
        return super().get_queryset().select_related('committee', 'member')

def create_committee_permission(request):
    if request.method == 'POST':
        form = CommitteePermissionForm(request.POST)
        if form.is_valid():
            permission = form.save()
            messages.success(request, f'Permissions for {permission.member} in {permission.committee} created successfully!')
            return redirect('committee_permissions:list')  # Adjust the redirect as needed
    else:
        form = CommitteePermissionForm()
    
    return render(request, 'dashboard/committee_permission_create.html', {'form': form})

def edit_committee_permission(request, pk):
    permission = get_object_or_404(CommitteePermission, pk=pk)
    
    if request.method == 'POST':
        form = CommitteePermissionForm(request.POST, instance=permission)
        if form.is_valid():
            permission = form.save()
            messages.success(request, f'Permissions for {permission.member} in {permission.committee} updated successfully!')
            return redirect('committee_permissions:list')  # Adjust the redirect as needed
    else:
        form = CommitteePermissionForm(instance=permission)
    
    return render(request, 'dashboard/committee_permission_edit.html', {'form': form, 'permission': permission})

def delete_committee_permission(request, pk):
    permission = get_object_or_404(CommitteePermission, pk=pk)
    if request.method == 'POST':
        permission.delete()
        messages.success(request, 'Permission deleted successfully!')
        return redirect('committee_permissions:list')  # Adjust the redirect as needed
    
    return render(request, 'dashboard/committee_permission_delete.html', {'permission': permission})

from .forms import AdminMembershipPaymentForm
from django.utils.translation import gettext_lazy as _

def admin_create_payment(request, profile_id=None):
    initial = {}
    
    if profile_id:
        try:
            profile = Profile.objects.get(id=profile_id)
            initial['profile'] = profile
            if profile.membership_type:
                initial['membership_type'] = profile.membership_type
                fee_structure = FeeStructure.objects.filter(
                    membership=profile.membership_type,
                    is_active=True
                ).first()
                if fee_structure:
                    initial['fee_structure'] = fee_structure
        except Profile.DoesNotExist:
            messages.warning(request, _('Member not found'))
    
    if request.method == 'POST':
        form = AdminMembershipPaymentForm(request.POST, request.FILES, initial=initial)
        if form.is_valid():
            payment = form.save()
            messages.success(request, _('Payment created successfully'))
            return redirect('user_dashboard')
    else:
        form = AdminMembershipPaymentForm(initial=initial)
    
    return render(request, 'dashboard/create_payment_member.html', {
        'form': form,
        'title': _('Create Payment')
    })

def get_fee_structures(request):
    membership_type_id = request.GET.get('membership_type_id')
    fee_structures = FeeStructure.objects.filter(
        membership_id=membership_type_id,
        is_active=True
    ).values('id', 'fee_name__name', 'amount', 'is_one_time')
    return JsonResponse(list(fee_structures), safe=False)

def get_profile_membership_type(request):
    profile_id = request.GET.get('profile_id')
    try:
        profile = Profile.objects.get(id=profile_id)
        if profile.membership_type:
            return JsonResponse({
                'membership_type_id': profile.membership_type.id,
                'membership_type_name': profile.membership_type.name
            })
    except Profile.DoesNotExist:
        pass
    return JsonResponse({'error': 'Profile not found'}, status=404)