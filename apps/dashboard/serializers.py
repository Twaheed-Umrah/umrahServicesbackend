# Add this to your existing serializers.py file

from rest_framework import serializers
from .models import ContactUs

class ContactUsSerializer(serializers.ModelSerializer):
    """Serializer for ContactUs model"""
    
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    status = serializers.CharField(read_only=True)
    
    class Meta:
        model = ContactUs
        fields = [
            'id', 'name', 'email', 'phone', 'package_type', 'message',
            'is_processed', 'processed_by', 'processed_by_name', 'processed_at',
            'notes', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['processed_by', 'processed_at']

    def create(self, validated_data):
        """Create new contact us entry"""
        return ContactUs.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update contact us entry"""
        # If marking as processed, set processed_by and processed_at
        if validated_data.get('is_processed') and not instance.is_processed:
            validated_data['processed_by'] = self.context['request'].user
            validated_data['processed_at'] = timezone.now()
        
        return super().update(instance, validated_data)


class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    
    bookings = serializers.DictField()
    amounts = serializers.DictField()
    enquiries = serializers.DictField()


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