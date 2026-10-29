from django.db import models
from apps.common.mixins import TimestampMixin
from django.conf import settings

class Package(TimestampMixin):
    PACKAGE_TYPE_CHOICES = [
        ('classic_hajj', 'Classic Hajj Package'),
        ('deluxe_hajj', 'Deluxe Hajj Package'),
        ('luxury_hajj', 'Luxury Hajj Package'),
        ('classic_umrah', 'Classic Umrah Package'),
        ('deluxe_umrah', 'Deluxe Umrah Package'),
        ('luxury_umrah', 'Luxury Umrah Package'),
        ('ramadan_20_days', 'First 20 Days Ramadan'),
        ('ramadan_18_days', 'Last 18 Days Ramadan'),
        ('ramadan_full_month', 'Full Month Ramadan Package'),
        ('umrah_classic', 'Classic Umrah Package'),
        ('umrah_delux', 'Delux Umrah Package'),
        ('umrah_luxury', 'Luxury Umrah Package'),
        ('hajj_classic', 'Classic Hajj Package'),
        ('hajj_delux', 'Delux Hajj Package'),
        ('hajj_luxury', 'Luxury Hajj Package'),
        ('ramadan_early', 'Early Ramadan Package'),
        ('ramadan_laylat', 'Laylat al-Qadr Package'),
        ('ramadan_full', 'Full Month Ramadan Package'),
    ]

    # Package Information
    name = models.CharField(max_length=255)
    description = models.TextField()
    package_type = models.CharField(max_length=50, choices=PACKAGE_TYPE_CHOICES)
    destination = models.CharField(max_length=255, default='Makkah & Madinah')
    duration_days = models.PositiveIntegerField(default=14)
    currency = models.CharField(max_length=10, default='INR')

    # Pricing & Multi-Occupancy Rates (Module 5 & 6)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base / Quad Sharing Price")
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0.00)
    single_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    double_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    triple_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quad_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    child_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    infant_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Inclusions, Exclusions & Features
    features = models.TextField(help_text="Features separated by new lines", blank=True, null=True)
    inclusions = models.TextField(blank=True, null=True)
    exclusions = models.TextField(blank=True, null=True)
    cancellation_policy = models.TextField(blank=True, null=True)

    # Media & Display Flags
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    show_on_agency_website = models.BooleanField(default=True, help_text="Show in public agency website feed")

    # Tenancy & Ownership
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_packages')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_packages')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_package_type_display()})"

    @property
    def title(self):
        """Backwards compatibility for enquiry packages"""
        return self.name

    def get_features_list(self):
        """Return features as a clean list"""
        if not self.features:
            return []
        return [f.strip() for f in self.features.split('\n') if f.strip()]


class PackageDeparture(TimestampMixin):
    """Specific dated departures with seat allotments (Module 5)"""
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PUBLISHED', 'Published / Open'),
        ('FULL', 'Capacity Full'),
        ('CLOSED', 'Closed'),
        ('ARCHIVED', 'Archived'),
    ]

    package = models.ForeignKey(Package, related_name='departures', on_delete=models.CASCADE)
    departure_date = models.DateField()
    return_date = models.DateField()
    departure_city = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(default=50)
    booked_count = models.PositiveIntegerField(default=0)
    cutoff_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PUBLISHED')

    class Meta:
        ordering = ['departure_date']

    def __str__(self):
        return f"{self.package.name} - {self.departure_city} ({self.departure_date})"

    @property
    def seats_available(self):
        return max(0, self.capacity - self.booked_count)


class Supplier(TimestampMixin):
    """Module 14: Supplier & Contract Management"""
    SUPPLIER_TYPE_CHOICES = [
        ('hotel', 'Hotel Accommodation'),
        ('airline', 'Airline / Ticketing Consolidator'),
        ('transport', 'Ground Transport & Ziyarat'),
        ('visa_agent', 'Visa Service Provider'),
        ('wholesaler', 'Package Wholesaler'),
        ('other', 'Other Supplier'),
    ]

    VERIFICATION_CHOICES = [
        ('unverified', 'Unverified'),
        ('under_review', 'Under Review'),
        ('verified', 'Verified Official Partner'),
        ('suspended', 'Suspended'),
    ]

    name = models.CharField(max_length=255)
    supplier_type = models.CharField(max_length=50, choices=SUPPLIER_TYPE_CHOICES)
    country = models.CharField(max_length=100, default='Saudi Arabia')
    city = models.CharField(max_length=100, default='Makkah')
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    license_reference = models.CharField(max_length=100, blank=True, null=True)
    verification_status = models.CharField(max_length=30, choices=VERIFICATION_CHOICES, default='verified')
    payment_terms = models.CharField(max_length=100, default='30 days net')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agency_suppliers')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_supplier_type_display()}) - {self.city}"
