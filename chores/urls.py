from django.urls import path
from . import views

app_name = 'chores'

urlpatterns = [
    path('', views.chore_list, name='list'),
    path('create/', views.chore_create, name='create'),
    path('<int:chore_id>/edit/', views.chore_edit, name='edit'),
    path('<int:chore_id>/delete/', views.chore_delete, name='delete'),
    path('<int:chore_id>/assign/', views.assign_chore, name='assign'),
    path('my/', views.my_chores, name='my_chores'),
    path('assignment/<int:assignment_id>/complete/', views.complete_chore, name='complete'),
    path('pending/', views.pending_approvals, name='pending_approvals'),
    path('assignment/<int:assignment_id>/approve/', views.approve_chore, name='approve'),
    path('assignment/<int:assignment_id>/reject/', views.reject_chore, name='reject'),
    path('payout/<int:kid_id>/', views.payout, name='payout'),
    path('history/', views.transaction_history, name='history'),
    path('history/<int:kid_id>/', views.transaction_history, name='history_kid'),
    path('export/<int:kid_id>/', views.export_csv, name='export_csv'),
]
