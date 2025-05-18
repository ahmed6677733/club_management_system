from django.urls import path
from . import views
from .views import CommitteePermissionListView


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('get-dashboard-data/', views.get_dashboard_data, name='get_dashboard_data'),
    path('profile/', views.club_profile, name='club_profile'),

    path('role-change-request-list/', views.role_change_request_list, name='role_change_request_list'),
    path('approve-role-change/<int:request_id>/', views.approve_role_change, name='approve_role_change'),
    path('reject-role-change/<int:request_id>/', views.reject_role_change, name='reject_role_change'),

    path('membership-applications/', views.membership_applications, name='membership_applications'),
    path('approve/<int:profile_id>/', views.approve_membership, name='approve_membership'),
    path('reject/<int:profile_id>/', views.reject_membership, name='reject_membership'),

    path('volunteer-dashboard/', views.volunteer_dashboard, name='volunteer_dashboard'),

    path('tasks/', views.task_list, name='task_list'),
    path('task/create/', views.create_and_assign_task, name='task_create'),

    path("teams/", views.list_teams, name="team_list"),
    path("teams/create/", views.create_team, name="create_team"),
    path("teams/<int:team_id>/edit/", views.edit_team, name="edit_team"),
    path("teams/<int:team_id>/delete/", views.delete_team, name="delete_team"),

    path('membership-list/create/', views.create_membership, name='create_membership'),
    path('membership-list/', views.membership_list, name='membership_list'),
    path('membership-list/edit/<int:membership_id>/', views.edit_membership, name='edit_membership'),

    path('fee-name/create/', views.create_fee_name, name='create_fee_name'),
    path('fee-name/edit/<int:fee_name_id>/', views.edit_fee_name, name='edit_fee_name'),

    path('committees/add/', views.create_committee_with_members, name="add_committee"),
    path('committees/', views.committee_list, name='committee_list'),
    path('committees/<int:committee_id>/edit/', views.edit_committee, name='edit_committee'),

    path('expenses/add/', views.add_committee_expense, name='expense_add'),
    # path('expenses/', views.committee_expense_list, name='expense_list'),

    path('expense-type/add/', views.expense_type_form, name='expense_type_add'),
    path('expense-type/edit/<int:pk>/', views.expense_type_form, name='expense_type_edit'),
    path('expense-type/delete/', views.delete_expense_type, name='expense_type_delete'),

    path('designation/add/', views.designation_form, name='designation_add'),
    path('designation/edit/<int:pk>/', views.designation_form, name='designation_edit'),

    path('activity/add/', views.activity_form, name='activity_add'),
    path('activity/edit/<int:pk>/', views.activity_form, name='activity_edit'),

    path('donation-types/', views.donation_type_list, name='donation_type_list'),
    path('donation-types/create/', views.donation_type_create_or_edit, name='create_donation_type'),
    path('donation-types/<int:pk>/edit/', views.donation_type_create_or_edit, name='edit_donation_type'),
    path('donation-types/<int:pk>/delete/', views.donation_type_delete, name='delete_donation_type'),

    path('user-dashboard/', views.user_list_view, name='user_dashboard'),
    path('user-dashboard/<int:profile_id>/pdf/', views.generate_profile_pdf, name='user_pdf'),

    path('profile/<int:profile_id>/', views.profile_detail_view, name='profile_detail'),
    path('profile/<int:profile_id>/edit/', views.profile_edit_view, name='profile_edit'),
    path('family/add/', views.add_family_member_view, name='add_family_member'),
    # path('api/search-profiles/', views.search_profiles, name='search_profiles'),

    path('donations/<int:donation_id>/status/<str:new_status>/', views.change_donation_status, name='change_donation_status'),
    path('donations/<str:status>/', views.donations_by_status, name='donations_by_status'),
    path('donations/', views.donation_list, name='donation_list'),
    

    path('expenses/<int:expense_id>/status/<str:new_status>/', views.change_expense_status, name='change_expense_status'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/status/<str:status>/', views.expenses_by_status, name='expenses_by_status'),

    path('donationssss/add/', views.add_committee_donation, name='add_committee_donation'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),

    path('committee-permission/list/', CommitteePermissionListView.as_view(), name='committee_permission_list'),
    path('committee-permission/create/', views.create_committee_permission, name='committee_permission_create'),
    path('committee-permission/<int:pk>/edit/', views.edit_committee_permission, name='committee_permission_edit'),
    path('committee-permission/<int:pk>/delete/', views.delete_committee_permission, name='committee_permission_delete'),

    path('payments/create/<int:profile_id>/', views.admin_create_payment, name='admin_create_payment_for_member'),
    path('get-fee-structures/', views.get_fee_structures, name='get_fee_structures'),
    path('admin/get-profile-membership-type/', views.get_profile_membership_type, name='get_profile_membership_type'),
]
