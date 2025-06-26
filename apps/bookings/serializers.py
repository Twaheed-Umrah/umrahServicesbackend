from rest_framework import serializers
from .models import Booking, BookingTraveler, QuickBooking
from apps.packages.serializers import PackageSerializer

class BookingTravelerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingTraveler
        fields = ['id', 'name', 'age', 'gender', 'traveler_type', 'passport_number']

class BookingSerializer(serializers.ModelSerializer):
    travelers = BookingTravelerSerializer(many=True, required=False)
    package_details = PackageSerializer(source='package', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    customer_name = serializers.CharField(read_only=True)
    total_travelers = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'booking_number', 'first_name', 'last_name', 'email', 'mobile_no',
            'passport_no', 'place_of_issue', 'address', 'travel_month', 'departure_city',
             'package_details', 'package_name', 'package_days', 
            'room_sharing', 'flight', 'special_request', 'adult_price', 'total_adults',
            'total_adult_price', 'child_price', 'total_children', 'total_child_price',
            'infant_price', 'total_infants', 'total_infant_price', 'total_price',
            'discount_percentage', 'discount_amount', 'advance_payment', 'payable_amount',
            'balance', 'payment_type', 'status', 'remarks', 'created_by', 'created_by_name',
            'customer_name', 'total_travelers', 'travelers', 'created_at', 'updated_at'
        ]
        read_only_fields = ['booking_number', 'total_adult_price', 'total_child_price', 
                           'total_infant_price', 'total_price', 'discount_amount', 
                           'payable_amount', 'balance', 'created_by']  # Add created_by here

    def create(self, validated_data):
        travelers_data = validated_data.pop('travelers', [])
        validated_data['created_by'] = self.context['request'].user
        booking = Booking.objects.create(**validated_data)
        
        for traveler_data in travelers_data:
            BookingTraveler.objects.create(booking=booking, **traveler_data)
        
        return booking

    def update(self, instance, validated_data):
        travelers_data = validated_data.pop('travelers', [])
        
        # Update booking fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update travelers
        if travelers_data:
            # Clear existing travelers
            instance.travelers.all().delete()
            # Create new travelers
            for traveler_data in travelers_data:
                BookingTraveler.objects.create(booking=instance, **traveler_data)
        
        return instance


class QuickBookingSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    customer_name = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = QuickBooking
        fields = [
            'id', 'booking_number', 'first_name', 'last_name', 'email', 'mobile',
            'travel_month', 'destination', 'number_of_travelers', 'budget',
            'payment', 'dues', 'total_amount', 'payment_status',
            'preferred_payment', 'created_by', 'created_by_name', 'customer_name',
            'is_converted_to_full_booking', 'converted_booking', 'created_at', 'updated_at'
        ]
        read_only_fields = ['booking_number', 'dues', 'total_amount', 'payment_status',
                           'is_converted_to_full_booking', 'converted_booking', 'created_by']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return QuickBooking.objects.create(**validated_data)

    def validate(self, data):
        """Validate that payment doesn't exceed budget"""
        budget = data.get('budget', 0)
        payment = data.get('payment', 0)
        
        if payment > budget:
            raise serializers.ValidationError("Payment amount cannot exceed budget.")
        
        return data

class BookingReceiptSerializer(serializers.ModelSerializer):
    """Serializer for generating booking receipts/bills"""
    travelers = BookingTravelerSerializer(many=True, read_only=True)
    package_details = PackageSerializer(source='package', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    customer_name = serializers.CharField(read_only=True)
    total_travelers = serializers.IntegerField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'booking_number', 'first_name', 'last_name', 'customer_name', 'email', 
            'mobile_no', 'address', 'travel_month', 'departure_city', 'package_name',
            'package_days', 'total_adults', 'total_children', 'total_infants', 
            'total_travelers', 'adult_price', 'total_adult_price', 'child_price',
            'total_child_price', 'infant_price', 'total_infant_price', 'total_price',
            'discount_percentage', 'discount_amount', 'advance_payment', 'balance',
            'payment_type', 'special_request', 'travelers', 'package_details',
            'created_by_name', 'created_at'
        ]


class QuickBookingReceiptSerializer(serializers.ModelSerializer):
    """Serializer for generating quick booking receipts"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    customer_name = serializers.CharField(read_only=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    payment_status = serializers.CharField(read_only=True)

    class Meta:
        model = QuickBooking
        fields = [
            'booking_number', 'first_name', 'last_name', 'customer_name', 'email',
            'mobile', 'travel_month', 'destination', 'number_of_travelers', 
            'budget', 'payment', 'dues', 'total_amount', 'payment_status',
            'preferred_payment', 'created_by_name', 'created_at'
        ]