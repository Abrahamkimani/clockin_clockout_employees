from rest_framework import serializers
from django.utils import timezone
from .models import ClockSession, SessionLocationUpdate
from clients.serializers import ClientLocationSerializer
from authentication.serializers import UserProfileSerializer


class ClockInSerializer(serializers.ModelSerializer):
    """
    Serializer for clocking in - creating a new session.
    """
    latitude = serializers.DecimalField(
        source='clock_in_latitude',
        max_digits=22,
        decimal_places=16,
        required=True
    )
    longitude = serializers.DecimalField(
        source='clock_in_longitude',
        max_digits=22,
        decimal_places=16,
        required=True
    )
    accuracy = serializers.FloatField(
        source='clock_in_accuracy',
        required=False
    )
    
    class Meta:
        model = ClockSession
        fields = (
            'client', 'latitude', 'longitude', 'accuracy',
            'service_type', 'session_notes'
        )
    
    def create(self, validated_data):
        # Set clock-in time and practitioner from request
        validated_data['clock_in_time'] = timezone.now()
        validated_data['practitioner'] = self.context['request'].user
        validated_data['status'] = 'active'
        
        return super().create(validated_data)
    
    def validate(self, attrs):
        """Validate that practitioner doesn't have active sessions."""
        practitioner = self.context['request'].user
        active_sessions = ClockSession.objects.filter(
            practitioner=practitioner,
            status='active'
        )
        
        if active_sessions.exists():
            raise serializers.ValidationError(
                "You already have an active session. Please clock out first."
            )
        
        return attrs


class ClockOutSerializer(serializers.Serializer):
    """
    Serializer for clocking out - updating an existing session.
    """
    latitude = serializers.DecimalField(
        max_digits=22,
        decimal_places=16,
        required=True
    )
    longitude = serializers.DecimalField(
        max_digits=22,
        decimal_places=16,
        required=True
    )
    accuracy = serializers.FloatField(required=False)
    session_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, attrs):
        """Validate that there's an active session to clock out."""
        practitioner = self.context['request'].user
        try:
            active_session = ClockSession.objects.get(
                practitioner=practitioner,
                status='active'
            )
            attrs['session'] = active_session
        except ClockSession.DoesNotExist:
            raise serializers.ValidationError(
                "No active session found to clock out."
            )
        
        return attrs
    
    def save(self):
        """Clock out the active session."""
        session = self.validated_data['session']
        session.clock_out(
            latitude=self.validated_data['latitude'],
            longitude=self.validated_data['longitude'],
            accuracy=self.validated_data.get('accuracy'),
            notes=self.validated_data.get('session_notes')
        )
        return session


class ClockSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for ClockSession with full details.
    """
    practitioner = UserProfileSerializer(read_only=True)
    client = ClientLocationSerializer(read_only=True)
    duration_hours_minutes = serializers.CharField(read_only=True)
    session_date = serializers.DateField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ClockSession
        fields = (
            'session_id', 'practitioner', 'client', 'status',
            'clock_in_time', 'clock_in_latitude', 'clock_in_longitude',
            'clock_in_accuracy', 'clock_out_time', 'clock_out_latitude',
            'clock_out_longitude', 'clock_out_accuracy', 'duration_minutes',
            'duration_hours_minutes', 'session_date', 'session_notes',
            'service_type', 'auto_clock_out_time', 'auto_clock_out_reason',
            'distance_from_client_meters', 'location_verified',
            'requires_review', 'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at', 'is_active'
        )
        read_only_fields = (
            'session_id', 'created_at', 'updated_at', 'auto_clock_out_time',
            'auto_clock_out_reason', 'distance_from_client_meters',
            'location_verified', 'requires_review'
        )


class ClockSessionListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing sessions (summary view).
    """
    practitioner_name = serializers.CharField(
        source='practitioner.get_full_name',
        read_only=True
    )
    client_name = serializers.CharField(
        source='client.get_full_name',
        read_only=True
    )
    duration_hours_minutes = serializers.CharField(read_only=True)
    session_date = serializers.DateField(read_only=True)
    
    class Meta:
        model = ClockSession
        fields = (
            'session_id', 'practitioner_name', 'client_name', 'status',
            'clock_in_time', 'clock_out_time', 'duration_hours_minutes',
            'session_date', 'service_type', 'location_verified',
            'requires_review'
        )


class SessionLocationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for session location updates.
    """
    
    class Meta:
        model = SessionLocationUpdate
        fields = (
            'timestamp', 'latitude', 'longitude', 'accuracy', 'battery_level'
        )
        read_only_fields = ('timestamp',)


class ActiveSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for active session information.
    """
    client = ClientLocationSerializer(read_only=True)
    elapsed_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = ClockSession
        fields = (
            'session_id', 'client', 'clock_in_time', 'clock_in_latitude',
            'clock_in_longitude', 'service_type', 'elapsed_minutes'
        )
    
    def get_elapsed_minutes(self, obj):
        """Calculate elapsed time since clock-in."""
        if obj.clock_in_time:
            elapsed = timezone.now() - obj.clock_in_time
            return int(elapsed.total_seconds() / 60)
        return 0


class SessionReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for reviewing sessions (supervisor functionality).
    """
    review_notes = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = ClockSession
        fields = ('requires_review', 'review_notes')
    
    def update(self, instance, validated_data):
        """Update session review status."""
        instance.requires_review = validated_data.get('requires_review', False)
        instance.reviewed_by = self.context['request'].user
        instance.reviewed_at = timezone.now()
        
        # Add review notes to session notes
        review_notes = validated_data.get('review_notes')
        if review_notes:
            existing_notes = instance.session_notes or ""
            instance.session_notes = f"{existing_notes}\n\nReview Notes: {review_notes}".strip()
        
        instance.save()
        return instance
