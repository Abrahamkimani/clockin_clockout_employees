from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import uuid


class ClockSession(models.Model):
    """
    Model representing a clock-in/clock-out session for a practitioner visiting a client.
    Tracks location, time, and session status.
    """
    
    STATUS_CHOICES = [
        ('active', _('Active')),
        ('completed', _('Completed')),
        ('disconnected', _('Disconnected')),
        ('auto_clocked_out', _('Auto Clocked Out')),
        ('cancelled', _('Cancelled')),
    ]
    
    # Unique session identifier
    session_id = models.UUIDField(
        _('session ID'),
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    
    # Relationships
    practitioner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clock_sessions',
        verbose_name=_('practitioner')
    )
    
    client = models.ForeignKey(
        'clients.Client',
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('client')
    )
    
    # Session status
    status = models.CharField(
        _('status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Clock-in information
    clock_in_time = models.DateTimeField(
        _('clock in time'),
        help_text=_('When the practitioner clocked in')
    )
    
    clock_in_latitude = models.DecimalField(
        _('clock in latitude'),
        max_digits=22,
        decimal_places=16,
        help_text=_('GPS latitude when clocking in')
    )
    
    clock_in_longitude = models.DecimalField(
        _('clock in longitude'),
        max_digits=22,
        decimal_places=16,
        help_text=_('GPS longitude when clocking in')
    )
    
    clock_in_accuracy = models.FloatField(
        _('clock in GPS accuracy'),
        blank=True,
        null=True,
        help_text=_('GPS accuracy in meters when clocking in')
    )
    
    # Clock-out information
    clock_out_time = models.DateTimeField(
        _('clock out time'),
        blank=True,
        null=True,
        help_text=_('When the practitioner clocked out')
    )
    
    clock_out_latitude = models.DecimalField(
        _('clock out latitude'),
        max_digits=22,
        decimal_places=16,
        blank=True,
        null=True,
        help_text=_('GPS latitude when clocking out')
    )
    
    clock_out_longitude = models.DecimalField(
        _('clock out longitude'),
        max_digits=22,
        decimal_places=16,
        blank=True,
        null=True,
        help_text=_('GPS longitude when clocking out')
    )
    
    clock_out_accuracy = models.FloatField(
        _('clock out GPS accuracy'),
        blank=True,
        null=True,
        help_text=_('GPS accuracy in meters when clocking out')
    )
    
    # Duration and timing
    duration_minutes = models.IntegerField(
        _('duration in minutes'),
        blank=True,
        null=True,
        help_text=_('Total session duration in minutes')
    )
    
    # Session notes and details
    session_notes = models.TextField(
        _('session notes'),
        blank=True,
        help_text=_('Notes about the session')
    )
    
    # Service type
    service_type = models.CharField(
        _('service type'),
        max_length=100,
        blank=True,
        choices=[
            ('counseling', _('Counseling Session')),
            ('assessment', _('Assessment')),
            ('crisis_intervention', _('Crisis Intervention')),
            ('case_management', _('Case Management')),
            ('family_therapy', _('Family Therapy')),
            ('group_therapy', _('Group Therapy')),
            ('other', _('Other')),
        ],
        help_text=_('Type of service provided')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Auto clock-out tracking
    auto_clock_out_time = models.DateTimeField(
        _('auto clock out time'),
        blank=True,
        null=True,
        help_text=_('When the session was automatically clocked out')
    )
    
    auto_clock_out_reason = models.CharField(
        _('auto clock out reason'),
        max_length=100,
        blank=True,
        choices=[
            ('timeout', _('Session Timeout')),
            ('gps_lost', _('GPS Signal Lost')),
            ('internet_lost', _('Internet Connection Lost')),
            ('system_maintenance', _('System Maintenance')),
        ]
    )
    
    # Distance tracking (for verification)
    distance_from_client_meters = models.FloatField(
        _('distance from client (meters)'),
        blank=True,
        null=True,
        help_text=_('Distance from client location when clocking in')
    )
    
    # Verification flags
    location_verified = models.BooleanField(
        _('location verified'),
        default=False,
        help_text=_('Whether the practitioner was at the correct location')
    )
    
    requires_review = models.BooleanField(
        _('requires review'),
        default=False,
        help_text=_('Whether this session requires supervisor review')
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reviewed_sessions',
        verbose_name=_('reviewed by')
    )
    
    reviewed_at = models.DateTimeField(
        _('reviewed at'),
        blank=True,
        null=True
    )
    
    class Meta:
        verbose_name = _('Clock Session')
        verbose_name_plural = _('Clock Sessions')
        ordering = ['-clock_in_time']
        indexes = [
            models.Index(fields=['practitioner', '-clock_in_time']),
            models.Index(fields=['client', '-clock_in_time']),
            models.Index(fields=['status']),
            models.Index(fields=['clock_in_time']),
            models.Index(fields=['requires_review']),
            models.Index(fields=['session_id']),
        ]
    
    def __str__(self):
        return f"{self.practitioner.get_full_name()} -> {self.client.get_full_name()} ({self.clock_in_time.strftime('%Y-%m-%d %H:%M')})"
    
    def save(self, *args, **kwargs):
        """Override save to calculate duration and set flags."""
        # Calculate duration if both clock in and out times exist
        if self.clock_in_time and self.clock_out_time:
            duration = self.clock_out_time - self.clock_in_time
            self.duration_minutes = int(duration.total_seconds() / 60)
            
            # Set status to completed if not already set
            if self.status == 'active':
                self.status = 'completed'
        
        # Calculate distance from client location if coordinates are available
        if (self.clock_in_latitude and self.clock_in_longitude and 
            self.client.latitude and self.client.longitude):
            self.distance_from_client_meters = self._calculate_distance(
                float(self.clock_in_latitude), float(self.clock_in_longitude),
                float(self.client.latitude), float(self.client.longitude)
            )
            
            # Verify location if within acceptable range
            if self.distance_from_client_meters <= settings.GPS_ACCURACY_THRESHOLD:
                self.location_verified = True
            else:
                self.requires_review = True
        
        super().save(*args, **kwargs)
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate the distance between two GPS coordinates using Haversine formula.
        Returns distance in meters.
        """
        from math import radians, cos, sin, asin, sqrt
        
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        
        return c * r
    
    def clock_out(self, latitude, longitude, accuracy=None, notes=None):
        """
        Clock out the session with location and time.
        """
        if self.status != 'active':
            raise ValueError("Cannot clock out a session that is not active")
        
        self.clock_out_time = timezone.now()
        self.clock_out_latitude = Decimal(str(latitude))
        self.clock_out_longitude = Decimal(str(longitude))
        if accuracy:
            self.clock_out_accuracy = accuracy
        if notes:
            self.session_notes = notes
        
        self.save()
    
    def auto_clock_out(self, reason='timeout'):
        """
        Automatically clock out the session due to system issues.
        """
        if self.status != 'active':
            return False
        
        self.auto_clock_out_time = timezone.now()
        self.auto_clock_out_reason = reason
        self.status = 'auto_clocked_out'
        self.requires_review = True
        
        # Calculate duration based on timeout settings
        if self.clock_in_time:
            duration = self.auto_clock_out_time - self.clock_in_time
            self.duration_minutes = int(duration.total_seconds() / 60)
        
        self.save()
        return True
    
    @property
    def is_active(self):
        """Check if session is currently active."""
        return self.status == 'active'
    
    @property
    def duration_hours_minutes(self):
        """Return duration as hours and minutes string."""
        if not self.duration_minutes:
            return "0h 0m"
        
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        return f"{hours}h {minutes}m"
    
    @property
    def session_date(self):
        """Return the date of the session."""
        return self.clock_in_time.date() if self.clock_in_time else None


class SessionLocationUpdate(models.Model):
    """
    Model to track location updates during an active session.
    Used for monitoring and safety purposes.
    """
    
    session = models.ForeignKey(
        ClockSession,
        on_delete=models.CASCADE,
        related_name='location_updates',
        verbose_name=_('session')
    )
    
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=22,
        decimal_places=16
    )
    
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=22,
        decimal_places=16
    )
    
    accuracy = models.FloatField(
        _('GPS accuracy'),
        blank=True,
        null=True,
        help_text=_('GPS accuracy in meters')
    )
    
    battery_level = models.IntegerField(
        _('battery level'),
        blank=True,
        null=True,
        help_text=_('Device battery level percentage')
    )
    
    class Meta:
        verbose_name = _('Session Location Update')
        verbose_name_plural = _('Session Location Updates')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session', '-timestamp']),
        ]
    
    def __str__(self):
        return f"Location update for {self.session.session_id} at {self.timestamp}"
