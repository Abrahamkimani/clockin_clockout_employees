from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    """
    Serializer for Client model with full details.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    full_address = serializers.CharField(read_only=True)
    location_coordinates = serializers.ReadOnlyField()
    
    class Meta:
        model = Client
        fields = (
            'id', 'client_id', 'first_name', 'last_name', 'full_name',
            'phone_number', 'email', 'street_address', 'city', 'state',
            'zip_code', 'full_address', 'latitude', 'longitude',
            'location_coordinates', 'is_active', 'care_level',
            'special_instructions', 'emergency_contact_name',
            'emergency_contact_phone', 'emergency_contact_relationship',
            'access_instructions', 'safety_notes', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class ClientListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing clients (summary view).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    full_address = serializers.CharField(read_only=True)
    recent_sessions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Client
        fields = (
            'id', 'client_id', 'full_name', 'full_address',
            'phone_number', 'is_active', 'care_level',
            'recent_sessions_count'
        )
    
    def get_recent_sessions_count(self, obj):
        """Get count of sessions in the last 30 days."""
        from django.utils import timezone
        from datetime import timedelta
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return obj.sessions.filter(clock_in_time__gte=thirty_days_ago).count()


class ClientCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new clients.
    """
    
    class Meta:
        model = Client
        fields = (
            'client_id', 'first_name', 'last_name', 'phone_number',
            'email', 'street_address', 'city', 'state', 'zip_code',
            'latitude', 'longitude', 'care_level', 'special_instructions',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship', 'access_instructions',
            'safety_notes'
        )
    
    def validate_client_id(self, value):
        """Ensure client_id is unique."""
        if Client.objects.filter(client_id=value).exists():
            raise serializers.ValidationError("Client ID already exists.")
        return value


class ClientLocationSerializer(serializers.ModelSerializer):
    """
    Serializer for client location information only.
    Used for GPS verification during clock-in.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    location_coordinates = serializers.ReadOnlyField()
    
    class Meta:
        model = Client
        fields = (
            'id', 'client_id', 'full_name', 'street_address',
            'city', 'state', 'latitude', 'longitude',
            'location_coordinates', 'access_instructions', 'safety_notes'
        )
