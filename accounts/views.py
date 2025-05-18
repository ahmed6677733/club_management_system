from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.http import JsonResponse
import hashlib
import uuid
from django.db import models
from django.db.models import Sum


from .forms import MemberForm, FamilyMemberForm, UserForm, RoleChangeRequestForm, UpdateUserForm, UpdateMemberForm
from .models import Profile, MembershipType, User, FamilyMember, RoleChangeRequest
from club.models import Committee, CommitteeExpense, CommitteeMember
from payment.models import CommitteeDonation
from django.db.models import Sum, OuterRef, Subquery, Value, DecimalField, ExpressionWrapper, F
from django.db.models.functions import Coalesce


def membership_registration(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        member_form = MemberForm(request.POST)

        if user_form.is_valid() and member_form.is_valid():
            # Create the User (username will be auto-generated)
            user = user_form.save(commit=False)
            user.role = 'Member'
            user.save()  # Verification token will be generated automatically

            # Manually assign user to the member and save
            member = member_form.save(user=user)

            # Send email verification
            verification_url = request.build_absolute_uri(f"/accounts/verify-email/{user.verification_token}/")
            email_subject = "Please verify your email address"
            
            # Include membership_id in the email context
            email_body = render_to_string(
                'accounts/email_confirmation.html', 
                {'user': user, 'verification_url': verification_url, 'membership_id': member.membership_id}
            )

            send_mail(
                email_subject,
                "",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=email_body
            )

            # Log the user in
            login(request, user)

            messages.success(request, 'Registration successful! Please verify your email to activate your account.')
            return redirect('/')  # Redirect to member dashboard

    else:
        user_form = UserForm()
        member_form = MemberForm()

    return render(request, 'accounts/membership_register.html', {'user_form': user_form, 'member_form': member_form})



def user_login(request):
    """Custom login view for Members and Family Members using Membership ID."""
    if request.method == 'POST':
        membership_id = request.POST['membership_id']
        password = request.POST['password']
        
        user = None
        family_member = None  # Initialize the family_member variable

        try:
            # Check if the membership ID belongs to a Member
            member = Profile.objects.get(membership_id=membership_id)
            user = member.user  # Get the associated User object

        except Profile.DoesNotExist:
            try:
                # If not found, check if it's a FamilyMember
                family_member = FamilyMember.objects.get(membership_id=membership_id)
                user = family_member.user  # Get the associated User object
            except FamilyMember.DoesNotExist:
                messages.error(request, 'Invalid Membership ID. Please try again.')
                return redirect('login')  # Redirect to login if membership ID doesn't exist

        # Authenticate user using username & password
        if user:
            user = authenticate(request, username=user.username, password=password)

            if user is not None:
                login(request, user)  # Log the user in

                # Check if email is verified
                if not user.is_email_verified:
                    messages.warning(request, 'Please verify your email to activate your account.')

                # Redirect based on the role
                if family_member:  # If family_member exists, redirect to family member dashboard
                    return redirect('family_member_dashboard')
                elif user.role == 'Admin':
                    return redirect('dashboard')  # Redirect to admin panel
                elif user.role == 'Member':
                    return redirect('/')  # Redirect to member dashboard
                elif user.role == 'Volunteer':
                    return redirect('volunteer_dashboard')  # Redirect to volunteer dashboard
                else:
                    messages.error(request, 'Unknown role')
                    return redirect('login')  # Default to login if role is not found
            else:
                messages.error(request, 'Invalid credentials. Please try again.')
                return redirect('login')  # Redirect to login if authentication fails

    return render(request, 'accounts/login.html')  # Render login template



def user_logout(request):
    """Logs out the user and redirects to the login page."""
    logout(request)
    return redirect('login')

@login_required
def create_family_member(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES)
        family_form = FamilyMemberForm(request.POST)
        
        if user_form.is_valid() and family_form.is_valid():
            # Save the user first
            user = user_form.save(commit=False)
            user.role = User.MEMBER  # Set role to Member
            user.save()
            
            # Save the family member linked to this user
            family_member = family_form.save(commit=False)
            family_member.user = user
            family_member.is_existing_member = False  # Since we're creating new
            family_member.save()
            
            messages.success(request, 'Member created successfully!')
            return redirect('view_profile')  # Replace with your URL name
            
    else:
        user_form = UserForm()
        family_form = FamilyMemberForm()
    
    context = {
        'user_form': user_form,
        'family_form': family_form,
    }
    return render(request, 'accounts/create_family_member.html', context)

# @login_required
# def create_family_member(request):
#     if request.method == 'POST':
#         form = FamilyMemberForm(request.POST)
#         if form.is_valid():
#             family_member = form.save(commit=False)
#             family_member.user = request.user
#             family_member.save()
#             return redirect('family_member_success')  # Change to your desired URL
#     else:
#         form = FamilyMemberForm()
#     return render(request, 'accounts/create_family_member.html', {'form': form})

def search_members(request):
    query = request.GET.get('query', '')
    if query:
        # Search by membership_id or full_name
        members = Profile.objects.filter(
            models.Q(membership_id__icontains=query) |
            models.Q(user__full_name__icontains=query)  # Assuming Member has a OneToOne link to User
        )
        member_data = [{
            'id': member.id,
            'membership_id': member.membership_id,
            'full_name': member.user.full_name  # Use the correct field from User
        } for member in members]
        return JsonResponse({'members': member_data})
    return JsonResponse({'members': []})

def register_admin(request):
    """Register an Admin user with linked Member profile."""
    if request.method == "POST":
        user_form = UserForm(request.POST)
        member_form = MemberForm(request.POST)

        if user_form.is_valid() and member_form.is_valid():
            user = user_form.save(commit=False)
            user.role = User.ADMIN  # Assign 'Admin' role
            user.save()  # Save the user

            member_form.save(user=user)  # Create linked Member profile

            messages.success(request, "Admin registered successfully!")
            # Send email verification
            verification_url = request.build_absolute_uri(f"/accounts/verify-email/{user.verification_token}/")
            email_subject = "Please verify your email address"
            email_body = render_to_string(
                'accounts/email_confirmation.html', 
                {'user': user, 'verification_url': verification_url}
            )

            send_mail(
                email_subject,
                "",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=email_body
            )

            return redirect("/")  # Redirect to home page

    else:
        user_form = UserForm()
        member_form = MemberForm()

    return render(request, "accounts/register_admin.html", {
        "user_form": user_form,
        "member_form": member_form,
        "role_display": "Admin"
    })

def register_volunteer(request):
    """Register a Volunteer user with linked Member profile."""
    if request.method == "POST":
        user_form = UserForm(request.POST)
        member_form = MemberForm(request.POST)

        if user_form.is_valid() and member_form.is_valid():
            user = user_form.save(commit=False)
            user.role = User.VOLUNTEER  # Assign 'Volunteer' role
            user.save()  # Save the user

            member_form.save(user=user)  # Create linked Member profile

            messages.success(request, "Volunteer registered successfully!")
            # Send email verification
            verification_url = request.build_absolute_uri(f"/accounts/verify-email/{user.verification_token}/")
            email_subject = "Please verify your email address"
            email_body = render_to_string(
                'accounts/email_confirmation.html', 
                {'user': user, 'verification_url': verification_url}
            )

            send_mail(
                email_subject,
                "",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=email_body
            )
            return redirect("/")  # Redirect to home page

    else:
        user_form = UserForm()
        member_form = MemberForm()

    return render(request, "accounts/register_volunteer.html", {
        "user_form": user_form,
        "member_form": member_form,
        "role_display": "Volunteer"
    })

@login_required
def request_role_change(request):
    """Allows users to submit a role change request."""
    if request.method == "POST":
        form = RoleChangeRequestForm(request.POST)
        if form.is_valid():
            role_request = form.save(commit=False)
            role_request.user = request.user  # Assign the current user
            role_request.current_role = request.user.role
            role_request.save()
            messages.success(request, "Your role change request has been submitted.")
            return redirect('home')  # Redirect to home or another page
    else:
        form = RoleChangeRequestForm()

    return render(request, "accounts/request_role_change.html", {"form": form})

@login_required
def view_profile(request):
    """View to display user's profile, including User and Profile details."""
    # Get the user object (logged in user)
    user = request.user
    # Get the associated Profile object
    profile = get_object_or_404(Profile, user=user)

    return render(request, 'accounts/view_profile.html', {
        'user': user,
        'profile': profile,
        'is_membership_approved': profile.is_approved == True
    })

@login_required
def update_profile(request):
    user = request.user  # Get the currently logged-in user
    profile, created = Profile.objects.get_or_create(user=user) # Get or create profile

    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, request.FILES, instance=user)  # Add request.FILES
        member_form = UpdateMemberForm(request.POST, instance=profile)

        if user_form.is_valid() and member_form.is_valid():
            user_form.save()
            member_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('view_profile')  # Redirect to the profile view

    else:
        user_form = UpdateUserForm(instance=user)
        member_form = UpdateMemberForm(instance=profile)

    return render(request, 'accounts/update_profile.html', {
        'user_form': user_form,
        'member_form': member_form,
    })


