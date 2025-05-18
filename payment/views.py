from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import MembershipPayment
from accounts.models import MembershipType
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from collections import defaultdict
from django.utils.timezone import now
from datetime import date, timedelta
import calendar
from django.http import JsonResponse
from django.http import HttpResponse
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import landscape, letter
from num2words import num2words


from .forms import MembershipPaymentForm, BankDetailFormSet, MobileBankingDetailFormSet, MobileBankingDetailForm, BankDetailForm, DateRangeForm, CommitteeDonationForm
from .models import MembershipPayment, BankDetail, MobileBankingDetail, DonationType
from club.models import Committee
from django.contrib import messages
from .models import BankDetail, MobileBankingDetail
from accounts.models import FeeStructure
from club.models import Club
from django.contrib.auth.decorators import login_required

def add_bank_details(request):
    if request.method == "POST":
        bank_formset = BankDetailFormSet(request.POST, prefix='bank')

        if bank_formset.is_valid():
            bank_formset.save()
            return redirect('payment_details_list')  # Redirect after saving

    else:
        bank_formset = BankDetailFormSet(queryset=BankDetail.objects.none(), prefix='bank')

    return render(request, 'payment/add_bank_details.html', {'bank_formset': bank_formset})

def add_mobile_banking_details(request):
    if request.method == "POST":
        mobile_formset = MobileBankingDetailFormSet(request.POST, prefix='mobile')

        if mobile_formset.is_valid():
            mobile_formset.save()
            return redirect('payment_details_list')  # Redirect after saving

    else:
        mobile_formset = MobileBankingDetailFormSet(queryset=MobileBankingDetail.objects.none(), prefix='mobile')

    return render(request, 'payment/add_mobile_banking_details.html', {'mobile_formset': mobile_formset})

def payment_details_list(request):
    # Fetch bank and mobile banking details
    bank_list = BankDetail.objects.all().order_by('-created_at')
    mobile_list = MobileBankingDetail.objects.all().order_by('-created_at')

    # Pagination (10 items per page)
    bank_paginator = Paginator(bank_list, 10)
    mobile_paginator = Paginator(mobile_list, 10)

    bank_page = request.GET.get('bank_page')
    mobile_page = request.GET.get('mobile_page')

    banks = bank_paginator.get_page(bank_page)
    mobiles = mobile_paginator.get_page(mobile_page)

    return render(request, 'payment/payment_details_list.html', {
        'banks': banks,
        'mobiles': mobiles
    })

# Edit Bank Detail
def edit_bank_detail(request, pk):
    bank = get_object_or_404(BankDetail, pk=pk)
    if request.method == "POST":
        form = BankDetailForm(request.POST, instance=bank)
        if form.is_valid():
            form.save()
            return redirect('payment_details_list')
    else:
        form = BankDetailForm(instance=bank)
    return render(request, 'edit_bank_detail.html', {'form': form})

def delete_bank_detail(request, bank_id):
    bank = get_object_or_404(BankDetail, id=bank_id)
    if request.method == 'POST':
        bank.delete()
        return redirect('bank_details')  # Or wherever you want to redirect
    return redirect('bank_details')

# Edit Mobile Banking Detail
def edit_mobile_banking_detail(request, pk):
    mobile = get_object_or_404(MobileBankingDetail, pk=pk)
    if request.method == "POST":
        form = MobileBankingDetailForm(request.POST, instance=mobile)
        if form.is_valid():
            form.save()
            return redirect('payment_details_list')
    else:
        form = MobileBankingDetailForm(instance=mobile)
    return render(request, 'edit_mobile_banking_detail.html', {'form': form})

def delete_mobile_banking_detail(request, mobile_id):
    mobile = get_object_or_404(MobileBankingDetail, id=mobile_id)
    if request.method == 'POST':
        mobile.delete()
        return redirect('mobile_banking_details')  # Or wherever you want to redirect
    return redirect('mobile_banking_details')


# @login_required
# def create_payment(request):
#     profile = request.user.profile  
#     membership_type = profile.membership_type  

#     # Get active FeeStructures for the logged-in user's membership type
#     fee_structures = FeeStructure.objects.filter(membership=membership_type, is_active=True)

#     # Exclude one-time fees already paid
#     paid_one_time_fees = MembershipPayment.objects.filter(
#         profile=profile,
#         fee_structure__is_one_time=True,
#         status="COMPLETED"
#     ).values_list("fee_structure_id", flat=True)

