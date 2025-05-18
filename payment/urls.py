from django.urls import path
from . import views


urlpatterns = [
    path('add-bank-details/', views.add_bank_details, name='add_bank_detail'),
    path('add-mobile-banking-details/', views.add_mobile_banking_details, name='add_mobile_banking_detail'),
    path('payment-details/', views.payment_details_list, name='payment_details_list'),
    path('edit-bank/<int:pk>/', views.edit_bank_detail, name='edit_bank_detail'),
    path('delete-bank/<int:pk>/', views.delete_bank_detail, name='delete_bank_detail'),
    path('edit-mobile/<int:pk>/', views.edit_mobile_banking_detail, name='edit_mobile_banking_detail'),
    path('delete-mobile/<int:pk>/', views.delete_mobile_banking_detail, name='delete_mobile_banking_detail'),

    path('add-mobile-banking-details/', views.add_mobile_banking_details, name='add_mobile_banking_details'),\
    
    path('create-payment/', views.create_payment, name='create_payment'),
    path('get-bank-details/<int:bank_id>/', views.get_bank_details, name='get_bank_details'),
    path('get_mobile_banking_details/<int:mbank_id>/', views.get_mobile_banking_details, name='get_mobile_banking_details'),
    path('payment-history/', views.payment_history, name='payment_history'),
    path("payment-receipt/<int:payment_id>/", views.generate_payment_pdf, name="payment_receipt"),
    path('generate-bank-statement/', views.generate_bank_statement_pdf, name='generate_bank_statement'),
    path('generate-payment-report/', views.generate_payment_report, name='generate_payment_report'),

    path('donate/<int:committee_id>/', views.create_donation, name='create_donation'),
    path('donations/get-donation-type-fields/', views.get_donation_type_fields, name='get_donation_type_fields'),
]