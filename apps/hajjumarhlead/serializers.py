
from rest_framework import serializers
from .models import HajjUmrahBookingDemo, HajjUmrahBookingService

class HajjUmrahBookingDemoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HajjUmrahBookingDemo
        fields = [
            'id', 'selected_date', 'selected_time', 'name',
            'email', 'phone', 'business_plan', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_phone(self, value):
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value


class HajjUmrahBookingServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HajjUmrahBookingService
        fields = [
            'id', 'selected_date', 'selected_time', 'first_name', 'last_name',
            'email', 'phone', 'business_plan', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_phone(self, value):
        if not value:
            raise serializers.ValidationError("Phone number is required.")
        return value
