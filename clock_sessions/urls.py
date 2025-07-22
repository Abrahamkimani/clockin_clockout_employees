from django.urls import path
from . import views

app_name = 'sessions'

urlpatterns = [
    # Clock in/out endpoints
    path('clock-in/', views.ClockInView.as_view(), name='clock_in'),
    path('clock-out/', views.ClockOutView.as_view(), name='clock_out'),
    
    # Session management endpoints
    path('active/', views.ActiveSessionView.as_view(), name='active_session'),
    path('my-sessions/', views.UserSessionsView.as_view(), name='user_sessions'),
    path('all/', views.AllSessionsView.as_view(), name='all_sessions'),
    path('<uuid:session_id>/', views.SessionDetailView.as_view(), name='session_detail'),
    path('<uuid:session_id>/review/', views.SessionReviewView.as_view(), name='session_review'),
    
    # Utility endpoints
    path('location-update/', views.session_location_update, name='location_update'),
    path('emergency-end/', views.emergency_session_end, name='emergency_end'),
    path('statistics/', views.session_statistics, name='statistics'),
]