def verify_email(request, token):
    try:
        # The token is a UUID, so we need to handle it properly
        user = User.objects.get(verification_token=token)

        # If user exists, activate the account and mark the email as verified
        if user:
            user.is_email_verified = True
            user.verification_token = None  # Clear the verification token after successful verification
            user.save()

            messages.success(request, "Your email has been successfully verified! You can now log in.")
            return redirect('login')  # Redirect to login page
    except User.DoesNotExist:
        messages.error(request, "Invalid verification link or token.")
        return redirect('home')  # Redirect to home page
    
def family_member_dashboard(request):
    try:
        family_member = FamilyMember.objects.get(user=request.user)
        primary_member = family_member.primary_member  # Get associated primary member
    except FamilyMember.DoesNotExist:
        context = {
            'no_family_members': True,
        }
        return render(request, 'accounts/family_member_dashboard.html', context)

    # Get all family members under the same primary member
    family_members = FamilyMember.objects.filter(primary_member=primary_member)

    context = {
        'family_member': family_member,  # The logged-in family member
        'primary_member': primary_member,  # The primary member they are linked to
        'family_members': family_members,  # Other family members of the primary member
        'no_family_members': False,
    }
    
    return render(request, 'accounts/family_member_dashboard.html', context)


def family_member_profile(request):
    # Ensure the user is logged in
    if not request.user.is_authenticated:
        return redirect('login')  # Redirect to the login page if not authenticated

    # Check if the logged-in user has a FamilyMember profile
    try:
        family_member = FamilyMember.objects.get(user=request.user)
    except FamilyMember.DoesNotExist:
        return redirect('home')  # Redirect to home or another page if the user is not a family member

    context = {
        'family_member': family_member,
        'user': family_member.user,  # Add the related user object
    }

    return render(request, 'accounts/family_member_profile.html', context)


