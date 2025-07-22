"""
Django management command to auto clock out sessions that have timed out.
Usage: python manage.py auto_clockout_sessions
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from sessions.models import ClockSession


class Command(BaseCommand):
    help = 'Automatically clock out sessions that have exceeded the timeout period'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout-minutes',
            type=int,
            default=getattr(settings, 'SESSION_TIMEOUT_MINUTES', 480),
            help='Timeout in minutes (default: 480 = 8 hours)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )
    
    def handle(self, *args, **options):
        timeout_minutes = options['timeout_minutes']
        dry_run = options['dry_run']
        
        cutoff_time = timezone.now() - timedelta(minutes=timeout_minutes)
        
        # Find active sessions that have exceeded timeout
        timeout_sessions = ClockSession.objects.filter(
            status='active',
            clock_in_time__lt=cutoff_time
        ).select_related('practitioner', 'client')
        
        count = timeout_sessions.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No sessions found that need to be auto clocked out.')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would auto clock out {count} sessions:')
            )
            for session in timeout_sessions:
                elapsed = timezone.now() - session.clock_in_time
                hours = elapsed.total_seconds() / 3600
                self.stdout.write(
                    f'  - {session.practitioner.get_full_name()} -> {session.client.get_full_name()} '
                    f'(elapsed: {hours:.1f} hours)'
                )
        else:
            success_count = 0
            for session in timeout_sessions:
                try:
                    session.auto_clock_out('timeout')
                    success_count += 1
                    self.stdout.write(
                        f'Auto clocked out: {session.practitioner.get_full_name()} -> {session.client.get_full_name()}'
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Failed to auto clock out session {session.session_id}: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully auto clocked out {success_count} out of {count} sessions.')
            )
