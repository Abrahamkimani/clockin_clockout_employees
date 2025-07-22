from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class Client(models.Model):
    """
    Model representing clients that practitioners visit.
    """
    
    # Client basic information
    first_name = models.CharField(_('first name'), max_length=100)
    last_name = models.CharField(_('last name'), max_length=100)
    
    # Phone number for contact
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        _('phone number'),
        validators=[phone_regex],
        max_length=17,
        blank=True,
        help_text=_('Client contact number')
    )
    
    email = models.EmailField(_('email address'), blank=True)
    
    # Client unique identifier
    client_id = models.CharField(
        _('client ID'),
        max_length=20,
        unique=True,
        help_text=_('Unique client identifier')
    )
    
    # Address information
    street_address = models.CharField(_('street address'), max_length=255)
    city = models.CharField(_('city'), max_length=100)
    state = models.CharField(_('state'), max_length=50)
    zip_code = models.CharField(_('zip code'), max_length=10)
    
    # GPS coordinates for the client's location
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=22,
        decimal_places=16,
        help_text=_('Latitude of client location')
    )
    
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=22,
        decimal_places=16,
        help_text=_('Longitude of client location')
    )
    
    # Client status and care information
    is_active = models.BooleanField(
        _('active status'),
        default=True,
        help_text=_('Whether the client is currently receiving services')
    )
    
    care_level = models.CharField(
        _('care level'),
        max_length=50,
        choices=[
            ('low', _('Low Intensity')),
            ('medium', _('Medium Intensity')),
            ('high', _('High Intensity')),
            ('crisis', _('Crisis Intervention')),
        ],
        default='medium'
    )
    
    # Special instructions for practitioners
    special_instructions = models.TextField(
        _('special instructions'),
        blank=True,
        help_text=_('Special instructions for practitioners visiting this client')
    )
    
    # Emergency contact information
    emergency_contact_name = models.CharField(
        _('emergency contact name'),
        max_length=100,
        blank=True
    )
    
    emergency_contact_phone = models.CharField(
        _('emergency contact phone'),
        validators=[phone_regex],
        max_length=17,
        blank=True
    )
    
    emergency_contact_relationship = models.CharField(
        _('emergency contact relationship'),
        max_length=50,
        blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Access and safety information
    access_instructions = models.TextField(
        _('access instructions'),
        blank=True,
        help_text=_('Instructions for accessing the client location (gate codes, etc.)')
    )
    
    safety_notes = models.TextField(
        _('safety notes'),
        blank=True,
        help_text=_('Important safety considerations for this location')
    )
    
    class Meta:
        verbose_name = _('Client')
        verbose_name_plural = _('Clients')
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['client_id']),
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.client_id})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def full_address(self):
        """Return formatted full address."""
        return f"{self.street_address}, {self.city}, {self.state} {self.zip_code}"
    
    @property
    def location_coordinates(self):
        """Return tuple of (latitude, longitude)."""
        return (float(self.latitude), float(self.longitude))