@login_required
def view_profile_admin(request):
    """View to display user's profile, including User and Profile details."""
    # Get the user object (logged in user)
    user = request.user
    # Get the associated Profile object
    profile = get_object_or_404(Profile, user=user)

    return render(request, 'accounts/view_profile_admin.html', {
        'user': user,
        'profile': profile,
        'is_membership_approved': profile.is_approved == True
    })

@login_required
def update_profile_admin(request):
    user = request.user  # Get the currently logged-in user
    profile, created = Profile.objects.get_or_create(user=user) # Get or create profile

    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, request.FILES, instance=user)  # Add request.FILES
        member_form = UpdateMemberForm(request.POST, instance=profile)

        if user_form.is_valid() and member_form.is_valid():
            user_form.save()
            member_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('view_profile_dashboard')  # Redirect to the profile view

    else:
        user_form = UpdateUserForm(instance=user)
        member_form = UpdateMemberForm(instance=profile)

    return render(request, 'accounts/update_profile_admin.html', {
        'user_form': user_form,
        'member_form': member_form,
    })

def committee_list(request):
    expense_subquery = CommitteeExpense.objects.filter(
        committee=OuterRef('pk')
    ).values('committee').annotate(
        total=Sum('amount')
    ).values('total')

    donation_subquery = CommitteeDonation.objects.filter(
        committee=OuterRef('pk')
    ).values('committee').annotate(
        total=Sum('amount')
    ).values('total')

    committees = Committee.objects.annotate(
        total_expense=Coalesce(Subquery(expense_subquery), Value(0, output_field=DecimalField())),
        total_donation=Coalesce(Subquery(donation_subquery), Value(0, output_field=DecimalField())),
    ).annotate(
        balance=ExpressionWrapper(
            F('total_donation') - F('total_expense'),
            output_field=DecimalField()
        )
    )

    return render(request, 'accounts/committee_list.html', {
        'committees': committees,
    })

from club.models import CommitteePermission

def committee_detail_view(request, committee_id):
    committee = get_object_or_404(Committee, id=committee_id)
    
    # Get all expenses and donations
    expenses = CommitteeExpense.objects.filter(committee=committee).select_related(
        'members__member__user', 
        'expense_type', 
        'donation_type'
    )
    donations = CommitteeDonation.objects.filter(committee=committee).select_related(
        'donation_type'
    )
    designations = CommitteeMember.objects.filter(committee=committee).select_related(
        'member__user'
    ).prefetch_related('activities')

    # Calculate totals
    total_expense = expenses.aggregate(total=Sum('amount'))['total'] or 0
    total_donation = donations.aggregate(total=Sum('amount'))['total'] or 0
    balance = total_donation - total_expense

    # Initialize user permissions
    user_permissions = {
        'can_create_expense': False,
        'can_approve_expense': False,
        'can_reject_expense': False,
        'can_create_donation': True,  # Anyone can create donations
        'can_approve_donation': False,
        'can_reject_donation': False,
        'is_committee_member': False,
    }

    # Check if user is a committee member and get permissions
    if request.user.is_authenticated:
        try:
            member = CommitteeMember.objects.get(
                committee=committee, 
                member__user=request.user
            )
            user_permissions['is_committee_member'] = True
            
            # Get permissions if they exist
            try:
                permission = CommitteePermission.objects.get(
                    committee=committee, 
                    member=member
                )
                user_permissions.update({
                    'can_approve_expense': permission.can_approve_expense,
                    'can_reject_expense': permission.can_reject_expense,
                    'can_approve_donation': permission.can_approve_donation,
                    'can_reject_donation': permission.can_reject_donation,
                })
            except CommitteePermission.DoesNotExist:
                pass
                
        except CommitteeMember.DoesNotExist:
            pass

    context = {
        'committee': committee,
        'expenses': expenses,
        'donations': donations,
        'designations': designations,
        'total_expense': total_expense,
        'total_donation': total_donation,
        'balance': balance,
        'user_permissions': user_permissions,
    }
    
    return render(request, 'accounts/committee_detail.html', context)

