from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Enquiry
from .serializers import EnquirySerializer

class EnquiryCreateView(generics.CreateAPIView):
    serializer_class = EnquirySerializer
    permission_classes = [permissions.AllowAny]  # Public access

    def perform_create(self, serializer):
        agency_id = self.request.data.get('agency')
        franchise_id = self.request.data.get('franchise')

        serializer.save(
            agency_id=agency_id if agency_id else None,
            franchise_id=franchise_id if franchise_id else None
        )


class EnquiryListView(generics.ListAPIView):
    serializer_class = EnquirySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'superadmin':
            return Enquiry.objects.all()
        elif user.role == 'agencyAdmin':
            return Enquiry.objects.filter(agency=user)
        elif user.role == 'franchiseAdmin':
            return Enquiry.objects.filter(franchise=user)
        else:
            return Enquiry.objects.none()
