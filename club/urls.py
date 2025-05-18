from django.urls import path
from . import views
urlpatterns = [
    path('club-register/', views.club_registration, name='club_registration'),
    path('edit/', views.edit_club, name='edit_club'),
    path('committees/<int:committee_id>/add-expense/', views.add_committee_expense, name='add_committee_expense'),
    path('expenses/', views.committee_expense_list, name='committee_expense_list'),
    path('committee-report/<int:committee_id>/', views.committee_report, name='committee_report'),
]