#     fee_structures = fee_structures.exclude(id__in=paid_one_time_fees)

#     # Get user registration month
#     registration_date = profile.user.date_joined
#     current_date = timezone.now()

#     # Generate month list from registration date to current month
#     month_dict = defaultdict(list)
#     temp_date = registration_date.replace(day=1)

#     while temp_date <= current_date:
#         month_dict[temp_date.year].append(temp_date.strftime("%B %Y"))
#         temp_date += timedelta(days=32)
#         temp_date = temp_date.replace(day=1)

#     # Get already paid months
#     paid_months = MembershipPayment.objects.filter(
#         profile=profile,
#         status="COMPLETED"
#     ).values_list("payment_month", flat=True)

#     paid_months = [p.strftime("%B %Y") for p in paid_months]

#     if request.method == "POST":
#         form = MembershipPaymentForm(request.POST, request.FILES)
        
#         if form.is_valid():
#             selected_month = form.cleaned_data["payment_month"]
#             payment = form.save(commit=False)
#             payment.profile = profile
#             payment.membership_type = membership_type
#             payment.fee_structure = fee_structures.first()
#             payment.payment_month = selected_month
#             payment.save()
#             return redirect('view_profile')
#     else:
#         form = MembershipPaymentForm()

#     return render(request, 'payment/create_payment.html', {
#         'form': form,
#         'profile': profile,
#         'membership_type': membership_type,
#         'fee_structures': fee_structures,
#         'month_dict': dict(month_dict),  # Pass months grouped by year
#         'paid_months': paid_months
#     })


def create_payment(request):
    profile = request.user.profile
    membership_type = profile.membership_type
    fee_structures = FeeStructure.objects.filter(membership=membership_type, is_active=True)
    bank_details = BankDetail.objects.filter(is_active=True)
    mobile_banking_details = MobileBankingDetail.objects.filter(is_active=True)

    today = timezone.now().date().replace(day=1)
    next_12_months = [(today + timedelta(days=30 * i)).strftime("%B %Y") for i in range(12)]

    paid_payments = MembershipPayment.objects.filter(profile=profile).values("fee_structure__id", "payment_months")
    
    paid_months = set()
    paid_fee_ids = set()

    for payment in paid_payments:
        if payment["payment_months"]:
            paid_months.update(payment["payment_months"].split(","))
        paid_fee_ids.add(payment["fee_structure__id"])

    if request.method == "POST":
        fee_structure_id = request.POST.get("fee_structure")
        selected_months = request.POST.getlist("payment_months")
        amount = float(request.POST.get("amount"))
        payment_method = request.POST.get("payment_method")

        if not fee_structure_id or not amount:
            messages.error(request, "Please fill all required fields!")
            return redirect("view_profile")

        try:
            fee_structure = FeeStructure.objects.get(id=fee_structure_id)
        except FeeStructure.DoesNotExist:
            messages.error(request, "Fee structure not found!")
            return redirect("view_profile")

        if fee_structure.is_one_time and fee_structure.id in paid_fee_ids:
            messages.error(request, "This one-time fee is already paid!")
            return redirect("view_profile")

        bank_details_selected = None
        mobile_banking_details_selected = None

        if payment_method == 'BANK_TRANSFER':
            bank_details_selected = BankDetail.objects.get(id=request.POST.get('bank_details'))
        elif payment_method == 'MOBILE_BANKING':
            mobile_banking_details_selected = MobileBankingDetail.objects.get(id=request.POST.get('mobile_banking_details'))

        try:
            payment = MembershipPayment.objects.create(
                profile=profile,
                membership_type=membership_type,
                fee_structure=fee_structure,
                amount=amount,
                payment_method=payment_method,
                bank_details=bank_details_selected,
                mobile_banking_details=mobile_banking_details_selected,
                transaction_id=request.POST.get("transaction_id"),
                proof_of_payment=request.FILES.get("proof_of_payment"),
                payment_months=",".join(selected_months),
            )
            messages.success(request, "Payment recorded successfully!")
            return redirect("view_profile")
        except Exception as e:
            messages.error(request, "There was an error while saving your payment. Please try again.")
            return redirect("view_profile")

    return render(request, "payment/create_payment.html", {
        "membership_type": membership_type,
        "fee_structures": fee_structures,
        "next_12_months": next_12_months,
        "paid_months": list(paid_months),
        "paid_fee_ids": paid_fee_ids,
        "bank_details": bank_details,
        "mobile_banking_details": mobile_banking_details,
    })

