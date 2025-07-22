"""
Celery configuration for clockin_project.
Handles background tasks like auto clock-out and notifications.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'clockin_project.settings')

app = Celery('clockin_project')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'auto-clock-out-timeout-sessions': {
        'task': 'sessions.tasks.auto_clock_out_timeout_sessions',
        'schedule': 300.0,  # Run every 5 minutes
    },
    'cleanup-old-location-updates': {
        'task': 'sessions.tasks.cleanup_old_location_updates',
        'schedule': 3600.0,  # Run every hour
    },
}

app.conf.timezone = 'UTC'

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
