# models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from apps.common.mixins import TimestampMixin

class User(AbstractUser, TimestampMixin):
    ROLE_CHOICES = [
        ('superadmin', 'SuperAdmin'),
        ('agencyadmin', 'AgencyAdmin'),
        ('franchisesadmin', 'FranchisesAdmin'),
        ('operations', 'Operations Coordinator'),
        ('accountant', 'Accountant'),
        ('caller', 'Telecaller'),
        ('sales_agent', 'Sales Agent'),
    ]
    
    # Basic user fields
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True, unique=True)
    email = models.EmailField(unique=True, blank=False, null=False)  
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Telecaller & Attendance fields
    is_present = models.BooleanField(
        default=True, 
        help_text="Attendance status: If False, Round-Robin lead assignment strictly skips this caller."
    )
    caller_status = models.CharField(
        max_length=20,
        choices=[
            ('available', 'Available'),
            ('on_call', 'On Call'),
            ('break', 'On Break'),
            ('absent', 'Absent / Off Duty'),
        ],
        default='available'
    )
    daily_lead_quota = models.PositiveIntegerField(
        default=50, 
        help_text="Maximum leads that can be assigned per day"
    )
    
    # Profile fields (merged from UserProfile)
    bio = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    agreement_letter = models.FileField(upload_to='agreement_letters/', blank=True, null=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)

    # Override the USERNAME_FIELD to use email for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Fields required when creating superuser

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class OTPVerification(TimestampMixin):
    VERIFICATION_TYPE_CHOICES = [
        ('email', 'Email Verification'),
        ('phone', 'Phone Verification'),
        ('password_reset', 'Password Reset'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_verifications')
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPE_CHOICES)
    otp = models.CharField(max_length=6)
    new_value = models.CharField(max_length=255, help_text="New email or phone number to be verified")
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.user.username} - {self.get_verification_type_display()}"
    
    def is_expired(self):
        """Check if the OTP has expired"""
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if the OTP is valid (not expired and not verified)"""
        return not self.is_expired() and not self.is_verified
