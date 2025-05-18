from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from accounts.models import User, Team

from .models import Club, CommitteeTask, CommitteeTaskAssignment, OrganizationRegistrationInfo, CommitteeExpense, Committee
from .forms import ClubForm, OrganizationRegistrationForm, CommitteeExpenseForm

from payment.models import CommitteeDonation, DonationType

from django.db.models import Sum, Count
from django.http import HttpResponseForbidden, HttpResponseNotFound
import csv
from datetime import datetime
from django.http import HttpResponse



def club_registration(request):
    """View to handle club registration"""
    if Club.objects.exists():
        return redirect('/')  # Redirect back if a club already exists

    if request.method == 'POST':
        form = ClubForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')  # After registration, redirect to home
    else:
        form = ClubForm()

    return render(request, 'club/club_registration.html', {'form': form})

def edit_club(request):
    club = get_object_or_404(Club)
    
    if request.method == "POST":
        form = ClubForm(request.POST, request.FILES, instance=club)
        if form.is_valid():
            form.save()
            return redirect('club_profile')  # Redirect to a detail or success page
    else:
        form = ClubForm(instance=club)

    return render(request, 'club/edit_club.html', {'form': form})

from django.http import HttpResponseForbidden
from .models import Committee, CommitteeMember, CommitteeExpense
from .forms import CommitteeExpenseForm

def add_committee_expense(request, committee_id):
    committee = get_object_or_404(Committee, id=committee_id)

    try:
        committee_member = CommitteeMember.objects.get(
            member=request.user.profile,
            committee=committee,
            is_active=True
        )
    except CommitteeMember.DoesNotExist:
        return HttpResponseForbidden("You are not an active member of this committee.")

    donation_type = None

    if request.method == 'POST':
        form = CommitteeExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            donation_type = form.cleaned_data['donation_type']
            expense = form.save(commit=False)
            expense.members = committee_member
            expense.committee = committee

            # Clear non-permitted fields
            if not donation_type.amount:
                expense.amount = None
            if not donation_type.quantity:
                expense.quantity = None
            if not donation_type.quantity_unit:
                expense.quantity_unit = None
            if not donation_type.bank_detail:
                expense.bank_detail = None
            if not donation_type.mobile_banking_detail:
                expense.mobile_banking_detail = None
            if not donation_type.payment_method:
                expense.payment_method = None
            if not donation_type.transaction_id:
                expense.transaction_id = None
            if not donation_type.proof_of_payment:
                expense.proof_of_payment = None

            expense.save()
            return redirect('committee_detail', committee.id)
        else:
            donation_type = form.cleaned_data.get('donation_type') or None
    else:
        # 🔧 Handle GET: Keep donation_type preselected
        donation_type_id = request.GET.get('donation_type')
        if donation_type_id:
            donation_type = DonationType.objects.filter(id=donation_type_id).first()
            form = CommitteeExpenseForm(initial={'donation_type': donation_type})
        else:
            form = CommitteeExpenseForm()

    # 🔁 Dynamically remove fields based on selected donation type
    if donation_type:
        if not donation_type.amount:
            form.fields.pop('amount', None)
        if not donation_type.quantity:
            form.fields.pop('quantity', None)
        if not donation_type.quantity_unit:
            form.fields.pop('quantity_unit', None)
        if not donation_type.bank_detail:
            form.fields.pop('bank_detail', None)
        if not donation_type.mobile_banking_detail:
            form.fields.pop('mobile_banking_detail', None)
        if not donation_type.payment_method:
            form.fields.pop('payment_method', None)
        if not donation_type.transaction_id:
            form.fields.pop('transaction_id', None)
        if not donation_type.proof_of_payment:
            form.fields.pop('proof_of_payment', None)

    return render(request, 'club/committee_expense_form.html', {
        'form': form,
        'committee': committee,
    })


def committee_expense_list(request):
    expenses = CommitteeExpense.objects.all()
    return render(request, 'club/committee_expense_list.html', {'expenses': expenses})

from decimal import Decimal

def committee_report(request, committee_id):
    committee = get_object_or_404(Committee, id=committee_id)

    # Get filter values
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    expenses = CommitteeExpense.objects.filter(committee=committee)
    donations = CommitteeDonation.objects.filter(committee=committee)

    # Apply filters
    if start_date:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        expenses = expenses.filter(expense_date__gte=start_date_obj)
        donations = donations.filter(donation_date__gte=start_date_obj)
    if end_date:
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        expenses = expenses.filter(expense_date__lte=end_date_obj)
        donations = donations.filter(donation_date__lte=end_date_obj)

    # Sum safely
    total_expenses = sum(exp.amount or Decimal('0.00') for exp in expenses)
    total_donations = sum(d.amount or Decimal('0.00') for d in donations)

    # CSV download
    if request.GET.get('download') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="committee_{committee_id}_report.csv"'
        writer = csv.writer(response)

        # Summary
        writer.writerow(['Committee Report'])
        writer.writerow(['Committee:', committee.name])
        writer.writerow(['Start Date:', start_date or 'N/A'])
        writer.writerow(['End Date:', end_date or 'N/A'])
        writer.writerow([])

        # Expenses Section
        writer.writerow(['Expenses'])
        writer.writerow([
            'Title', 'Type', 'Amount', 'Quantity', 'Unit',
            'Description', 'Member', 'Payment Method',
            'Bank / Mobile Provider', 'Transaction ID',
            'Notes', 'Date'
        ])
        for exp in expenses:
            writer.writerow([
                exp.title,
                str(exp.expense_type),
                exp.amount or '0.00',
                exp.quantity or '-',
                str(exp.quantity_unit) if exp.quantity_unit else '-',
                exp.description or '-',
                str(exp.members),
                exp.payment_method or '-',
                exp.bank_detail.bank_name if exp.bank_detail else (
                    exp.mobile_banking_detail.provider_name if exp.mobile_banking_detail else '-'
                ),
                exp.transaction_id or '-',
                exp.expense_notes or '-',
                exp.expense_date
            ])
        writer.writerow(['Total Expenses:', total_expenses])
        writer.writerow([])

        # Donations Section
        writer.writerow(['Donations'])
        writer.writerow([
            'Name', 'Email', 'Phone', 'Address', 'Type',
            'Amount', 'Quantity', 'Unit', 'Method',
            'Bank / Mobile Provider', 'Transaction ID',
            'Proof Link', 'Status', 'Notes', 'Date'
        ])
        for d in donations:
            proof_url = d.proof_of_payment.url if d.proof_of_payment else '-'
            writer.writerow([
                d.name or 'Anonymous',
                d.email or '-',
                d.phone or '-',
                d.address or '-',
                str(d.donation_type) if d.donation_type else '-',
                d.amount or '0.00',
                d.quantity or '-',
                str(d.quantity_unit) if d.quantity_unit else '-',
                d.payment_method or '-',
                d.bank_detail.bank_name if d.bank_detail else (
                    d.mobile_banking_detail.provider_name if d.mobile_banking_detail else '-'
                ),
                d.transaction_id or '-',
                proof_url,
                d.status,
                d.donattion_notes or '-',
                d.donation_date
            ])
        writer.writerow(['Total Donations:', total_donations])
        return response

    # Render to template
    context = {
        'committee': committee,
        'expenses': expenses,
        'donations': donations,
        'total_expenses': total_expenses,
        'total_donations': total_donations,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'club/committee_report.html', context)