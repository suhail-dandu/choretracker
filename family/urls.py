from django.urls import path
from . import views

app_name = 'family'

urlpatterns = [
    path('', views.family_overview, name='overview'),
    path('add-child/', views.add_child, name='add_child'),
    path('remove-child/<int:kid_id>/', views.remove_child, name='remove_child'),
    path('award-badge/<int:kid_id>/', views.award_badge, name='award_badge'),
    path('settings/', views.family_settings, name='settings'),
]