def get_bank_details(request, bank_id):
    bank = BankDetail.objects.get(id=bank_id)
    data = {
        'bank_name': bank.bank_name,
        'branch_name': bank.branch_name,
        'account_type': bank.account_type,
        'account_number': bank.account_number,
        'routing_number': bank.routing_number,
        'contact_number': bank.contact_number,
        'email_address': bank.email_address,
        'currencey': bank.currencey,

    }
    return JsonResponse(data)

def get_mobile_banking_details(request, mbnak_id):
    mobile_bank = MobileBankingDetail.objects.get(id=mbnak_id)
    data = {
        'mobile_banking_id': mobile_bank.mobile_bank_id,
        'banking_name': mobile_bank.banking_name,
        'mobile_number': mobile_bank.mobile_number,
        'personal_account': mobile_bank.personal_account,
        'merchant_account': mobile_bank.merchant_account,
        'instructions': mobile_bank.get_instructions()
        
    }
    return JsonResponse(data)


@login_required
def payment_history(request):
    # Get the logged-in user's profile
    profile = request.user.profile

    # Get all payments for the logged-in user's profile
    payments = MembershipPayment.objects.filter(profile=profile).order_by('-payment_date')  # Ordered by latest first

    return render(request, 'payment/payment_history.html', {
        'payments': payments,
    })

def convert_number_to_words(amount):
    """Convert a float amount to words like: Taka Three Lac Fifty Thousand Only"""
    words = num2words(amount, to='cardinal', lang='en_IN').replace(",", "").title()
    return f"Taka {words}"


def generate_payment_pdf(request, payment_id):
    club = Club.objects.first()
    if not club:
        return HttpResponse("Club not found.", status=404)

    payment = get_object_or_404(MembershipPayment, id=payment_id)
    if payment.status != "COMPLETED":
        return HttpResponse("Payment is not completed yet.", status=400)

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    left = 40
    right = width - 40
    top = height - 40

    # Header
    p.setFont("Helvetica-Bold", 13)
    p.setFillColor(colors.black)
    p.drawString(left, top, club.club_name)
    p.setFont("Helvetica", 10)
    p.drawString(left, top - 20, club.description)
    p.drawString(left, top - 35, f"Contact: {club.contact_name}")
    p.drawString(left, top - 50, f"Phone: {club.contact_phone}")
    p.setFillColor(colors.black)

    # Title
    p.setFillColor(colors.darkblue)
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, top - 65, "MONEY RECEIPT")
    p.setFillColor(colors.black)

    # Receipt Info
    p.setFont("Helvetica-Bold", 10)
    p.drawString(left, top - 90, f"No. #{payment.id:07}")
    p.drawString(right - 150, top - 90, f"Date: {payment.payment_date.strftime('%d-%b-%Y')}")

    # Main Content
    y = top - 120
    line_height = 22
    field_gap = 160
    dotted_line_x_end = right

    def draw_dotted_line(y_pos):
        p.setDash(1, 2)
        p.line(left + field_gap, y_pos - 2, dotted_line_x_end, y_pos - 2)
        p.setDash()

    def draw_label_and_value(label, value, y_pos):
        p.setFont("Helvetica-Bold", 10)
        p.drawString(left, y_pos, label)
        p.setFont("Helvetica", 10)
        p.drawString(left + field_gap, y_pos, str(value))
        draw_dotted_line(y_pos)

    # Amount line with In Word
    p.setFont("Helvetica-Bold", 10)
    p.drawString(left, y, "Receive with thanks a sum of Tk.")
    p.setFont("Helvetica", 10)
    amount_str = f"{payment.amount:.2f}"
    p.drawString(left + field_gap, y, amount_str)

    in_word_text = f"(Taka {convert_number_to_words(payment.amount)} Only)"
    p.drawString(left + field_gap + 150, y, "In Word: " + in_word_text)
    draw_dotted_line(y)
    y -= line_height

    # Other fields
    from_text = f"{payment.profile.membership_id} - {payment.profile.user.full_name}"
    draw_label_and_value("From", from_text, y)
    y -= line_height

    fee_structure_text = {payment.fee_structure.fee_name}
    draw_label_and_value("Fee Structure", fee_structure_text, y)
    y -= line_height

    payment_method_text = f"{payment.payment_method.replace('_', ' ').title()}  Deposit To: {payment.bank_details.bank_name if payment.bank_details else 'N/A'}"
    draw_label_and_value("Payment Method", payment_method_text, y)
    y -= line_height

    transaction_id = payment.transaction_id if payment.transaction_id else "N/A"
    draw_label_and_value("Transaction ID", transaction_id, y)
    y -= line_height

    remarks = payment.payment_notes if payment.payment_notes else "N/A"
    draw_label_and_value("Remarks", remarks, y)
    y -= line_height

    # Footer note
    y -= 20
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(left, y, "Note: The above cheque/PO/DD is valid subject to encashment")

    # Dotted bottom separator
    y -= 20
    p.setDash(3, 2)
    p.line(left, y, right, y)
    p.setDash()

    # Footer text below line
    y -= 20
    p.setFont("Helvetica", 8)
    p.drawString(left, y, "This is a computer-generated receipt and does not require a physical signature.")

    # Finalize PDF
    p.showPage()
    p.save()
    buffer.seek(0)

    return HttpResponse(buffer, content_type="application/pdf", headers={
        'Content-Disposition': f'attachment; filename="money_receipt_{payment.id}.pdf"'
    })

