"""
Celery tasks for session management and background processing.
"""

from celery import shared_task
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def auto_clock_out_timeout_sessions():
    """
    Background task to automatically clock out sessions that have exceeded the timeout.
    Runs every 5 minutes via Celery Beat.
    """
    from .models import ClockSession
    
    timeout_minutes = getattr(settings, 'SESSION_TIMEOUT_MINUTES', 480)  # 8 hours default
    cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)
    
    # Find active sessions that have exceeded timeout
    timeout_sessions = ClockSession.objects.filter(
        status='active',
        clock_in_time__lt=cutoff_time
    )
    
    count = 0
    for session in timeout_sessions:
        try:
            session.auto_clock_out('timeout')
            count += 1
            logger.info(f"Auto clocked out session {session.session_id} due to timeout")
        except Exception as e:
            logger.error(f"Failed to auto clock out session {session.session_id}: {e}")
    
    logger.info(f"Auto clocked out {count} sessions due to timeout")
    return count


@shared_task
def cleanup_old_location_updates():
    """
    Background task to clean up old location updates (older than 30 days).
    Runs hourly via Celery Beat.
    """
    from .models import SessionLocationUpdate
    
    cutoff_date = timezone.now() - timedelta(days=30)
    
    # Delete old location updates
    deleted_count, _ = SessionLocationUpdate.objects.filter(
        timestamp__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old location updates")
    return deleted_count


@shared_task
def send_session_reminder(session_id):
    """
    Send reminder notification for long-running sessions.
    Called 4 hours after clock-in.
    """
    from .models import ClockSession
    
    try:
        session = ClockSession.objects.get(session_id=session_id, status='active')
        # Here you would implement your notification logic
        # For example: send push notification, email, SMS, etc.
        
        logger.info(f"Sent reminder for session {session_id}")
        return True
    except ClockSession.DoesNotExist:
        logger.warning(f"Session {session_id} not found or not active for reminder")
        return False


@shared_task
def process_gps_verification(session_id):
    """
    Background task to verify GPS location against client location.
    """
    from .models import ClockSession
    
    try:
        session = ClockSession.objects.get(session_id=session_id)
        
        # This would typically involve more sophisticated GPS verification
        # For now, we'll use the simple distance calculation in the model
        if session.distance_from_client_meters:
            threshold = getattr(settings, 'GPS_ACCURACY_THRESHOLD', 100)
            
            if session.distance_from_client_meters <= threshold:
                session.location_verified = True
            else:
                session.requires_review = True
                
            session.save(update_fields=['location_verified', 'requires_review'])
            
        logger.info(f"Processed GPS verification for session {session_id}")
        return True
    except ClockSession.DoesNotExist:
        logger.error(f"Session {session_id} not found for GPS verification")
        return False


@shared_task
def generate_daily_report(date_str):
    """
    Generate daily session report for supervisors.
    """
    from datetime import datetime
    from django.core.mail import send_mail
    from authentication.models import User
    from .models import ClockSession
    
    try:
        report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get all sessions for the date
        sessions = ClockSession.objects.filter(
            clock_in_time__date=report_date
        ).select_related('practitioner', 'client')
        
        # Generate report data
        total_sessions = sessions.count()
        completed_sessions = sessions.filter(status='completed').count()
        active_sessions = sessions.filter(status='active').count()
        sessions_needing_review = sessions.filter(requires_review=True).count()
        
        total_hours = sum(
            (session.duration_minutes or 0) / 60 
            for session in sessions.filter(duration_minutes__isnull=False)
        )
        
        # Send email to supervisors
        supervisors = User.objects.filter(is_supervisor=True, is_active=True)
        
        subject = f'Daily Session Report - {report_date.strftime("%B %d, %Y")}'
        message = f"""
        Daily Session Report for {report_date.strftime("%B %d, %Y")}
        
        Summary:
        - Total Sessions: {total_sessions}
        - Completed Sessions: {completed_sessions}
        - Active Sessions: {active_sessions}
        - Sessions Needing Review: {sessions_needing_review}
        - Total Hours: {total_hours:.2f}
        
        Please review the admin interface for detailed information.
        """
        
        for supervisor in supervisors:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [supervisor.email],
                fail_silently=True
            )
        
        logger.info(f"Generated daily report for {report_date}")
        return True
    except Exception as e:
        logger.error(f"Failed to generate daily report for {date_str}: {e}")
        return False
