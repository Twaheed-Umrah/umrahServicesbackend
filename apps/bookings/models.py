from django.db import models
from apps.common.mixins import TimestampMixin

class Booking(TimestampMixin):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('net_banking', 'Net Banking'),
        ('cheque', 'Cheque'),
    ]
    
    SHARING_CHOICES = [
        ('single', 'Single'),
        ('double', 'Double'),
        ('triple', 'Triple'),
        ('quad', 'Quad'),
    ]

    # Basic Information
    booking_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True, db_index=True)
    mobile_no = models.CharField(max_length=15)
    
    # Passport Details
    passport_no = models.CharField(max_length=20, blank=True, null=True)
    place_of_issue = models.CharField(max_length=100, blank=True, null=True)
    address = models.TextField()
    
    # Travel Information
    travel_month = models.CharField(max_length=8, null=False, blank=False)
    departure_city = models.CharField(max_length=100)
    package_name = models.CharField(max_length=255)
    package_days = models.PositiveIntegerField()
    
    # Sharing Details
    room_sharing = models.CharField(max_length=20, choices=SHARING_CHOICES)
    flight = models.BooleanField(default=False)
    special_request = models.TextField(blank=True, null=True)
    
    # Adult Pricing
    adult_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_adults = models.PositiveIntegerField()
    total_adult_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Child Pricing
    child_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_children = models.PositiveIntegerField(default=0)
    total_child_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Infant Pricing
    infant_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_infants = models.PositiveIntegerField(default=0)
    total_infant_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Payment Details
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_payment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payable_amount = models.DecimalField(max_digits=10, decimal_places=2)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    
    # System Fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    remarks = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE)

    def __str__(self):
        return f"Booking {self.booking_number} - {self.first_name} {self.last_name}"

    @property
    def customer_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def total_travelers(self):
        return self.total_adults + self.total_children + self.total_infants

    def save(self, *args, **kwargs):
        if not self.booking_number:
            import uuid
            self.booking_number = f"BK{str(uuid.uuid4())[:8].upper()}"
        
        # Auto-calculate totals
        self.total_adult_price = self.adult_price * self.total_adults
        self.total_child_price = self.child_price * self.total_children
        self.total_infant_price = self.infant_price * self.total_infants
        
        # Calculate total price before discount
        subtotal = self.total_adult_price + self.total_child_price + self.total_infant_price
        self.discount_amount = (subtotal * self.discount_percentage) / 100
        self.total_price = subtotal - self.discount_amount
        self.payable_amount = self.total_price
        self.balance = self.total_price - self.advance_payment
        
        super().save(*args, **kwargs)


class BookingTraveler(TimestampMixin):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    TRAVELER_TYPE_CHOICES = [
        ('adult', 'Adult'),
        ('child', 'Child'),
        ('infant', 'Infant'),
    ]
    
    booking = models.ForeignKey(Booking, related_name='travelers', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    traveler_type = models.CharField(max_length=10, choices=TRAVELER_TYPE_CHOICES)
    passport_number = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.booking.booking_number}"




class QuickBooking(TimestampMixin):
    PAYMENT_PREFERENCE_CHOICES = [
        ('full_advance', 'Full Payment in Advance'),
        ('partial_advance', 'Partial Payment in Advance'),
        ('pay_later', 'Pay Later'),
    ]
    
    # Basic Information
    booking_number = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True, db_index=True)
    mobile = models.CharField(max_length=15)
    
    # Travel Details
    travel_month = models.CharField(max_length=8, null=False, blank=False)
    destination = models.CharField(max_length=255)
    number_of_travelers = models.PositiveIntegerField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    preferred_payment = models.CharField(max_length=20, choices=PAYMENT_PREFERENCE_CHOICES)
    
    # Payment Details
    payment = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Amount paid")
    dues = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Amount due")
    
    # System Fields
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE)
    is_converted_to_full_booking = models.BooleanField(default=False)
    converted_booking = models.ForeignKey('Booking', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Quick Booking {self.booking_number} - {self.first_name} {self.last_name}"

    @property
    def customer_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def total_amount(self):
        """Total amount (payment + dues)"""
        return self.payment + self.dues

    @property
    def payment_status(self):
        """Return payment status based on payment and dues"""
        if self.dues == 0:
            return "Fully Paid"
        elif self.payment == 0:
            return "Unpaid"
        else:
            return "Partially Paid"

    def save(self, *args, **kwargs):
        if not self.booking_number:
            import uuid
            self.booking_number = f"QB{str(uuid.uuid4())[:8].upper()}"
        
        # Auto-calculate dues based on budget and payment
        if self.budget and self.payment:
            self.dues = max(0, self.budget - self.payment)
        
        super().save(*args, **kwargs)