def generate_bank_statement_pdf(request):
    start_date_str = request.GET.get('start_date', '')
    end_date_str = request.GET.get('end_date', '')

    if not start_date_str or not end_date_str:
        return HttpResponse("Please provide both start and end dates.", status=400)

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        return HttpResponse("Invalid date format. Use YYYY-MM-DD.", status=400)

    payments = MembershipPayment.objects.filter(
        payment_date__gte=start_date,
        payment_date__lte=end_date,
        status="COMPLETED"
    )

    if not payments.exists():
        return HttpResponse("No payments found in this date range.", status=404)

    # Create the response PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="payment_statement_{start_date_str}_to_{end_date_str}.pdf"'

    # Build PDF
    doc = SimpleDocTemplate(response, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph("<b>Organization Name</b>", styles['Title']))
    elements.append(Paragraph("Payment Statement", styles['Heading2']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Member Name & ID:</b> { request.user.full_name } - {request.user.profile.membership_id} ", styles['Normal']))
    elements.append(Paragraph(f"<b>Membership Type:</b> { request.user.profile.membership_type }", styles['Normal']))
    elements.append(Paragraph(f"<b>Contact No:</b> { request.user.phone_number }", styles['Normal']))
    elements.append(Paragraph(f"<b>From Date:</b> {start_date.strftime('%d-%b-%y')} &nbsp;&nbsp; <b>To Date:</b> {end_date.strftime('%d-%b-%y')}", styles['Normal']))
    elements.append(Spacer(1, 12))

    # Table data
    data = [
        ["Sl", "Payment Date", "Payment Type", "Month", "Bank Name", "Account No", "Remarks", "Transaction No", "Amount"]
    ]

    total_amount = 0
    for idx, payment in enumerate(payments, start=1):
        bank_name = ''
        account_no = ''
        if payment.bank_details:
            bank_name = payment.bank_details.bank_name
            account_no = payment.bank_details.account_number
        elif payment.mobile_banking_details:
            bank_name = payment.mobile_banking_details.banking_name
            account_no = payment.mobile_banking_details.account_number

        data.append([
            idx,
            payment.payment_date.strftime('%d-%b-%y'),
            payment.fee_structure,
            payment.payment_months or '',
            bank_name,
            account_no,
            payment.payment_notes or '',
            payment.transaction_id,
            f"{payment.amount:,.2f}"
        ])
        total_amount += payment.amount

    # Add total row
    data.append(['', '', '', '', '', '', '', 'Total', f"{total_amount:,.2f}"])

    # Create table
    table = Table(data, repeatRows=1, hAlign='LEFT')

    # Styling
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
        ('BACKGROUND', (-2, -1), (-1, -1), colors.lightgrey),
        ('SPAN', (0, -1), (-3, -1)),  # Span from column 0 to -3 in total row
        ('ALIGN', (-1, -1), (-1, -1), 'RIGHT'),
    ]))

    doc = SimpleDocTemplate(response, pagesize=landscape(letter))

    # Set column widths (in points: 1 inch = 72 points)
    col_widths = [
        30,   # Sl
        70,   # Payment Date
        90,   # Payment Type
        80,   # Month
        100,  # Bank Name
        80,   # Account No
        100,  # Remarks
        90,   # Transaction No
        70,   # Amount
    ]

    table = Table(data, repeatRows=1, hAlign='LEFT', colWidths=col_widths)

    elements.append(table)

    # Build the PDF
    doc.build(elements)
    return response

