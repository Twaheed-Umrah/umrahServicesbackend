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
    
    HOTEL_STATUS_CHOICES = [
        ('unassigned', 'Unassigned'),
        ('reserved', 'Reserved'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
    ]
    
    FLIGHT_STATUS_CHOICES = [
        ('not_required', 'Not Required'),
        ('requested', 'Requested'),
        ('booked', 'Booked'),
        ('ticketed', 'Ticketed'),
        ('cancelled', 'Cancelled'),
    ]

    VISA_STATUS_CHOICES = [
        ('not_required', 'Not Required'),
        ('documents_pending', 'Documents Pending'),
        ('applied', 'Applied'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
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
    
    # Segregated Operational Statuses (Blueprint Module 5 & 8)
    hotel_status = models.CharField(max_length=20, choices=HOTEL_STATUS_CHOICES, default='unassigned')
    flight_status = models.CharField(max_length=20, choices=FLIGHT_STATUS_CHOICES, default='not_required')
    visa_status = models.CharField(max_length=20, choices=VISA_STATUS_CHOICES, default='documents_pending')

    # Flights & Ticketing Details (Module 11)
    airline = models.CharField(max_length=100, blank=True, null=True)
    flight_number = models.CharField(max_length=50, blank=True, null=True)
    pnr_number = models.CharField(max_length=20, blank=True, null=True)
    departure_airport = models.CharField(max_length=100, blank=True, null=True)
    arrival_airport = models.CharField(max_length=100, blank=True, null=True)
    baggage_allowance = models.CharField(max_length=50, blank=True, null=True, default='2 x 23kg + 7kg Hand')

    # Hotel & Room Allocation Details (Module 12)
    makkah_hotel = models.CharField(max_length=255, blank=True, null=True)
    makkah_checkin = models.DateField(blank=True, null=True)
    makkah_checkout = models.DateField(blank=True, null=True)
    madinah_hotel = models.CharField(max_length=255, blank=True, null=True)
    madinah_checkin = models.DateField(blank=True, null=True)
    madinah_checkout = models.DateField(blank=True, null=True)
    hotel_booking_ref = models.CharField(max_length=100, blank=True, null=True)

    # Transport & Ziyarat Details (Module 13)
    transport_type = models.CharField(max_length=100, blank=True, null=True, default='Bus')
    ziyarat_included = models.BooleanField(default=True)

    # Direct Costs & Profitability (Module 16)
    cost_hotel = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_flight = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_visa = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_transport = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost_other = models.DecimalField(max_digits=10, decimal_places=2, default=0)

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

    @property
    def total_direct_cost(self):
        return self.cost_hotel + self.cost_flight + self.cost_visa + self.cost_transport + self.cost_other

    @property
    def gross_profit(self):
        return self.total_price - self.total_direct_cost

    @property
    def profit_margin_pct(self):
        if self.total_price and self.total_price > 0:
            return round(float(self.gross_profit / self.total_price) * 100, 2)
        return 0.0

    def save(self, *args, **kwargs):
        if not self.booking_number:
            import uuid
            self.booking_number = f"BK{str(uuid.uuid4())[:8].upper()}"
        
        # Auto-calculate totals safely
        if self.adult_price is not None and self.total_adults is not None:
            self.total_adult_price = self.adult_price * self.total_adults
        elif not self.total_adult_price:
            self.total_adult_price = self.total_price or Decimal('0.00')

        if self.child_price is not None and self.total_children is not None:
            self.total_child_price = self.child_price * self.total_children
        elif not self.total_child_price:
            self.total_child_price = Decimal('0.00')

        if self.infant_price is not None and self.total_infants is not None:
            self.total_infant_price = self.infant_price * self.total_infants
        elif not self.total_infant_price:
            self.total_infant_price = Decimal('0.00')
        
        # Calculate total price before discount
        subtotal = (self.total_adult_price or Decimal('0.00')) + (self.total_child_price or Decimal('0.00')) + (self.total_infant_price or Decimal('0.00'))
        if subtotal > 0 and (not self.total_price or self.total_price == 0):
            disc_pct = self.discount_percentage or Decimal('0.00')
            self.discount_amount = (subtotal * disc_pct) / Decimal('100.00')
            self.total_price = subtotal - self.discount_amount

        if not self.payable_amount:
            self.payable_amount = self.total_price or Decimal('0.00')

        adv = self.advance_payment or Decimal('0.00')
        self.balance = max(Decimal('0.00'), (self.payable_amount or Decimal('0.00')) - adv)
        
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
    passport_expiry = models.DateField(null=True, blank=True)
    passport_scan = models.FileField(upload_to='traveler_passports/', null=True, blank=True)
    photo = models.ImageField(upload_to='traveler_photos/', null=True, blank=True)
    visa_status = models.CharField(max_length=30, default='documents_pending')
    relationship = models.CharField(max_length=50, blank=True, null=True, default='relative')
    special_assistance = models.CharField(max_length=100, blank=True, null=True, default='none')
    is_repeat_pilgrim = models.BooleanField(default=False)
    
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

class SupportTicket(TimestampMixin):
    """Module 20: Complaints & Customer Support"""
    CATEGORY_CHOICES = [
        ('flight', 'Flight Delay / Cancellation'),
        ('hotel', 'Hotel Room / Check-in Issue'),
        ('visa', 'Visa Status / MOFA Delay'),
        ('transport', 'Ground Transport / Driver Issue'),
        ('medical', 'Medical / Emergency Assistance'),
        ('other', 'General Complaint / Inquiry'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('emergency', 'Emergency / In-Trip SOS'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    ticket_number = models.CharField(max_length=20, unique=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='support_tickets')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='hotel')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    resolution_notes = models.TextField(blank=True, null=True)
    assigned_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets')
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='reported_tickets')
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.subject} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            import uuid
            self.ticket_number = f"TCK{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)


import datetime
from decimal import Decimal
from django.utils import timezone
from django.conf import settings

class Quotation(TimestampMixin):
    """
    Module 6: Quotation & Costing Specification
    Handles dynamic quotation creation, costing engine, multi-template PDF,
    revision management, and 1-click booking conversion.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('ready', 'Ready to Send'),
        ('sent', 'Sent to Customer'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('converted', 'Converted to Booking'),
        ('expired', 'Expired'),
    ]

    JOURNEY_TYPE_CHOICES = [
        ('umrah', 'Umrah'),
        ('hajj', 'Hajj'),
        ('combined', 'Hajj & Umrah Combined'),
        ('ziyarat', 'Ziyarat / Tour'),
    ]

    PACKAGE_CATEGORY_CHOICES = [
        ('economy', 'Economy (3 Star)'),
        ('standard', 'Standard (4 Star)'),
        ('premium', 'Premium (5 Star)'),
        ('luxury', 'VIP / Luxury Haram View'),
    ]

    PRICING_METHOD_CHOICES = [
        ('markup', 'Markup on Cost (%)'),
        ('target_margin', 'Target Gross Margin (%)'),
        ('manual', 'Manual Selling Price'),
    ]

    TEMPLATE_STYLE_CHOICES = [
        ('royal_emerald', 'Royal Emerald (Islamic Heritage)'),
        ('modern_minimalist', 'Modern Minimalist (Slate & Indigo)'),
        ('executive_deluxe', 'Executive Deluxe (Corporate Navy)'),
        ('compact_quick', 'Compact Quick Quote (WhatsApp Flyer)'),
    ]

    # Identifiers & Versioning
    quotation_number = models.CharField(max_length=40, unique=True, db_index=True)
    version = models.PositiveIntegerField(default=1)
    parent_quotation = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='revisions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    template_style = models.CharField(max_length=30, choices=TEMPLATE_STYLE_CHOICES, default='royal_emerald')

    # Dates
    quotation_date = models.DateField(default=datetime.date.today)
    valid_until = models.DateField(null=True, blank=True)

    # Agency & Agent
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_quotations')
    prepared_by_name = models.CharField(max_length=150, blank=True, null=True)
    branch = models.CharField(max_length=100, default='Head Office')

    # Customer / Lead Details
    lead = models.ForeignKey('crm.Lead', on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    contact_name = models.CharField(max_length=150)
    mobile_no = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=50, default='Indian')

    # Trip & Package Details
    journey_type = models.CharField(max_length=20, choices=JOURNEY_TYPE_CHOICES, default='umrah')
    package = models.ForeignKey('packages.Package', on_delete=models.SET_NULL, null=True, blank=True, related_name='quotations')
    package_name = models.CharField(max_length=255)
    package_category = models.CharField(max_length=20, choices=PACKAGE_CATEGORY_CHOICES, default='standard')
    departure_city = models.CharField(max_length=100, default='Mumbai')
    departure_date = models.DateField(null=True, blank=True)
    return_date = models.DateField(null=True, blank=True)
    duration_days = models.PositiveIntegerField(default=15)
    special_requirements = models.TextField(blank=True, null=True)

    # Pax & Occupancy
    adults_count = models.PositiveIntegerField(default=1)
    children_count = models.PositiveIntegerField(default=0)
    infants_count = models.PositiveIntegerField(default=0)
    room_sharing = models.CharField(max_length=20, default='quad') # single, double, triple, quad, family

    # Flights & Transport
    flight_included = models.BooleanField(default=True)
    airline = models.CharField(max_length=100, blank=True, null=True, default='Saudi Arabian Airlines')
    flight_routing = models.CharField(max_length=255, blank=True, null=True, default='Direct Flight (BOM - JED - BOM)')
    departure_airport = models.CharField(max_length=100, blank=True, null=True, default='BOM')
    arrival_airport = models.CharField(max_length=100, blank=True, null=True, default='JED')
    baggage_allowance = models.CharField(max_length=100, default='2 x 23kg + 7kg Hand Baggage')
    flight_cost_per_pax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_flight_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    transport_included = models.BooleanField(default=True)
    transport_type = models.CharField(max_length=100, default='AC Luxury Bus / Private GMC')
    transport_route = models.CharField(max_length=255, default='JED Airport - Makkah - Madinah - Airport + Holy Ziyarat')
    total_transport_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    ziyarat_included = models.BooleanField(default=True)
    ziyarat_details = models.TextField(blank=True, null=True, default='Makkah Ziyarat: Jabal al-Noor (Cave of Hira), Cave of Thawr, Mina, Arafat, Muzdalifah. Madinah Ziyarat: Masjid Quba, Mount Uhud, Masjid al-Qiblatayn, Seven Mosques.')

    # Visa & Additional Services
    visa_included = models.BooleanField(default=True)
    visa_type = models.CharField(max_length=50, default='Umrah Electronic Visa')
    visa_cost_per_pax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_visa_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    insurance_included = models.BooleanField(default=True)
    insurance_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    zamzam_included = models.BooleanField(default=True)
    laundry_included = models.BooleanField(default=False)
    guide_included = models.BooleanField(default=True)
    other_services_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Costing Engine (Internal / Supplier Costs - NEVER EXPOSED IN PDF)
    total_hotel_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_supplier_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Pricing Engine (Customer Facing)
    pricing_method = models.CharField(max_length=20, choices=PRICING_METHOD_CHOICES, default='markup')
    markup_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'))
    target_margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('15.00'))
    currency = models.CharField(max_length=10, default='INR')
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('1.0000'))

    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_reason = models.CharField(max_length=255, blank=True, null=True)
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('5.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_customer_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    # Profitability & Approval Controls
    estimated_gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    gross_margin_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    requires_discount_approval = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_quotations')

    # Inclusions, Exclusions & Policies
    inclusions = models.TextField(blank=True, null=True, default='- Direct / Connecting Flights with baggage allowance\n- Hotel accommodation in Makkah & Madinah near Haram\n- Umrah Electronic Visa & Mandatory Saudi Medical Insurance\n- Full ground transport in AC VIP buses / GMC\n- Complete holy Ziyarat in Makkah & Madinah\n- Complimentary 5-liter Zamzam water can per pilgrim\n- 24/7 Experienced Mutawwif / Pilgrim Guide assistance')
    exclusions = models.TextField(blank=True, null=True, default='- Personal room service, telephone calls, laundry (unless specified)\n- Individual excess luggage charges\n- Optional local activities not mentioned in itinerary\n- Tips & porterage at airports and hotels')
    terms_and_conditions = models.TextField(blank=True, null=True, default='1. Quotation is valid strictly up to the validity date mentioned. Hotel rates & flight fares are subject to availability.\n2. Passports must have minimum 6 months validity from travel date.\n3. Deposit is required to block seats and hotel allocations.\n4. Balance payment must be settled at least 15 days prior to departure.\n5. Cancellation fees apply as per Saudi Ministry and Airline regulations.')

    # Payment Schedule
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    deposit_due_date = models.DateField(null=True, blank=True)
    second_installment = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    second_installment_due_date = models.DateField(null=True, blank=True)
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    balance_due_date = models.DateField(null=True, blank=True)

    # Conversion Link
    converted_booking = models.OneToOneField(Booking, on_delete=models.SET_NULL, null=True, blank=True, related_name='source_quotation')
    converted_at = models.DateTimeField(null=True, blank=True)

    # Follow-up
    next_followup_at = models.DateTimeField(null=True, blank=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.quotation_number} - {self.contact_name} ({self.get_status_display()})"

    @property
    def total_travelers(self):
        return (self.adults_count or 0) + (self.children_count or 0) + (self.infants_count or 0)

    def generate_quotation_number(self):
        if self.parent_quotation:
            parent_base = self.parent_quotation.quotation_number.split('-V')[0]
            return f"{parent_base}-V{self.version}"

        now = timezone.now()
        prefix = f"QT-{now.strftime('%Y%m')}"
        last_quote = Quotation.objects.filter(quotation_number__startswith=prefix).order_by('-id').first()
        if last_quote:
            try:
                base_part = last_quote.quotation_number.split('-')[2].split('/')[0].split('-V')[0]
                next_seq = int(base_part) + 1
            except (IndexError, ValueError):
                next_seq = Quotation.objects.count() + 1001
        else:
            next_seq = 1001
        
        if self.version > 1:
            return f"{prefix}-{next_seq:04d}-V{self.version}"
        return f"{prefix}-{next_seq:04d}"

    def calculate_totals(self):
        """
        Calculates supplier costs, selling price, discounts, taxes, and margins.
        """
        total_pax = Decimal(self.total_travelers or 1)
        if self.flight_included and self.flight_cost_per_pax > 0 and self.total_flight_cost == 0:
            self.total_flight_cost = self.flight_cost_per_pax * total_pax

        if self.visa_included and self.visa_cost_per_pax > 0 and self.total_visa_cost == 0:
            self.total_visa_cost = self.visa_cost_per_pax * total_pax

        self.total_supplier_cost = (
            (self.total_hotel_cost or Decimal('0.00')) +
            (self.total_flight_cost or Decimal('0.00')) +
            (self.total_transport_cost or Decimal('0.00')) +
            (self.total_visa_cost or Decimal('0.00')) +
            (self.other_services_cost or Decimal('0.00'))
        )

        if self.pricing_method == 'markup':
            markup_factor = Decimal('1.00') + (Decimal(self.markup_percentage or 0) / Decimal('100.00'))
            self.selling_price = (self.total_supplier_cost * markup_factor).quantize(Decimal('0.01'))
        elif self.pricing_method == 'target_margin':
            margin_rate = Decimal(self.target_margin_percentage or 0) / Decimal('100.00')
            if margin_rate < Decimal('1.00'):
                self.selling_price = (self.total_supplier_cost / (Decimal('1.00') - margin_rate)).quantize(Decimal('0.01'))
            else:
                self.selling_price = self.total_supplier_cost

        discounted = max(Decimal('0.00'), self.selling_price - (self.discount_amount or Decimal('0.00')))
        self.tax_amount = (discounted * (Decimal(self.tax_percentage or 0) / Decimal('100.00'))).quantize(Decimal('0.01'))
        self.total_customer_price = (discounted + self.tax_amount).quantize(Decimal('0.01'))

        self.estimated_gross_profit = (discounted - self.total_supplier_cost).quantize(Decimal('0.01'))
        if discounted > Decimal('0.00'):
            self.gross_margin_percentage = ((self.estimated_gross_profit / discounted) * Decimal('100.00')).quantize(Decimal('0.01'))
        else:
            self.gross_margin_percentage = Decimal('0.00')

        if self.discount_amount > Decimal('0.00') and self.gross_margin_percentage < Decimal('8.00'):
            self.requires_discount_approval = True
        else:
            self.requires_discount_approval = False

    def save(self, *args, **kwargs):
        if isinstance(self.quotation_date, datetime.datetime):
            self.quotation_date = self.quotation_date.date()
        if self.valid_until and isinstance(self.valid_until, datetime.datetime):
            self.valid_until = self.valid_until.date()
        if not self.quotation_number:
            self.quotation_number = self.generate_quotation_number()
        
        if not self.valid_until and self.quotation_date:
            self.valid_until = self.quotation_date + datetime.timedelta(days=7)

        self.calculate_totals()
        super().save(*args, **kwargs)


class QuotationHotel(TimestampMixin):
    CITY_CHOICES = [
        ('makkah', 'Makkah Mukarramah'),
        ('madinah', 'Madinah Munawwarah'),
        ('jeddah', 'Jeddah'),
        ('other', 'Other City'),
    ]

    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='hotels')
    city = models.CharField(max_length=20, choices=CITY_CHOICES, default='makkah')
    hotel_name = models.CharField(max_length=255)
    hotel_rating = models.CharField(max_length=20, default='5 Star')
    distance_to_haram = models.CharField(max_length=100, blank=True, null=True, default='350m from Haram')
    check_in = models.DateField(null=True, blank=True)
    check_out = models.DateField(null=True, blank=True)
    nights = models.PositiveIntegerField(default=7)
    room_type = models.CharField(max_length=50, default='Quad Sharing Room')
    room_count = models.PositiveIntegerField(default=1)
    occupancy = models.PositiveIntegerField(default=4, help_text='Persons per room')
    meal_plan = models.CharField(max_length=50, default='Buffet Breakfast')
    cost_per_night = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_hotel_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    customer_notes = models.CharField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.cost_per_night > 0 and self.nights > 0 and self.room_count > 0:
            self.total_hotel_cost = (self.cost_per_night * self.nights * self.room_count).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)


class QuotationActivity(TimestampMixin):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='activities')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

