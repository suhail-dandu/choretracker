from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register_family, name='register_family'),
    path('join/', views.join_family, name='join_family'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/<str:token>/', views.password_reset, name='password_reset'),
    path('profile/', views.profile, name='profile'),
    path('kid/<int:kid_id>/', views.kid_profile, name='kid_profile'),
    path('kid/<int:kid_id>/adjust-points/', views.adjust_points, name='adjust_points'),
]
