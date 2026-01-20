from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Lead, LeadNote
from .serializers import LeadSerializer, LeadUpdateStatusSerializer

class LeadListCreateView(generics.ListCreateAPIView):
    """
    List all leads for the authenticated user or create a new lead.
    """
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Lead.objects.filter(user=self.request.user)
        lead_status = self.request.query_params.get('status', None)
        if lead_status:
            queryset = queryset.filter(status=lead_status)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class LeadDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a lead.
    Only the owner can access.
    """
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lead.objects.filter(user=self.request.user)

class LeadAddNoteView(generics.UpdateAPIView):
    """
    View specifically to update status and add a history note.
    """
    serializer_class = LeadUpdateStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Lead.objects.filter(user=self.request.user)
