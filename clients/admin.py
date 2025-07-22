from django.contrib import admin
from django.utils.html import format_html
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Admin configuration for Client model.
    """
    
    # Fields to display in the client list
    list_display = (
        'client_id', 'get_full_name', 'phone_number', 'city', 
        'care_level', 'is_active', 'sessions_count', 'created_at'
    )
    
    # Fields to search by
    search_fields = (
        'client_id', 'first_name', 'last_name', 'phone_number', 
        'email', 'street_address', 'city'
    )
    
    # Filters for the right sidebar
    list_filter = (
        'is_active', 'care_level', 'state', 'city', 'created_at'
    )
    
    # Links to detail pages
    list_display_links = ('client_id', 'get_full_name')
    
    # Default ordering
    ordering = ('last_name', 'first_name')
    
    # Pagination
    list_per_page = 25
    
    # Readonly fields
    readonly_fields = ('created_at', 'updated_at', 'location_link')
    
    # Fieldsets for organization
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'client_id', 'first_name', 'last_name', 
                'phone_number', 'email'
            )
        }),
        ('Address & Location', {
            'fields': (
                'street_address', 'city', 'state', 'zip_code',
                'latitude', 'longitude', 'location_link'
            )
        }),
        ('Care Information', {
            'fields': (
                'is_active', 'care_level', 'special_instructions'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relationship'
            ),
            'classes': ('collapse',)
        }),
        ('Access & Safety', {
            'fields': (
                'access_instructions', 'safety_notes'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_full_name(self, obj):
        """Display full name in admin."""
        return obj.get_full_name()
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'last_name'
    
    def sessions_count(self, obj):
        """Display number of sessions for this client."""
        count = obj.sessions.count()
        if count > 0:
            return format_html(
                '<a href="/admin/sessions/clocksession/?client__id__exact={}">{} sessions</a>',
                obj.id, count
            )
        return '0 sessions'
    sessions_count.short_description = 'Sessions'
    
    def location_link(self, obj):
        """Display Google Maps link for client location."""
        if obj.latitude and obj.longitude:
            return format_html(
                '<a href="https://maps.google.com/?q={},{}" target="_blank">View on Google Maps</a>',
                obj.latitude, obj.longitude
            )
        return 'No location data'
    location_link.short_description = 'Map Link'
    
    def get_queryset(self, request):
        """Optimize queryset with session count."""
        qs = super().get_queryset(request)
        return qs.prefetch_related('sessions')
    
    # Custom actions
    actions = ['activate_clients', 'deactivate_clients']
    
    def activate_clients(self, request, queryset):
        """Custom action to activate selected clients."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request, 
            f'{updated} client(s) were successfully activated.'
        )
    activate_clients.short_description = "Activate selected clients"
    
    def deactivate_clients(self, request, queryset):
        """Custom action to deactivate selected clients."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request, 
            f'{updated} client(s) were successfully deactivated.'
        )
    deactivate_clients.short_description = "Deactivate selected clients"