@login_required
def approve_expense(request, expense_id):
    expense = get_object_or_404(CommitteeExpense, id=expense_id)
    
    # Check if user has permission to approve
    try:
        member = CommitteeMember.objects.get(
            committee=expense.committee, 
            member__user=request.user
        )
        permission = CommitteePermission.objects.get(
            committee=expense.committee, 
            member=member
        )
        if not permission.can_approve_expense:
            messages.error(request, "You don't have permission to approve expenses.")
            return redirect('committee_detail', committee_id=expense.committee.id)
            
    except (CommitteeMember.DoesNotExist, CommitteePermission.DoesNotExist):
        messages.error(request, "You don't have permission to approve expenses.")
        return redirect('committee_detail', committee_id=expense.committee.id)
    
    # Approve the expense
    expense.status = 'approved'
    expense.approved_by = request.user
    expense.save()
    
    messages.success(request, f"Expense '{expense.title}' has been approved.")
    return redirect('committee_detail', committee_id=expense.committee.id)

@login_required
def reject_expense(request, expense_id):
    expense = get_object_or_404(CommitteeExpense, id=expense_id)
    
    # Check if user has permission to reject
    try:
        member = CommitteeMember.objects.get(
            committee=expense.committee, 
            member__user=request.user
        )
        permission = CommitteePermission.objects.get(
            committee=expense.committee, 
            member=member
        )
        if not permission.can_reject_expense:
            messages.error(request, "You don't have permission to reject expenses.")
            return redirect('committee_detail', committee_id=expense.committee.id)
            
    except (CommitteeMember.DoesNotExist, CommitteePermission.DoesNotExist):
        messages.error(request, "You don't have permission to reject expenses.")
        return redirect('committee_detail', committee_id=expense.committee.id)
    
    # Reject the expense
    expense.status = 'rejected'
    expense.approved_by = request.user
    expense.save()
    
    messages.success(request, f"Expense '{expense.title}' has been rejected.")
    return redirect('committee_detail', committee_id=expense.committee.id)

@login_required
def approve_donation(request, donation_id):
    donation = get_object_or_404(CommitteeDonation, id=donation_id)
    
    # Check if user has permission to approve donations
    try:
        member = CommitteeMember.objects.get(
            committee=donation.committee, 
            member__user=request.user
        )
        permission = CommitteePermission.objects.get(
            committee=donation.committee, 
            member=member
        )
        if not permission.can_approve_donation:
            messages.error(request, "You don't have permission to approve donations.")
            return redirect('committee_detail', committee_id=donation.committee.id)
            
    except (CommitteeMember.DoesNotExist, CommitteePermission.DoesNotExist):
        messages.error(request, "You don't have permission to approve donations.")
        return redirect('committee_detail', committee_id=donation.committee.id)
    
    # Approve the donation
    donation.status = 'approved'
    donation.approved_by = request.user
    donation.save()
    
    messages.success(request, f"Donation from '{donation.name or 'Anonymous'}' has been approved.")
    return redirect('committee_detail', committee_id=donation.committee.id)

@login_required
def reject_donation(request, donation_id):
    donation = get_object_or_404(CommitteeDonation, id=donation_id)
    
    # Check if user has permission to reject donations
    try:
        member = CommitteeMember.objects.get(
            committee=donation.committee, 
            member__user=request.user
        )
        permission = CommitteePermission.objects.get(
            committee=donation.committee, 
            member=member
        )
        if not permission.can_reject_donation:
            messages.error(request, "You don't have permission to reject donations.")
            return redirect('committee_detail', committee_id=donation.committee.id)
            
    except (CommitteeMember.DoesNotExist, CommitteePermission.DoesNotExist):
        messages.error(request, "You don't have permission to reject donations.")
        return redirect('committee_detail', committee_id=donation.committee.id)
    
    # Reject the donation
    donation.status = 'rejected'
    donation.approved_by = request.user
    donation.save()
    
    messages.success(request, f"Donation from '{donation.name or 'Anonymous'}' has been rejected.")
    return redirect('committee_detail', committee_id=donation.committee.id)