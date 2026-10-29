from rest_framework import serializers
from .models import Booking, BookingTraveler, QuickBooking, SupportTicket, Quotation, QuotationHotel, QuotationActivity
from apps.packages.serializers import PackageSerializer

class BookingTravelerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingTraveler
        fields = ['id', 'name', 'age', 'gender', 'traveler_type', 'passport_number', 'passport_expiry', 'passport_scan', 'photo', 'visa_status', 'relationship', 'special_assistance', 'is_repeat_pilgrim']

class BookingSerializer(serializers.ModelSerializer):
    travelers = BookingTravelerSerializer(many=True, required=False)
    package_details = PackageSerializer(source='package', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    customer_name = serializers.CharField(read_only=True)
    total_travelers = serializers.IntegerField(read_only=True)
    total_direct_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    gross_profit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    profit_margin_pct = serializers.FloatField(read_only=True)

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
            'balance', 'payment_type', 'status', 'hotel_status', 'flight_status', 'visa_status',
            'airline', 'flight_number', 'pnr_number', 'departure_airport', 'arrival_airport', 'baggage_allowance',
            'makkah_hotel', 'makkah_checkin', 'makkah_checkout', 'madinah_hotel', 'madinah_checkin', 'madinah_checkout', 'hotel_booking_ref',
            'transport_type', 'ziyarat_included',
            'cost_hotel', 'cost_flight', 'cost_visa', 'cost_transport', 'cost_other',
            'total_direct_cost', 'gross_profit', 'profit_margin_pct',
            'remarks', 'created_by', 'created_by_name',
            'customer_name', 'total_travelers', 'travelers', 'created_at', 'updated_at'
        ]
        read_only_fields = ['booking_number', 'total_adult_price', 'total_child_price', 
                           'total_infant_price', 'total_price', 'discount_amount', 
                           'payable_amount', 'balance', 'total_direct_cost', 'gross_profit', 'profit_margin_pct', 'created_by']  # Add created_by here

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
    total_direct_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    gross_profit = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    profit_margin_pct = serializers.FloatField(read_only=True)

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


class SupportTicketSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    booking_number = serializers.CharField(source='booking.booking_number', read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'ticket_number', 'booking', 'booking_number',
            'category', 'category_display', 'priority', 'priority_display',
            'status', 'status_display', 'subject', 'description',
            'resolution_notes', 'assigned_to', 'assigned_to_name',
            'created_by', 'created_by_name', 'resolved_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'ticket_number', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


from decimal import Decimal

class QuotationHotelSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuotationHotel
        fields = [
            'id', 'city', 'hotel_name', 'hotel_rating', 'distance_to_haram',
            'check_in', 'check_out', 'nights', 'room_type', 'room_count', 'occupancy',
            'meal_plan', 'cost_per_night', 'total_hotel_cost', 'customer_notes'
        ]


class QuotationActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = QuotationActivity
        fields = ['id', 'action', 'notes', 'user', 'user_name', 'created_at']
        read_only_fields = ['id', 'user', 'user_name', 'created_at']


class QuotationSerializer(serializers.ModelSerializer):
    hotels = QuotationHotelSerializer(many=True, required=False)
    activities = QuotationActivitySerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    journey_type_display = serializers.CharField(source='get_journey_type_display', read_only=True)
    package_category_display = serializers.CharField(source='get_package_category_display', read_only=True)
    template_style_display = serializers.CharField(source='get_template_style_display', read_only=True)
    total_travelers = serializers.IntegerField(read_only=True)
    converted_booking_number = serializers.CharField(source='converted_booking.booking_number', read_only=True)

    class Meta:
        model = Quotation
        fields = [
            'id', 'quotation_number', 'version', 'parent_quotation', 'status', 'status_display',
            'template_style', 'template_style_display', 'quotation_date', 'valid_until',
            'created_by', 'created_by_name', 'prepared_by_name', 'branch',
            'lead', 'contact_name', 'mobile_no', 'email', 'city', 'nationality',
            'journey_type', 'journey_type_display', 'package', 'package_name',
            'package_category', 'package_category_display', 'departure_city',
            'departure_date', 'return_date', 'duration_days', 'special_requirements',
            'adults_count', 'children_count', 'infants_count', 'room_sharing', 'total_travelers',
            'flight_included', 'airline', 'flight_routing', 'departure_airport', 'arrival_airport', 'baggage_allowance',
            'flight_cost_per_pax', 'total_flight_cost',
            'transport_included', 'transport_type', 'transport_route', 'total_transport_cost',
            'ziyarat_included', 'ziyarat_details',
            'visa_included', 'visa_type', 'visa_cost_per_pax', 'total_visa_cost',
            'insurance_included', 'insurance_cost', 'zamzam_included', 'laundry_included', 'guide_included',
            'other_services_cost',
            'total_hotel_cost', 'total_supplier_cost',
            'pricing_method', 'markup_percentage', 'target_margin_percentage',
            'currency', 'exchange_rate', 'selling_price', 'discount_amount',
            'discount_reason', 'tax_percentage', 'tax_amount', 'total_customer_price',
            'estimated_gross_profit', 'gross_margin_percentage',
            'requires_discount_approval', 'is_approved', 'approved_by',
            'inclusions', 'exclusions', 'terms_and_conditions',
            'deposit_amount', 'deposit_due_date', 'second_installment', 'second_installment_due_date',
            'balance_amount', 'balance_due_date',
            'converted_booking', 'converted_booking_number', 'converted_at',
            'next_followup_at', 'last_sent_at',
            'hotels', 'activities', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'quotation_number', 'version', 'total_hotel_cost',
            'total_supplier_cost', 'tax_amount', 'total_customer_price',
            'estimated_gross_profit', 'gross_margin_percentage',
            'requires_discount_approval', 'created_by', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        hotels_data = validated_data.pop('hotels', [])
        user = self.context['request'].user
        validated_data['created_by'] = user
        if not validated_data.get('prepared_by_name'):
            validated_data['prepared_by_name'] = user.get_full_name() or user.username
        
        quotation = Quotation.objects.create(**validated_data)

        total_hotel_cost = Decimal('0.00')
        for h_data in hotels_data:
            hotel = QuotationHotel.objects.create(quotation=quotation, **h_data)
            total_hotel_cost += hotel.total_hotel_cost

        quotation.total_hotel_cost = total_hotel_cost
        quotation.save()

        QuotationActivity.objects.create(
            quotation=quotation,
            user=user,
            action='Created Quotation',
            notes=f"Quotation {quotation.quotation_number} initialized with {len(hotels_data)} hotel(s). Total price: {quotation.currency} {quotation.total_customer_price}"
        )
        return quotation

    def update(self, instance, validated_data):
        hotels_data = validated_data.pop('hotels', None)
        user = self.context['request'].user

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if hotels_data is not None:
            instance.hotels.all().delete()
            total_hotel_cost = Decimal('0.00')
            for h_data in hotels_data:
                hotel = QuotationHotel.objects.create(quotation=instance, **h_data)
                total_hotel_cost += hotel.total_hotel_cost
            instance.total_hotel_cost = total_hotel_cost

        instance.save()

        QuotationActivity.objects.create(
            quotation=instance,
            user=user,
            action='Updated Quotation',
            notes=f"Updated quotation details. Total price: {instance.currency} {instance.total_customer_price}"
        )
        return instance

