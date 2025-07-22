from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.urls import reverse
from .models import ClockSession, SessionLocationUpdate


class SessionLocationUpdateInline(admin.TabularInline):
    """
    Inline admin for session location updates.
    """
    model = SessionLocationUpdate
    extra = 0
    readonly_fields = ('timestamp', 'battery_level')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ClockSession)
class ClockSessionAdmin(admin.ModelAdmin):
    """
    Admin configuration for ClockSession model.
    """
    
    # Fields to display in the session list
    list_display = (
        'session_id_short', 'practitioner_name', 'client_name',
        'session_date', 'clock_in_time', 'clock_out_time', 
        'duration_display', 'status', 'location_verified',
        'requires_review'
    )
    
    # Fields to search by
    search_fields = (
        'session_id', 'practitioner__first_name', 'practitioner__last_name',
        'practitioner__phone_number', 'client__first_name', 
        'client__last_name', 'client__client_id'
    )
    
    # Filters for the right sidebar
    list_filter = (
        'status', 'location_verified', 'requires_review', 'service_type',
        'clock_in_time', 'practitioner__department', 'client__care_level'
    )
    
    # Links to detail pages
    list_display_links = ('session_id_short',)
    
    # Default ordering
    ordering = ('-clock_in_time',)
    
    # Pagination
    list_per_page = 25
    
    # Readonly fields
    readonly_fields = (
        'session_id', 'created_at', 'updated_at', 'duration_minutes',
        'distance_from_client_meters', 'location_verified',
        'clock_in_map_link', 'clock_out_map_link'
    )
    
    # Inlines
    inlines = [SessionLocationUpdateInline]
    
    # Fieldsets for organization
    fieldsets = (
        ('Session Information', {
            'fields': (
                'session_id', 'practitioner', 'client', 'status',
                'service_type', 'session_notes'
            )
        }),
        ('Clock In Details', {
            'fields': (
                'clock_in_time', 'clock_in_latitude', 'clock_in_longitude',
                'clock_in_accuracy', 'clock_in_map_link'
            )
        }),
        ('Clock Out Details', {
            'fields': (
                'clock_out_time', 'clock_out_latitude', 'clock_out_longitude',
                'clock_out_accuracy', 'clock_out_map_link'
            ),
            'classes': ('collapse',)
        }),
        ('Auto Clock Out', {
            'fields': (
                'auto_clock_out_time', 'auto_clock_out_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Verification & Review', {
            'fields': (
                'duration_minutes', 'distance_from_client_meters',
                'location_verified', 'requires_review', 'reviewed_by',
                'reviewed_at'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def session_id_short(self, obj):
        """Display shortened session ID."""
        return str(obj.session_id)[:8] + '...'
    session_id_short.short_description = 'Session ID'
    
    def practitioner_name(self, obj):
        """Display practitioner name with link."""
        name = obj.practitioner.get_full_name()
        url = reverse('admin:authentication_user_change', args=[obj.practitioner.id])
        return format_html('<a href="{}">{}</a>', url, name)
    practitioner_name.short_description = 'Practitioner'
    practitioner_name.admin_order_field = 'practitioner__last_name'
    
    def client_name(self, obj):
        """Display client name with link."""
        name = obj.client.get_full_name()
        url = reverse('admin:clients_client_change', args=[obj.client.id])
        return format_html('<a href="{}">{}</a>', url, name)
    client_name.short_description = 'Client'
    client_name.admin_order_field = 'client__last_name'
    
    def duration_display(self, obj):
        """Display session duration in a readable format."""
        if obj.duration_minutes:
            return obj.duration_hours_minutes
        elif obj.status == 'active':
            elapsed = timezone.now() - obj.clock_in_time
            minutes = int(elapsed.total_seconds() / 60)
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m (active)"
        return 'N/A'
    duration_display.short_description = 'Duration'
    
    def clock_in_map_link(self, obj):
        """Display Google Maps link for clock-in location."""
        if obj.clock_in_latitude and obj.clock_in_longitude:
            return format_html(
                '<a href="https://maps.google.com/?q={},{}" target="_blank">View Clock-In Location</a>',
                obj.clock_in_latitude, obj.clock_in_longitude
            )
        return 'No location data'
    clock_in_map_link.short_description = 'Clock-In Map'
    
    def clock_out_map_link(self, obj):
        """Display Google Maps link for clock-out location."""
        if obj.clock_out_latitude and obj.clock_out_longitude:
            return format_html(
                '<a href="https://maps.google.com/?q={},{}" target="_blank">View Clock-Out Location</a>',
                obj.clock_out_latitude, obj.clock_out_longitude
            )
        return 'No location data'
    clock_out_map_link.short_description = 'Clock-Out Map'
    
    def get_queryset(self, request):
        """Optimize queryset with related objects."""
        qs = super().get_queryset(request)
        return qs.select_related('practitioner', 'client', 'reviewed_by')
    
    # Custom actions
    actions = ['mark_reviewed', 'mark_needs_review', 'auto_clock_out_selected']
    
    def mark_reviewed(self, request, queryset):
        """Custom action to mark sessions as reviewed."""
        updated = queryset.update(
            requires_review=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(
            request, 
            f'{updated} session(s) were marked as reviewed.'
        )
    mark_reviewed.short_description = "Mark selected sessions as reviewed"
    
    def mark_needs_review(self, request, queryset):
        """Custom action to mark sessions as needing review."""
        updated = queryset.update(requires_review=True)
        self.message_user(
            request, 
            f'{updated} session(s) were marked as needing review.'
        )
    mark_needs_review.short_description = "Mark selected sessions as needing review"
    
    def auto_clock_out_selected(self, request, queryset):
        """Custom action to auto clock out active sessions."""
        active_sessions = queryset.filter(status='active')
        count = 0
        for session in active_sessions:
            session.auto_clock_out('admin_action')
            count += 1
        
        self.message_user(
            request, 
            f'{count} active session(s) were automatically clocked out.'
        )
    auto_clock_out_selected.short_description = "Auto clock-out selected active sessions"


@admin.register(SessionLocationUpdate)
class SessionLocationUpdateAdmin(admin.ModelAdmin):
    """
    Admin configuration for SessionLocationUpdate model.
    """
    
    list_display = (
        'session_short', 'practitioner_name', 'timestamp', 
        'battery_level', 'accuracy'
    )
    
    list_filter = ('timestamp', 'battery_level')
    
    search_fields = (
        'session__session_id', 'session__practitioner__first_name',
        'session__practitioner__last_name'
    )
    
    readonly_fields = ('timestamp', 'map_link')
    
    ordering = ('-timestamp',)
    
    list_per_page = 50
    
    fieldsets = (
        ('Session Information', {
            'fields': ('session',)
        }),
        ('Location Data', {
            'fields': (
                'timestamp', 'latitude', 'longitude', 'accuracy', 'map_link'
            )
        }),
        ('Device Information', {
            'fields': ('battery_level',)
        }),
    )
    
    def session_short(self, obj):
        """Display shortened session ID."""
        return str(obj.session.session_id)[:8] + '...'
    session_short.short_description = 'Session'
    
    def practitioner_name(self, obj):
        """Display practitioner name."""
        return obj.session.practitioner.get_full_name()
    practitioner_name.short_description = 'Practitioner'
    
    def map_link(self, obj):
        """Display Google Maps link for location update."""
        return format_html(
            '<a href="https://maps.google.com/?q={},{}" target="_blank">View on Google Maps</a>',
            obj.latitude, obj.longitude
        )
    map_link.short_description = 'Map Link'
    
    def get_queryset(self, request):
        """Optimize queryset with related objects."""
        qs = super().get_queryset(request)
        return qs.select_related('session__practitioner')
    
    def has_add_permission(self, request):
        """Disable manual addition of location updates."""
        return False
