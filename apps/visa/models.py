from django.db import models 
from apps.common.mixins import TimestampMixin 
 
class VisaApplication(TimestampMixin): 
    STATUS_CHOICES = [ 
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'), 
        ('approved', 'Approved'), 
        ('rejected', 'Rejected'), 
        ('issued', 'Issued'), 
    ] 
 
    VISA_TYPE_CHOICES = [ 
        ('hajj', 'Hajj'),
        ('umrah', 'Umrah'), 
        ('ramadan', 'Ramadan'),
        ('tourist', 'Tourist'), 
    ] 
 
    application_number = models.CharField(max_length=20, unique=True) 
    applicant_name = models.CharField(max_length=255) 
    passport_number = models.CharField(max_length=20) 
    nationality = models.CharField(max_length=100) 
    destination_country = models.CharField(max_length=100) 
    visa_type = models.CharField(max_length=20, choices=VISA_TYPE_CHOICES) 
    travel_date = models.DateField() 
    return_date = models.DateField() 
    purpose_of_visit = models.TextField() 
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft') 
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2) 
    embassy_fee = models.DecimalField(max_digits=10, decimal_places=2) 
    service_fee = models.DecimalField(max_digits=10, decimal_places=2) 
    total_fee = models.DecimalField(max_digits=10, decimal_places=2) 
    applied_by = models.ForeignKey('users.User', on_delete=models.CASCADE)  # Agency user
    remarks = models.TextField(blank=True, null=True) 
    processed_by = models.ForeignKey('users.User', related_name='processed_applications', on_delete=models.SET_NULL, null=True, blank=True)  # SuperAdmin
    processed_at = models.DateTimeField(null=True, blank=True)
 
    def __str__(self): 
        return f"Visa Application {self.application_number} - {self.applicant_name}" 
 
    def save(self, *args, **kwargs): 
        if not self.application_number: 
            import uuid 
            self.application_number = f"VA{str(uuid.uuid4())[:8].upper()}" 
         
        self.total_fee = self.processing_fee + self.embassy_fee + self.service_fee 
        super().save(*args, **kwargs) 
 
    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('can_process_application', 'Can process visa applications'),
            ('can_view_all_applications', 'Can view all visa applications'),
        ]
 
class VisaDocument(TimestampMixin): 
    DOCUMENT_TYPE_CHOICES = [ 
        ('passport', 'Passport'), 
        ('photo', 'Passport Photo'), 
        ('invitation', 'Invitation Letter'), 
        ('bank_statement', 'Bank Statement'), 
        ('employment_letter', 'Employment Letter'), 
        ('hotel_booking', 'Hotel Booking'), 
        ('flight_booking', 'Flight Booking'), 
        ('other', 'Other'), 
    ] 
 
    visa_application = models.ForeignKey(VisaApplication, related_name='documents', on_delete=models.CASCADE) 
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE_CHOICES) 
    document_file = models.FileField(upload_to='visa_documents/') 
    description = models.CharField(max_length=255, blank=True, null=True) 
    is_verified = models.BooleanField(default=False) 
    verified_by = models.ForeignKey('users.User', related_name='verified_documents', on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
 
    def __str__(self): 
        return f"{self.get_document_type_display()} - {self.visa_application.application_number}"
    
    class Meta:
        ordering = ['-created_at']