def generate_payment_report(request):
    """Render the form for entering start and end date"""
    
    if request.method == 'POST':
        form = DateRangeForm(request.POST)
        if form.is_valid():
            # Extract the start and end dates from the form
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            
            # Build the URL with query parameters
            url = reverse('generate_bank_statement')  # Use the named URL without parameters
            url += f'?start_date={start_date.strftime("%Y-%m-%d")}&end_date={end_date.strftime("%Y-%m-%d")}'
            
            # Redirect to the generated URL
            return HttpResponseRedirect(url)
    else:
        form = DateRangeForm()

    return render(request, 'payment/generate_report_form.html', {'form': form})


# def donate_to_committee(request, committee_id):
#     committee = get_object_or_404(Committee, id=committee_id)
#     form = CommitteeDonationForm(request.POST or None)

#     context = {
#         'form': form,
#         'committee': committee,
#         'banks': BankDetail.objects.filter(is_active=True),
#         'mobile_accounts': MobileBankingDetail.objects.filter(is_active=True),
#     }
    
#     if form.is_valid():
#         donation = form.save(commit=False)
#         donation.committee = committee
#         donation.donor = request.user
#         donation.save()

#     return render(request, 'payment/donate_form.html', context)
from django.views.decorators.http import require_GET

@require_GET
def get_donation_type_fields(request):
    type_id = request.GET.get('type_id')
    try:
        donation_type = DonationType.objects.get(id=type_id)
        return JsonResponse({
            'amount': donation_type.amount,
            'quantity': donation_type.quantity,
            'quantity_unit': donation_type.quantity_unit,
            'show_payment': any([
                donation_type.bank_detail,
                donation_type.mobile_banking_detail,
                donation_type.payment_method,
                donation_type.transaction_id,
                donation_type.proof_of_payment
            ]),
            'show_payment_method': donation_type.payment_method,
            'show_bank_detail': donation_type.bank_detail,
            'show_mobile_banking': donation_type.mobile_banking_detail,
            'show_transaction_id': donation_type.transaction_id,
            'show_proof_of_payment': donation_type.proof_of_payment,
        })
    except DonationType.DoesNotExist:
        return JsonResponse({'error': 'Invalid donation type'}, status=400)

def create_donation(request, committee_id):
    committee = get_object_or_404(Committee, id=committee_id)

    if request.method == 'POST':
        form = CommitteeDonationForm(request.POST, request.FILES, committee=committee, request=request)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.committee = committee

            # Set user info if logged in
            if request.user.is_authenticated:
                donation.donor = request.user
                donation.is_member = True
                donation.name = request.user.get_full_name()
                donation.email = request.user.email
                donation.phone = getattr(request.user, 'phone_number', '')

                if hasattr(request.user, 'profile'):
                    donation.address = request.user.profile.present_address

                # Track who created and updated
                donation.created_by = request.user

            # Clean up based on donation type
            donation_type = donation.donation_type

            if donation_type:
                # Optional cleanup: unset unrelated fields based on what the type supports
                if not donation.amount:
                    donation.amount = None
                if not donation.quantity:
                    donation.quantity = None
                if not donation.quantity_unit:
                    donation.quantity_unit = None
                if not donation.payment_method or donation.payment_method == '----':
                    donation.payment_method = '----'
                if not donation.bank_detail:
                    donation.bank_detail = None
                if not donation.mobile_banking_detail:
                    donation.mobile_banking_detail = None
                if not donation.transaction_id:
                    donation.transaction_id = ''
                if not donation.proof_of_payment:
                    donation.proof_of_payment = None
            else:
                # No donation type — clear optional fields
                donation.amount = None
                donation.quantity = None
                donation.quantity_unit = None
                donation.payment_method = '----'
                donation.bank_detail = None
                donation.mobile_banking_detail = None
                donation.transaction_id = ''
                donation.proof_of_payment = None

            donation.save()

            messages.success(request, 'Donation submitted successfully!')
            return redirect('committee_detail', committee.id)

    else:
        form = CommitteeDonationForm(committee=committee, request=request)

    return render(request, 'payment/create_donation.html', {
        'form': form,
        'committee': committee,
        'user_authenticated': request.user.is_authenticated
    })