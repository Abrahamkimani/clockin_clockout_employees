from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom User admin with phone number authentication support.
    """
    
    # Fields to display in the user list
    list_display = (
        'phone_number', 'get_full_name', 'email', 'employee_id', 
        'department', 'is_practitioner', 'is_supervisor', 'is_active', 
        'last_login', 'created_at'
    )
    
    # Fields to search by
    search_fields = ('phone_number', 'first_name', 'last_name', 'email', 'employee_id')
    
    # Filters for the right sidebar
    list_filter = (
        'is_practitioner', 'is_supervisor', 'is_active', 'is_staff', 
        'department', 'position', 'created_at', 'last_login'
    )
    
    # Links to detail pages
    list_display_links = ('phone_number', 'get_full_name')
    
    # Pagination
    list_per_page = 25
    
    # Default ordering
    ordering = ('last_name', 'first_name')
    
    # Fields that are readonly
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'last_location_update')
    
    # Fieldsets for the user detail/edit page
    fieldsets = (
        (None, {
            'fields': ('phone_number', 'password')
        }),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'email', 'profile_picture',
                'employee_id', 'department', 'position'
            )
        }),
        (_('Contact & Emergency'), {
            'fields': (
                'emergency_contact_name', 'emergency_contact_phone'
            ),
            'classes': ('collapse',)
        }),
        (_('Location'), {
            'fields': (
                'current_latitude', 'current_longitude', 'last_location_update'
            ),
            'classes': ('collapse',)
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_practitioner', 'is_supervisor', 
                'is_staff', 'is_superuser', 'groups', 'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    # Fields for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'phone_number', 'email', 'first_name', 'last_name',
                'password1', 'password2', 'employee_id', 'department',
                'position', 'is_practitioner', 'is_supervisor'
            ),
        }),
    )
    
    def get_full_name(self, obj):
        """Display full name in admin."""
        return obj.get_full_name() or obj.phone_number
    get_full_name.short_description = 'Full Name'
    get_full_name.admin_order_field = 'last_name'
    
    def get_queryset(self, request):
        """Optimize queryset for admin list view."""
        qs = super().get_queryset(request)
        return qs.select_related()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of superusers by non-superusers."""
        if obj and obj.is_superuser and not request.user.is_superuser:
            return False
        return super().has_delete_permission(request, obj)
