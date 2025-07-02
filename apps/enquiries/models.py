from django.db import models
from apps.common.mixins import TimestampMixin
import uuid
from django.conf import settings
from django.utils import timezone

class APIKey(models.Model):
    """Model to store API keys for external website integration"""
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='api_keys')
    key = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    name = models.CharField(max_length=100, help_text="Name/description for this API key")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    website_url = models.URLField(blank=True, null=True, help_text="Website URL where this key is used")
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.key:
            self.key = str(uuid.uuid4()).replace('-', '')
        super().save(*args, **kwargs)

class Package(models.Model):
    PACKAGE_TYPES = [
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
    
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPES, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR', blank=True, null=True)
    image = models.ImageField(upload_to='package_images/', blank=True, null=True)
    features = models.TextField(help_text="Enter features separated by new lines", blank=True)
    duration_days = models.IntegerField(default=7)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['package_type']

    def __str__(self):
        return self.title

    def get_features_list(self):
        """Return features as a list"""
        return [feature.strip() for feature in self.features.split('\n') if feature.strip()]

class HomePage(models.Model):
    content = models.TextField(help_text="Main content for the homepage")
    background_video = models.FileField(upload_to='homepage_videos/', blank=True, null=True)
    background_image = models.ImageField(upload_to='homepage_images/', blank=True, null=True)
    welcome_title = models.CharField(max_length=200, default="Welcome")
    welcome_subtitle = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Homepage Content - {self.welcome_title}"
    

# Add this to your existing models.py file

class ContactUs(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    package_type = models.CharField(max_length=50, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    api_key = models.ForeignKey(
        'APIKey', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='contact_submissions',
        help_text="API key used to submit this contact form"
    )
    submitted_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_submissions',
        help_text="User who owns the API key used for submission"
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Us"
        verbose_name_plural = "Contact Us"

    def __str__(self):
        api_info = f" (via {self.api_key.name})" if self.api_key else ""
        return f"{self.name} - {self.email}{api_info}"
