from django.db import models
from django.contrib.auth import get_user_model
from apps.common.mixins import TimestampMixin

User = get_user_model()

class PosterTemplate(TimestampMixin):
    TEMPLATE_CHOICES = [
        ('Umrah', 'Umrah Template'),
        ('Hajj', 'Hajj Template'),
        ('Ramadan', 'Ramadan Template'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_CHOICES, default='classic')
    background_image = models.ImageField(upload_to='poster_templates/')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_template_type_display()}"

class PackagePoster(TimestampMixin):
    PACKAGE_TYPE_CHOICES = [
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
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='package_posters')
    package_name = models.CharField(max_length=200)
    package_type = models.CharField(max_length=20, choices=PACKAGE_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    template = models.ForeignKey(PosterTemplate, on_delete=models.CASCADE)
    
    # Generated poster files
    poster_jpg = models.ImageField(upload_to='generated_posters/jpg/', blank=True, null=True)
    poster_png = models.ImageField(upload_to='generated_posters/png/', blank=True, null=True)
    poster_pdf = models.FileField(upload_to='generated_posters/pdf/', blank=True, null=True)
    
    class Meta:
        permissions = [
            ("can_create_poster", "Can create poster"),
        ]
    
    def __str__(self):
        return f"{self.package_name} - {self.user.company_name}"