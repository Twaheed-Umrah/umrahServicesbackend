from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from apps.common.permissions import IsAgencyAdmin,IsSuperAdmin
from .models import VisaApplication, VisaDocument
from .serializers import (
    VisaApplicationListSerializer,
    VisaApplicationDetailSerializer,
    VisaApplicationCreateSerializer,
    VisaApplicationUpdateSerializer,
    VisaApplicationStatusUpdateSerializer,
    VisaApplicationSubmitSerializer,
    VisaDocumentSerializer,
    VisaDocumentUploadSerializer
)


class VisaApplicationListView(generics.ListAPIView):
    """List visa applications based on user role"""
    serializer_class = VisaApplicationListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # SuperAdmin can see all applications
        if user.is_superuser or (hasattr(user, 'user_type') and user.user_type == 'superadmin'):
            queryset = VisaApplication.objects.all()
        # Agency can only see their own applications
        elif hasattr(user, 'user_type') and user.user_type == 'agency':
            queryset = VisaApplication.objects.filter(applied_by=user)
        else:
            queryset = VisaApplication.objects.none()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by visa type if provided
        visa_type_filter = self.request.query_params.get('visa_type')
        if visa_type_filter:
            queryset = queryset.filter(visa_type=visa_type_filter)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(application_number__icontains=search) |
                Q(applicant_name__icontains=search) |
                Q(passport_number__icontains=search)
            )
        
        return queryset

class VisaApplicationDetailView(generics.RetrieveAPIView):
    """Get detailed visa application"""
    serializer_class = VisaApplicationDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # SuperAdmin can see all applications
        if user.is_superuser or (hasattr(user, 'user_type') and user.user_type == 'superadmin'):
            return VisaApplication.objects.all()
        # Agency can only see their own applications
        elif hasattr(user, 'user_type') and user.user_type == 'agency':
            return VisaApplication.objects.filter(applied_by=user)
        else:
            return VisaApplication.objects.none()

class VisaApplicationCreateView(generics.CreateAPIView):
    """Create new visa application (Agency only)"""
    serializer_class = VisaApplicationCreateSerializer
    permission_classes = [IsAgencyAdmin]

class VisaApplicationUpdateView(generics.UpdateAPIView):
    """Update visa application (Agency only, draft status only)"""
    serializer_class = VisaApplicationUpdateSerializer
    permission_classes = [IsAgencyAdmin]
    
    def get_queryset(self):
        return VisaApplication.objects.filter(applied_by=self.request.user, status='draft')

class VisaApplicationDeleteView(generics.DestroyAPIView):
    """Delete visa application (Agency only, draft status only)"""
    permission_classes = [IsAgencyAdmin]
    
    def get_queryset(self):
        return VisaApplication.objects.filter(applied_by=self.request.user, status='draft')

@api_view(['POST'])
@permission_classes([IsAgencyAdmin])
def submit_visa_application(request, pk):
    """Submit visa application for review"""
    application = get_object_or_404(
        VisaApplication, 
        pk=pk, 
        applied_by=request.user, 
        status='draft'
    )
    
    serializer = VisaApplicationSubmitSerializer(data=request.data)
    if serializer.is_valid():
        # Check if all required documents are uploaded
        required_docs = ['passport', 'photo']  # Add more as needed
        uploaded_docs = application.documents.values_list('document_type', flat=True)
        
        missing_docs = [doc for doc in required_docs if doc not in uploaded_docs]
        if missing_docs:
            return Response({
                'error': f'Missing required documents: {", ".join(missing_docs)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        application.status = 'submitted'
        application.save()
        
        return Response({
            'message': 'Application submitted successfully',
            'application_number': application.application_number
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VisaApplicationStatusUpdateView(generics.UpdateAPIView):
    """Update visa application status (SuperAdmin only)"""
    serializer_class = VisaApplicationStatusUpdateSerializer
    permission_classes = [IsSuperAdmin]
    queryset = VisaApplication.objects.all()

@api_view(['GET'])
@permission_classes([IsSuperAdmin])
def visa_application_dashboard(request):
    """Dashboard data for SuperAdmin"""
    total_applications = VisaApplication.objects.count()
    pending_review = VisaApplication.objects.filter(status='submitted').count()
    under_review = VisaApplication.objects.filter(status='under_review').count()
    approved = VisaApplication.objects.filter(status='approved').count()
    rejected = VisaApplication.objects.filter(status='rejected').count()
    issued = VisaApplication.objects.filter(status='issued').count()
    
    # Visa type breakdown
    visa_type_stats = {}
    for choice in VisaApplication.VISA_TYPE_CHOICES:
        visa_type_stats[choice[0]] = VisaApplication.objects.filter(visa_type=choice[0]).count()
    
    return Response({
        'total_applications': total_applications,
        'status_breakdown': {
            'pending_review': pending_review,
            'under_review': under_review,
            'approved': approved,
            'rejected': rejected,
            'issued': issued,
        },
        'visa_type_breakdown': visa_type_stats,
    })

# Document Views
class VisaDocumentListView(generics.ListAPIView):
    """List documents for a visa application"""
    serializer_class = VisaDocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        application_id = self.kwargs['application_id']
        user = self.request.user
        
        # Check if user has access to this application
        if user.is_superuser or (hasattr(user, 'user_type') and user.user_type == 'superadmin'):
            application = get_object_or_404(VisaApplication, id=application_id)
        elif hasattr(user, 'user_type') and user.user_type == 'agency':
            application = get_object_or_404(VisaApplication, id=application_id, applied_by=user)
        else:
            return VisaDocument.objects.none()
        
        return application.documents.all()

class VisaDocumentUploadView(generics.CreateAPIView):
    """Upload document for visa application (Agency only)"""
    serializer_class = VisaDocumentUploadSerializer
    permission_classes = [IsAgencyAdmin]
    
    def perform_create(self, serializer):
        application_id = self.kwargs['application_id']
        application = get_object_or_404(
            VisaApplication, 
            id=application_id, 
            applied_by=self.request.user
        )
        
        # Only allow document upload for draft and submitted applications
        if application.status not in ['draft', 'submitted']:
            raise serializers.ValidationError("Cannot upload documents for this application status")
        
        serializer.save(visa_application=application)

class VisaDocumentDeleteView(generics.DestroyAPIView):
    """Delete document (Agency only, draft status only)"""
    permission_classes = [IsAgencyAdmin]
    
    def get_queryset(self):
        application_id = self.kwargs['application_id']
        return VisaDocument.objects.filter(
            visa_application_id=application_id,
            visa_application__applied_by=self.request.user,
            visa_application__status='draft'
        )

@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def verify_document(request, document_id):
    """Verify document (SuperAdmin only)"""
    document = get_object_or_404(VisaDocument, id=document_id)
    
    is_verified = request.data.get('is_verified', False)
    document.is_verified = is_verified
    document.verified_by = request.user
    document.verified_at = timezone.now()
    document.save()
    
    return Response({
        'message': f'Document {"verified" if is_verified else "rejected"}',
        'document_id': document.id
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def visa_types_list(request):
    """Get list of available visa types"""
    return Response({
        'visa_types': [{'value': choice[0], 'label': choice[1]} for choice in VisaApplication.VISA_TYPE_CHOICES]
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_status_choices(request):
    """Get list of application status choices"""
    return Response({
        'status_choices': [{'value': choice[0], 'label': choice[1]} for choice in VisaApplication.STATUS_CHOICES]
    })