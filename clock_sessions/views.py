from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from .models import ClockSession, SessionLocationUpdate
from .serializers import (
    ClockInSerializer,
    ClockOutSerializer,
    ClockSessionSerializer,
    ClockSessionListSerializer,
    SessionLocationUpdateSerializer,
    ActiveSessionSerializer,
    SessionReviewSerializer
)


class ClockInView(generics.CreateAPIView):
    """
    API endpoint for clocking in - starting a new session.
    """
    serializer_class = ClockInSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        
        return Response({
            'message': 'Clocked in successfully',
            'session': ClockSessionSerializer(session).data
        }, status=status.HTTP_201_CREATED)


class ClockOutView(generics.GenericAPIView):
    """
    API endpoint for clocking out - ending the active session.
    """
    serializer_class = ClockOutSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        session = serializer.save()
        
        return Response({
            'message': 'Clocked out successfully',
            'session': ClockSessionSerializer(session).data
        }, status=status.HTTP_200_OK)


class ActiveSessionView(generics.RetrieveAPIView):
    """
    API endpoint to get the current active session for a practitioner.
    """
    serializer_class = ActiveSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        try:
            return ClockSession.objects.get(
                practitioner=self.request.user,
                status='active'
            )
        except ClockSession.DoesNotExist:
            return None
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance is None:
            return Response({
                'active_session': None,
                'message': 'No active session found'
            }, status=status.HTTP_200_OK)
        
        serializer = self.get_serializer(instance)
        return Response({
            'active_session': serializer.data
        }, status=status.HTTP_200_OK)


class UserSessionsView(generics.ListAPIView):
    """
    API endpoint to get sessions for the authenticated user.
    """
    serializer_class = ClockSessionListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ClockSession.objects.filter(practitioner=self.request.user)
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(clock_in_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(clock_in_time__date__lte=end_date)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-clock_in_time')


class SessionDetailView(generics.RetrieveAPIView):
    """
    API endpoint to get detailed information about a specific session.
    """
    serializer_class = ClockSessionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'session_id'
    
    def get_queryset(self):
        user = self.request.user
        queryset = ClockSession.objects.all()
        
        # Regular practitioners can only see their own sessions
        if not (user.is_supervisor or user.is_staff):
            queryset = queryset.filter(practitioner=user)
        # Supervisors can see sessions from their department
        elif user.is_supervisor and not user.is_staff:
            queryset = queryset.filter(practitioner__department=user.department)
        
        return queryset


class AllSessionsView(generics.ListAPIView):
    """
    API endpoint for supervisors/admins to view all sessions.
    """
    serializer_class = ClockSessionListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Only supervisors and staff can view all sessions
        if not (user.is_supervisor or user.is_staff):
            return ClockSession.objects.none()
        
        queryset = ClockSession.objects.all()
        
        # Filter by department if user is supervisor (not admin)
        if user.is_supervisor and not user.is_staff:
            queryset = queryset.filter(practitioner__department=user.department)
        
        # Apply filters
        practitioner_id = self.request.query_params.get('practitioner')
        client_id = self.request.query_params.get('client')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        status_filter = self.request.query_params.get('status')
        
        if practitioner_id:
            queryset = queryset.filter(practitioner_id=practitioner_id)
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if start_date:
            queryset = queryset.filter(clock_in_time__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(clock_in_time__date__lte=end_date)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-clock_in_time')


class SessionReviewView(generics.UpdateAPIView):
    """
    API endpoint for supervisors to review sessions.
    """
    serializer_class = SessionReviewSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'session_id'
    
    def get_queryset(self):
        user = self.request.user
        
        # Only supervisors and staff can review sessions
        if not (user.is_supervisor or user.is_staff):
            return ClockSession.objects.none()
        
        queryset = ClockSession.objects.filter(requires_review=True)
        
        # Filter by department if user is supervisor (not admin)
        if user.is_supervisor and not user.is_staff:
            queryset = queryset.filter(practitioner__department=user.department)
        
        return queryset


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def session_location_update(request):
    """
    API endpoint to update location during an active session.
    """
    try:
        active_session = ClockSession.objects.get(
            practitioner=request.user,
            status='active'
        )
    except ClockSession.DoesNotExist:
        return Response({
            'error': 'No active session found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = SessionLocationUpdateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Create location update record
    location_update = SessionLocationUpdate.objects.create(
        session=active_session,
        **serializer.validated_data
    )
    
    # Update user's current location
    request.user.current_latitude = location_update.latitude
    request.user.current_longitude = location_update.longitude
    request.user.last_location_update = timezone.now()
    request.user.save(update_fields=[
        'current_latitude', 'current_longitude', 'last_location_update'
    ])
    
    return Response({
        'message': 'Location updated successfully',
        'timestamp': location_update.timestamp
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def emergency_session_end(request):
    """
    API endpoint for emergency session termination.
    """
    try:
        active_session = ClockSession.objects.get(
            practitioner=request.user,
            status='active'
        )
    except ClockSession.DoesNotExist:
        return Response({
            'error': 'No active session found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    reason = request.data.get('reason', 'emergency')
    notes = request.data.get('notes', 'Emergency session termination')
    
    # Auto clock out the session
    active_session.auto_clock_out(reason=reason)
    active_session.session_notes = f"{active_session.session_notes or ''}\n\nEmergency Notes: {notes}".strip()
    active_session.save()
    
    return Response({
        'message': 'Session terminated due to emergency',
        'session': ClockSessionSerializer(active_session).data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def session_statistics(request):
    """
    API endpoint to get session statistics for a user or department.
    """
    user = request.user
    
    # Base queryset
    if user.is_supervisor or user.is_staff:
        queryset = ClockSession.objects.all()
        if user.is_supervisor and not user.is_staff:
            queryset = queryset.filter(practitioner__department=user.department)
    else:
        queryset = ClockSession.objects.filter(practitioner=user)
    
    # Filter by date range (default to last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    start_param = request.query_params.get('start_date')
    end_param = request.query_params.get('end_date')
    
    if start_param:
        from datetime import datetime
        start_date = datetime.strptime(start_param, '%Y-%m-%d').date()
    if end_param:
        from datetime import datetime
        end_date = datetime.strptime(end_param, '%Y-%m-%d').date()
    
    queryset = queryset.filter(
        clock_in_time__date__range=[start_date, end_date]
    )
    
    # Calculate statistics
    total_sessions = queryset.count()
    completed_sessions = queryset.filter(status='completed').count()
    active_sessions = queryset.filter(status='active').count()
    auto_clocked_out = queryset.filter(status='auto_clocked_out').count()
    sessions_requiring_review = queryset.filter(requires_review=True).count()
    
    # Calculate total duration
    total_minutes = sum(
        session.duration_minutes or 0 
        for session in queryset.filter(duration_minutes__isnull=False)
    )
    
    average_duration = (
        total_minutes / completed_sessions 
        if completed_sessions > 0 else 0
    )
    
    return Response({
        'period': {
            'start_date': start_date,
            'end_date': end_date
        },
        'statistics': {
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'active_sessions': active_sessions,
            'auto_clocked_out': auto_clocked_out,
            'sessions_requiring_review': sessions_requiring_review,
            'total_hours': round(total_minutes / 60, 2),
            'average_session_minutes': round(average_duration, 2)
        }
    }, status=status.HTTP_200_OK)
