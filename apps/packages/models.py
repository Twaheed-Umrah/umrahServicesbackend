from django.db import models
from apps.common.mixins import TimestampMixin

class Package(TimestampMixin):
    PACKAGE_TYPE_CHOICES = [
        ('classic_hajj', 'Classic Hajj'),
        ('deluxe_hajj', 'Deluxe Hajj'),
        ('luxury_hajj', 'Luxury Hajj'),
        ('classic_umrah', 'Classic Umrah'),
        ('deluxe_umrah', 'Deluxe Umrah'),
        ('luxury_umrah', 'Luxury Umrah'),
        ('ramadan_20_days', 'First 20 Days Ramadan'),
        ('ramadan_18_days', 'Last 18 Days Ramadan'),
        ('ramadan_full_month', 'Full Month Ramadan'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    package_type = models.CharField(max_length=50, choices=PACKAGE_TYPE_CHOICES)
    destination = models.CharField(max_length=255)
    duration_days = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,default=0.00)
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    # User who created the package (superadmin or others)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_packages')
    
    # Optional: Owner to whom it is assigned (agency, franchise, or freelancer)
    assigned_to = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_packages')

    def __str__(self):
        return self.name
