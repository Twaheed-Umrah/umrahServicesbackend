from django.contrib import admin
from .models import Booking, BookingTraveler, QuickBooking


class BookingTravelerInline(admin.TabularInline):
    model = BookingTraveler
    extra = 0


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_number', 'customer_name', 'travel_month', 'departure_city',
        'package_name', 'total_travelers', 'status', 'payable_amount', 'balance'
    )
    list_filter = ('status', 'travel_month', 'payment_type')
    search_fields = ('booking_number', 'first_name', 'last_name',  'mobile_no')
    readonly_fields = ('total_adult_price', 'total_child_price', 'total_infant_price', 'total_price', 'discount_amount', 'payable_amount', 'balance')
    inlines = [BookingTravelerInline]


@admin.register(BookingTraveler)
class BookingTravelerAdmin(admin.ModelAdmin):
    list_display = ('name', 'booking', 'traveler_type', 'age', 'gender')
    list_filter = ('traveler_type', 'gender')
    search_fields = ('name', 'booking__booking_number')


@admin.register(QuickBooking)
class QuickBookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_number', 'customer_name', 'travel_month', 'destination',
        'number_of_travelers', 'budget', 'preferred_payment', 'is_converted_to_full_booking'
    )
    list_filter = ('preferred_payment', 'is_converted_to_full_booking', 'travel_month')
    search_fields = ('booking_number', 'first_name', 'last_name',  'mobile')
    readonly_fields = ('converted_booking',)

