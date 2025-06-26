from rest_framework import serializers
from .models import Enquiry
from apps.users.models import User
  # adjust if your user model path is different

class EnquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enquiry
        fields = ['id', 'name', 'email', 'phone', 'message', 'place', 'agency', 'franchise']
        read_only_fields = ['agency', 'franchise']  # Assigned from view
