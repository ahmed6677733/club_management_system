from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    path('membership-registration/', views.membership_registration, name='membership_registration'),
    path("register/admin/", views.register_admin, name="register_admin"),
    path("register/volunteer/", views.register_volunteer, name="register_volunteer"),

    path('create-family-member/', views.create_family_member, name='create_family_member'),
    path('search-members/', views.search_members, name='search_members'),

    path('request-role-change/', views.request_role_change, name='request_role_change'),
    path('profile/', views.view_profile, name='view_profile'),
    path('update-profile/', views.update_profile, name='update_profile'),

    path('dashboard/profile/', views.view_profile_admin, name='view_profile_dashboard'),
    path('dashboard/profile/update-profile/', views.update_profile_admin, name='update_profile_dashboard'),

    path('verify-email/<str:token>/', views.verify_email, name='verify_email'), # type: ignore

    path('family-member/dashboard/', views.family_member_dashboard, name='family_member_dashboard'),
    path('family-member/profile/', views.family_member_profile, name='family_member_profile'),

    path('committees/', views.committee_list, name='committees'),
    path('committees/<int:committee_id>/', views.committee_detail_view, name='committee_detail'),

    path('expense/<int:expense_id>/approve/', views.approve_expense, name='approve_expense'),
    path('expense/<int:expense_id>/reject/', views.reject_expense, name='reject_expense'),
    path('donation/<int:donation_id>/approve/', views.approve_donation, name='approve_donation'),
    path('donation/<int:donation_id>/reject/', views.reject_donation, name='reject_donation'),
]
