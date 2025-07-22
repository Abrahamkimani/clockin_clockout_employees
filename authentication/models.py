from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager for phone number authentication."""
    
    def create_user(self, phone_number, password=None, **extra_fields):
        """Create and return a regular user with the given phone number and password."""
        if not phone_number:
            raise ValueError(_('The Phone Number field must be set'))
        
        extra_fields.setdefault('is_active', True)
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Create and return a superuser with the given phone number and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for mental health wellness center practitioners.
    Uses phone number as the unique identifier for login.
    """
    
    # Remove username and use phone as primary identifier
    username = None
    
    # Phone number as unique identifier
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    phone_number = models.CharField(
        _('phone number'),
        validators=[phone_regex],
        max_length=17,
        unique=True,
        help_text=_('Required. Up to 15 digits allowed.')
    )
    
    # Additional user information
    employee_id = models.CharField(
        _('employee ID'),
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text=_('Unique employee identifier')
    )
    
    department = models.CharField(
        _('department'),
        max_length=100,
        blank=True,
        help_text=_('Department or team name')
    )
    
    position = models.CharField(
        _('position'),
        max_length=100,
        blank=True,
        help_text=_('Job title or position')
    )
    
    is_practitioner = models.BooleanField(
        _('practitioner status'),
        default=True,
        help_text=_('Designates whether this user is a field practitioner.')
    )
    
    is_supervisor = models.BooleanField(
        _('supervisor status'),
        default=False,
        help_text=_('Designates whether this user can supervise other practitioners.')
    )
    
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )
    
    # Emergency contact information
    emergency_contact_name = models.CharField(
        _('emergency contact name'),
        max_length=100,
        blank=True,
        null=True
    )
    
    emergency_contact_phone = models.CharField(
        _('emergency contact phone'),
        validators=[phone_regex],
        max_length=17,
        blank=True,
        null=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_location_update = models.DateTimeField(
        _('last location update'),
        blank=True,
        null=True,
        help_text=_('Last time GPS location was updated')
    )
    
    # Current location (for emergency purposes)
    current_latitude = models.DecimalField(
        _('current latitude'),
        max_digits=22,
        decimal_places=16,
        blank=True,
        null=True
    )
    
    current_longitude = models.DecimalField(
        _('current longitude'),
        max_digits=22,
        decimal_places=16,
        blank=True,
        null=True
    )
    
    # Use phone number as username field
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    # Custom user manager
    objects = UserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'auth_user'
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['employee_id']),
            models.Index(fields=['is_practitioner']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.phone_number})"
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    @property
    def has_current_location(self):
        """Check if user has current location data."""
        return bool(self.current_latitude and self.current_longitude)
    
    @property
    def display_name(self):
        """Return display name for UI."""
        full_name = self.get_full_name()
        return full_name if full_name else self.phone_number
