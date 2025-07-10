# models.py
from django.db import models
from django.utils import timezone
from apps.users.models import User  # Assuming your User model is in users app

class HajjUmrahBookingDemo(models.Model):
    BUSINESS_PLAN_CHOICES = [
        ('agency', 'Agency ID'),
        ('franchise', 'Franchises ID'),
        ('freelancer', 'Freelancer ID'),
    ]
    
    selected_date = models.DateField()
    selected_time = models.TimeField()
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=20)
    business_plan = models.CharField(max_length=20, choices=BUSINESS_PLAN_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hajj_umrah_booking_demo'
        verbose_name = 'Hajj Umrah Booking Demo'
        verbose_name_plural = 'Hajj Umrah Booking Demos'
    
    def __str__(self):
        return f"{self.name} - {self.business_plan}"


class HajjUmrahBookingService(models.Model):
    BUSINESS_PLAN_CHOICES = [
        ('agency', 'Agency ID'),
        ('franchise', 'Franchises ID'),
        ('freelancer', 'Freelancer ID'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=20)
    business_plan = models.CharField(max_length=20, choices=BUSINESS_PLAN_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hajj_umrah_booking_service'
        verbose_name = 'Hajj Umrah Booking Service'
        verbose_name_plural = 'Hajj Umrah Booking Services'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.business_plan}"
