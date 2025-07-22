from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with phone number authentication.
    """
    phone_number = serializers.CharField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = (
            'phone_number', 'email', 'first_name', 'last_name',
            'employee_id', 'department', 'position', 'password', 'password_confirm',
            'emergency_contact_name', 'emergency_contact_phone'
        )
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        # Remove password_confirm from validated_data
        validated_data.pop('password_confirm', None)
        
        # Create user
        user = User.objects.create_user(
            phone_number=validated_data['phone_number'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
            employee_id=validated_data.get('employee_id'),
            department=validated_data.get('department'),
            position=validated_data.get('position'),
            emergency_contact_name=validated_data.get('emergency_contact_name'),
            emergency_contact_phone=validated_data.get('emergency_contact_phone'),
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login with phone number and password.
    """
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        password = attrs.get('password')
        
        if phone_number and password:
            # Authenticate user
            user = authenticate(
                request=self.context.get('request'),
                username=phone_number,  # Django uses 'username' parameter
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "phone_number" and "password".'
            )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    display_name = serializers.CharField(read_only=True)
    has_current_location = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'phone_number', 'email', 'first_name', 'last_name',
            'full_name', 'display_name', 'employee_id', 'department', 
            'position', 'is_practitioner', 'is_supervisor',
            'profile_picture', 'emergency_contact_name', 
            'emergency_contact_phone', 'has_current_location',
            'last_location_update', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'phone_number', 'created_at', 'updated_at',
            'is_practitioner', 'is_supervisor', 'last_location_update'
        )


class UserLocationUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user's current location.
    """
    latitude = serializers.DecimalField(
        source='current_latitude',
        max_digits=22,
        decimal_places=16,
        required=True
    )
    longitude = serializers.DecimalField(
        source='current_longitude',
        max_digits=22,
        decimal_places=16,
        required=True
    )
    
    class Meta:
        model = User
        fields = ('latitude', 'longitude')
    
    def update(self, instance, validated_data):
        instance.current_latitude = validated_data.get('current_latitude')
        instance.current_longitude = validated_data.get('current_longitude')
        instance.last_location_update = timezone.now()
        instance.save(update_fields=[
            'current_latitude', 'current_longitude', 'last_location_update'
        ])
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for changing user password.
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password]
    )
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class UserListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing users (for admin/supervisor use).
    """
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    active_sessions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'phone_number', 'full_name', 'employee_id',
            'department', 'position', 'is_practitioner', 'is_supervisor',
            'is_active', 'last_login', 'active_sessions_count'
        )
    
    def get_active_sessions_count(self, obj):
        """Get count of active sessions for this user."""
        return obj.clock_sessions.filter(status='active').count()
