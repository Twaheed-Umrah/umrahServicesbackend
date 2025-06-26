from django.db import models
from apps.common.mixins import TimestampMixin

class Enquiry(TimestampMixin):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    message = models.TextField()
    place = models.CharField(max_length=255, blank=True, null=True)

    # Foreign keys for agency and franchise
    agency = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='agency_enquiries')
    franchise = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='franchise_enquiries')

    def __str__(self):
        return f"Enquiry from {self.name} ({self.phone})"
