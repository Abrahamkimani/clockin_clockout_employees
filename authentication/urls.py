from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User profile endpoints
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('location/update/', views.UserLocationUpdateView.as_view(), name='location_update'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    
    # User management endpoints
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('status/', views.user_status_view, name='user_status'),
    path('check-phone/', views.check_phone_availability, name='check_phone'),
]
