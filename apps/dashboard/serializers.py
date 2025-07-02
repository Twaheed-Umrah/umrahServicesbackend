# serializers.py - Updated with user-specific logic

from rest_framework import serializers
from django.utils import timezone
from apps.enquiries.models import ContactUs, APIKey

class ContactUsSerializer(serializers.ModelSerializer):
    """Serializer for ContactUs model with API key tracking"""
    
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    status = serializers.CharField(read_only=True)
    api_key_name = serializers.CharField(source='api_key.name', read_only=True)
    api_key_user = serializers.CharField(source='api_key.user.get_full_name', read_only=True)
    
    class Meta:
        model = ContactUs
        fields = [
            'id', 'name', 'email', 'phone', 'package_type', 'message',
            'is_processed', 'processed_by', 'processed_by_name', 'processed_at',
            'notes', 'status', 'created_at', 'updated_at', 'api_key',
            'api_key_name', 'api_key_user', 'ip_address', 'user_agent', 'referrer_url'
        ]
        read_only_fields = ['processed_by', 'processed_at', 'api_key_user', 'api_key_name']

    def create(self, validated_data):
        """Create new contact us entry with API key tracking"""
        # API key should be set when the enquiry is submitted through external API
        return ContactUs.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update contact us entry"""
        # If marking as processed, set processed_by and processed_at
        if validated_data.get('is_processed') and not instance.is_processed:
            validated_data['processed_by'] = self.context['request'].user
            validated_data['processed_at'] = timezone.now()
        
        return super().update(instance, validated_data)


class APIKeySerializer(serializers.ModelSerializer):
    """Serializer for API Key management"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    enquiry_count = serializers.SerializerMethodField()
    
    class Meta:
        model = APIKey
        fields = [
            'id', 'key', 'name', 'is_active', 'created_at', 'last_used', 
            'website_url', 'user', 'user_name', 'enquiry_count'
        ]
        read_only_fields = ['key', 'created_at', 'last_used', 'user']
    
    def get_enquiry_count(self, obj):
        """Get count of enquiries received through this API key"""
        return obj.contactus_set.count()

    def create(self, validated_data):
        """Create API key for the current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    
    bookings = serializers.DictField()
    amounts = serializers.DictField()
    enquiries = serializers.DictField()
    user_role = serializers.CharField()


class ChartDataSerializer(serializers.Serializer):
    """Serializer for chart data points"""
    
    name = serializers.CharField()
    value = serializers.IntegerField()


class BookingRevenueSerializer(serializers.Serializer):
    """Serializer for booking revenue chart data"""
    
    name = serializers.CharField()
    bookings = serializers.IntegerField()
    revenue = serializers.IntegerField()


class EnquiryDistributionSerializer(serializers.Serializer):
    """Serializer for enquiry distribution data"""
    
    name = serializers.CharField()
    value = serializers.IntegerField()
    color = serializers.CharField()


class RecentActivitySerializer(serializers.Serializer):
    """Serializer for recent activities"""
    
    type = serializers.CharField()
    title = serializers.CharField()
    description = serializers.CharField()
    amount = serializers.CharField(allow_null=True)
    time = serializers.CharField()
    created_by = serializers.CharField()


class UserSpecificContactUsSerializer(serializers.ModelSerializer):
    """Serializer for user-specific contact us queries"""
    
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    status = serializers.CharField(read_only=True)
    api_key_name = serializers.CharField(source='api_key.name', read_only=True)
    
    class Meta:
        model = ContactUs
        fields = [
            'id', 'name', 'email', 'phone', 'package_type', 'message',
            'is_processed', 'processed_by_name', 'processed_at',
            'status', 'created_at', 'api_key_name'
        ]
    
    def to_representation(self, instance):
        """Customize representation based on user role"""
        data = super().to_representation(instance)
        user = self.context['request'].user
        
        # Non-superadmin users should only see limited information
        if user.role != 'superadmin':
            # Remove sensitive information for non-superadmin users
            data.pop('processed_by_name', None)
            
        return data