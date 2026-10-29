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

    SOURCE_CHOICES = [
        ('Meta Ads', 'Meta / Facebook Ads'),
        ('Google Ads', 'Google Ads'),
        ('Website', 'Website Form'),
        ('Excel Upload', 'Excel / Bulk Upload'),
        ('Walk-in', 'Walk In'),
        ('Referral', 'Referral'),
        ('Other', 'Other'),
    ]

    # Owner / Agency Head
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='crm_leads')
    
    # Assigned Telecaller / Sales Agent
    assigned_caller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_caller_leads',
        help_text="The caller currently assigned to work this lead"
    )
    is_in_agency_pool = models.BooleanField(
        default=False,
        help_text="True if lead is in the Agency Head unassigned master pool"
    )

    # Pilgrim Information
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=25)
    email = models.EmailField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    # Campaign & Source
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='Meta Ads')
    campaign_name = models.CharField(max_length=255, blank=True, null=True)
    journey_type = models.CharField(max_length=50, default='Umrah')
    pax_count = models.PositiveIntegerField(default=1)
    budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Pipeline status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    notes = models.TextField(blank=True, null=True)
    next_followup_at = models.DateTimeField(null=True, blank=True)
    lost_reason = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        caller = self.assigned_caller.username if self.assigned_caller else "UNASSIGNED POOL"
        return f"{self.name} ({self.mobile_number}) -> {caller} [{self.status}]"


class LeadNote(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='history_notes')
    note = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.lead.name} at {self.created_at}"


class Task(models.Model):
    """Module 18: Tasks & Team Management"""
    TASK_TYPE_CHOICES = [
        ('call', 'Phone Call / Follow-up'),
        ('quote', 'Send Package Quotation'),
        ('document', 'Collect Passport / Visa Documents'),
        ('payment', 'Collect Balance Payment'),
        ('supplier', 'Confirm Supplier Booking'),
        ('other', 'General Task'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    title = models.CharField(max_length=255)
    task_type = models.CharField(max_length=50, choices=TASK_TYPE_CHOICES, default='call')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    due_date = models.DateTimeField()
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assigned_tasks')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    related_lead = models.ForeignKey(Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    description = models.TextField(blank=True, null=True)
    resolution_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"{self.title} - {self.assigned_to.username} ({self.status})"
