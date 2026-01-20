from django.db import models
from django.conf import settings

class Lead(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('CONTACTED', 'Contacted'),
        ('INTERESTED', 'Interested'),
        ('FOLLOW_UP', 'Follow Up'),
        ('BUSY', 'Busy'),
        ('RNR', 'RNR'),
        ('CALLBACK', 'Callback'),
        ('CLOSED', 'Closed'),
        ('NOT_INTERESTED', 'Not Interested'),
        ('LOST', 'Lost'),
        ('CONVERTED', 'Converted'),
        ('SWITCH_OFF', 'Switch Off'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='crm_leads')
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=20)
    email = models.EmailField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.status}"

class LeadNote(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='history_notes')
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for {self.lead.name} at {self.created_at}"
