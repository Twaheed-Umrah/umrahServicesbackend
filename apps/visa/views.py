from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from apps.common.permissions import IsFranchiseAdmin, IsSuperAdmin
from .models import VisaApplication, VisaDocument
from .serializers import (
    VisaApplicationListSerializer,
    VisaApplicationDetailSerializer,
    VisaApplicationCreateSerializer,
    VisaApplicationUpdateSerializer,
    VisaApplicationStatusUpdateSerializer,
    VisaApplicationSubmitSerializer,
    VisaDocumentSerializer,
    VisaDocumentUploadSerializer)


def get_accessible_queryset(user, queryset):
    """
    Helper function to filter queryset based on user role.
    - Superadmin: sees everything
    - Franchise Admin / Tenant: sees their own data AND data created by their staff/subordinates
    - Accountant: sees data created by their parent admin AND their own data
    """
    if user.is_superuser or (hasattr(user, 'role') and user.role == 'superadmin'):
        return queryset
    elif hasattr(user, 'role') and user.role in ['franchisesadmin']:
        return queryset.filter(
            Q(applied_by=user) | Q(applied_by__created_by=user)
        )
    elif hasattr(user, 'role') and user.role == 'accountant':
        if user.created_by:
            return queryset.filter(applied_by__in=[user.created_by, user])
        else:
            return queryset.filter(applied_by=user)
    else:
        return queryset.filter(applied_by=user)


def check_access_permission(user, obj):
    """
    Check if user has permission to access an object.
    """
    if user.is_superuser or (hasattr(user, 'role') and user.role == 'superadmin'):
        return True
    elif hasattr(user, 'role') and user.role in ['franchisesadmin']:
        if obj.applied_by == user:
            return True
        return hasattr(obj.applied_by, 'created_by') and obj.applied_by.created_by == user
    elif hasattr(user, 'role') and user.role == 'accountant':
        if user.created_by:
            return obj.applied_by in [user.created_by, user]
        else:
            return obj.applied_by == user
    else:
        return obj.applied_by == user


def can_modify(user):
    """
    Check if user can modify data (accountants CAN modify now)
    """
    # Both accountants and admins can modify
    return hasattr(user, 'role') and user.role in ['accountant', 'franchisesadmin']


class VisaApplicationListView(generics.ListAPIView):
    """List visa applications based on user role"""
    serializer_class = VisaApplicationListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = VisaApplication.objects.all()
        queryset = get_accessible_queryset(user, queryset)
        
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
        queryset = VisaApplication.objects.all()
        return get_accessible_queryset(self.request.user, queryset)


class VisaApplicationCreateView(generics.CreateAPIView):
    """Create new visa application (Agency and Accountants can create)"""
    serializer_class = VisaApplicationCreateSerializer
    permission_classes = [IsFranchiseAdmin]


class VisaApplicationUpdateView(generics.UpdateAPIView):
    """Update visa application (Agency and Accountants can update, draft status only)"""
    serializer_class = VisaApplicationUpdateSerializer
    permission_classes = [IsFranchiseAdmin]
    
    def get_queryset(self):
        user = self.request.user
        queryset = VisaApplication.objects.filter(status='draft')
        return get_accessible_queryset(user, queryset)


class VisaApplicationDeleteView(generics.DestroyAPIView):
    """Delete visa application (Agency and Accountants can delete, draft status only)"""
    permission_classes = [IsFranchiseAdmin]
    
    def get_queryset(self):
        user = self.request.user
        queryset = VisaApplication.objects.filter(status='draft')
        return get_accessible_queryset(user, queryset)


@api_view(['POST'])
@permission_classes([IsFranchiseAdmin])
def submit_visa_application(request, pk):
    """Submit visa application for review (Accountants and Admins can submit)"""
    user = request.user
    queryset = VisaApplication.objects.filter(status='draft')
    queryset = get_accessible_queryset(user, queryset)
    application = get_object_or_404(queryset, pk=pk)
    
    serializer = VisaApplicationSubmitSerializer(data=request.data)
    if serializer.is_valid():
        # Check if all required documents are uploaded
        required_docs = ['passport', 'photo']
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
@permission_classes([IsAuthenticated])
def visa_application_dashboard(request):
    """Dashboard data - accessible by all authenticated users based on their role"""
    user = request.user
    
    # Get accessible queryset based on user role
    queryset = VisaApplication.objects.all()
    queryset = get_accessible_queryset(user, queryset)
    
    total_applications = queryset.count()
    pending_review = queryset.filter(status='submitted').count()
    under_review = queryset.filter(status='under_review').count()
    approved = queryset.filter(status='approved').count()
    rejected = queryset.filter(status='rejected').count()
    issued = queryset.filter(status='issued').count()
    
    # Visa type breakdown
    visa_type_stats = {}
    for choice in VisaApplication.VISA_TYPE_CHOICES:
        visa_type_stats[choice[0]] = queryset.filter(visa_type=choice[0]).count()
    
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
        queryset = VisaApplication.objects.all()
        queryset = get_accessible_queryset(user, queryset)
        application = get_object_or_404(queryset, id=application_id)
        
        return application.documents.all()


class VisaDocumentUploadView(generics.CreateAPIView):
    """Upload document for visa application (Agency and Accountants can upload)"""
    serializer_class = VisaDocumentUploadSerializer
    permission_classes = [IsFranchiseAdmin]
    
    def perform_create(self, serializer):
        application_id = self.kwargs['application_id']
        queryset = VisaApplication.objects.all()
        queryset = get_accessible_queryset(self.request.user, queryset)
        application = get_object_or_404(queryset, id=application_id)
        
        # Only allow document upload for draft and submitted applications
        if application.status not in ['draft', 'submitted']:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Cannot upload documents for this application status")
        
        serializer.save(visa_application=application)


class VisaDocumentDeleteView(generics.DestroyAPIView):
    """Delete document (Agency and Accountants can delete, draft status only)"""
    permission_classes = [IsFranchiseAdmin]
    
    def get_queryset(self):
        application_id = self.kwargs['application_id']
        user = self.request.user
        accessible_apps = get_accessible_queryset(user, VisaApplication.objects.all())
        return VisaDocument.objects.filter(
            visa_application_id=application_id,
            visa_application__in=accessible_apps,
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


# Payment Views with Accountant Access
def get_payment_accessible_queryset(user, queryset):
    """
    Helper function to filter payment queryset based on user role.
    - Superadmin: sees everything
    - Agency/Franchise admin: sees their own payments AND payments made by their accountants
    - Accountant: sees payments made by their parent admin AND their own payments
    """
    if user.is_superuser or (hasattr(user, 'role') and user.role == 'superadmin'):
        return queryset
    elif hasattr(user, 'role') and user.role == 'accountant':
        # Accountant sees payments made by their parent admin AND themselves
        if user.created_by:
            return queryset.filter(paid_by__in=[user.created_by, user])
        else:
            return queryset.filter(paid_by=user)
    else:
        # Agency/Franchise admin sees their own payments AND payments made by their accountants
        return queryset.filter(
            Q(paid_by=user) | Q(paid_by__created_by=user, paid_by__role='accountant')
        )


