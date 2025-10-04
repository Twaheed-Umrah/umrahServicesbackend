from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import Payment
from apps.common.permissions import IsAgencyAdmin, IsSuperAdmin
from .models import VisaApplication, VisaDocument
from .serializers import (
    VisaApplicationListSerializer,
    VisaApplicationDetailSerializer,
    VisaApplicationCreateSerializer,
    VisaApplicationUpdateSerializer,
    VisaApplicationStatusUpdateSerializer,
    VisaApplicationSubmitSerializer,
    VisaDocumentSerializer,
    VisaDocumentUploadSerializer,
    PaymentCreateSerializer,
    PaymentListSerializer,
    PaymentDetailSerializer,
    PaymentStatusUpdateSerializer,
    UserPaymentHistorySerializer
)


def get_accessible_queryset(user, queryset):
    """
    Helper function to filter queryset based on user role.
    - Superadmin: sees everything
    - AgencyAdmin/FranchisesAdmin: sees their own data AND data created by their accountants
    - Accountant: sees data created by their parent admin AND their own data
    """
    if user.is_superuser or (hasattr(user, 'role') and user.role == 'superadmin'):
        return queryset
    elif hasattr(user, 'role') and user.role == 'accountant':
        # Accountant sees data created by their parent admin AND themselves
        if user.created_by:
            return queryset.filter(applied_by__in=[user.created_by, user])
        else:
            return queryset.filter(applied_by=user)
    else:
        # Agency/Franchise admin sees their own data AND data created by their accountants
        return queryset.filter(
            Q(applied_by=user) | Q(applied_by__created_by=user, applied_by__role='accountant')
        )


def check_access_permission(user, obj):
    """
    Check if user has permission to access an object.
    - Superadmin: can access all
    - Creator: can access their own
    - Accountant: can access if created by their parent admin OR themselves
    - Parent admin: can access their own OR if created by their accountants
    """
    if user.is_superuser or (hasattr(user, 'role') and user.role == 'superadmin'):
        return True
    elif hasattr(user, 'role') and user.role == 'accountant':
        # Accountant can access their parent admin's data AND their own
        if user.created_by:
            return obj.applied_by in [user.created_by, user]
        else:
            return obj.applied_by == user
    else:
        # Agency/Franchise admin can access their own AND their accountants' data
        if obj.applied_by == user:
            return True
        # Check if created by one of their accountants
        return (hasattr(obj.applied_by, 'created_by') and 
                obj.applied_by.created_by == user and 
                obj.applied_by.role == 'accountant')


def can_modify(user):
    """
    Check if user can modify data (accountants CAN modify now)
    """
    # Both accountants and admins can modify
    return hasattr(user, 'role') and user.role in ['accountant', 'agencyadmin', 'franchiseadmin']


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
    permission_classes = [IsAgencyAdmin]


class VisaApplicationUpdateView(generics.UpdateAPIView):
    """Update visa application (Agency and Accountants can update, draft status only)"""
    serializer_class = VisaApplicationUpdateSerializer
    permission_classes = [IsAgencyAdmin]
    
    def get_queryset(self):
        user = self.request.user
        queryset = VisaApplication.objects.filter(status='draft')
        return get_accessible_queryset(user, queryset)


class VisaApplicationDeleteView(generics.DestroyAPIView):
    """Delete visa application (Agency and Accountants can delete, draft status only)"""
    permission_classes = [IsAgencyAdmin]
    
    def get_queryset(self):
        user = self.request.user
        queryset = VisaApplication.objects.filter(status='draft')
        return get_accessible_queryset(user, queryset)


@api_view(['POST'])
@permission_classes([IsAgencyAdmin])
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
    permission_classes = [IsAgencyAdmin]
    
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
    permission_classes = [IsAgencyAdmin]
    
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


class PaymentCreateView(generics.CreateAPIView):
    """Create new payment (authenticated users including accountants can create)"""
    serializer_class = PaymentCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()
        
        return Response({
            'message': 'Payment submitted successfully',
            'payment_id': payment.id,
            'status': 'inprocess'
        }, status=status.HTTP_201_CREATED)


class PaymentListView(generics.ListAPIView):
    """List all payments (All authenticated users can view based on their role)"""
    serializer_class = PaymentListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.all()
        queryset = get_payment_accessible_queryset(user, queryset)
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by payment mode if provided
        payment_mode_filter = self.request.query_params.get('payment_mode')
        if payment_mode_filter:
            queryset = queryset.filter(payment_mode=payment_mode_filter)
        
        # Date range filter
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Search functionality
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(paid_by__first_name__icontains=search) |
                Q(paid_by__last_name__icontains=search) |
                Q(paid_by__email__icontains=search) |
                Q(reference_number__icontains=search)
            )
        
        return queryset


class PaymentDetailView(generics.RetrieveAPIView):
    """Get detailed payment information (All authenticated users can view based on their role)"""
    serializer_class = PaymentDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.all()
        return get_payment_accessible_queryset(user, queryset)


class PaymentStatusUpdateView(generics.UpdateAPIView):
    """Update payment status (SuperAdmin only)"""
    serializer_class = PaymentStatusUpdateSerializer
    permission_classes = [IsSuperAdmin]
    queryset = Payment.objects.all()
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': f'Payment status updated to {instance.status}',
            'payment_id': instance.id,
            'status': instance.status
        })


class UserPaymentHistoryView(generics.ListAPIView):
    """Get user's own payment history or parent admin's for accountants"""
    serializer_class = UserPaymentHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Payment.objects.all()
        return get_payment_accessible_queryset(user, queryset)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_dashboard(request):
    """Payment dashboard data (All authenticated users can access based on their role)"""
    user = request.user
    
    queryset = Payment.objects.all()
    queryset = get_payment_accessible_queryset(user, queryset)
    
    total_payments = queryset.count()
    inprocess_payments = queryset.filter(status='inprocess').count()
    completed_payments = queryset.filter(status='completed').count()
    rejected_payments = queryset.filter(status='rejected').count()
    
    # Total amounts
    total_amount = queryset.aggregate(total=Sum('payment_amount'))['total'] or 0
    completed_amount = queryset.filter(status='completed').aggregate(
        total=Sum('payment_amount')
    )['total'] or 0
    inprocess_amount = queryset.filter(status='inprocess').aggregate(
        total=Sum('payment_amount')
    )['total'] or 0
    
    # Payment mode breakdown
    payment_mode_stats = {}
    for choice in Payment.PAYMENT_MODE_CHOICES:
        mode_count = queryset.filter(payment_mode=choice[0]).count()
        mode_amount = queryset.filter(payment_mode=choice[0]).aggregate(
            total=Sum('payment_amount')
        )['total'] or 0
        payment_mode_stats[choice[0]] = {
            'label': choice[1],
            'count': mode_count,
            'amount': mode_amount
        }
    
    # Recent payments (last 10)
    recent_payments = queryset.select_related('paid_by', 'processed_by')[:10]
    recent_payments_data = PaymentListSerializer(recent_payments, many=True).data
    
    # Monthly stats (current month)
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_stats = queryset.filter(created_at__gte=current_month).aggregate(
        count=Count('id'),
        amount=Sum('payment_amount')
    )
    
    return Response({
        'total_payments': total_payments,
        'status_breakdown': {
            'inprocess': inprocess_payments,
            'completed': completed_payments,
            'rejected': rejected_payments,
        },
        'amount_breakdown': {
            'total_amount': total_amount,
            'completed_amount': completed_amount,
            'inprocess_amount': inprocess_amount,
        },
        'payment_mode_breakdown': payment_mode_stats,
        'monthly_stats': {
            'count': monthly_stats['count'] or 0,
            'amount': monthly_stats['amount'] or 0,
        },
        'recent_payments': recent_payments_data,
    })


@api_view(['POST'])
@permission_classes([IsSuperAdmin])
def bulk_update_payments(request):
    """Bulk update payment status (SuperAdmin only)"""
    payment_ids = request.data.get('payment_ids', [])
    new_status = request.data.get('status')
    notes = request.data.get('notes', '')
    
    if not payment_ids:
        return Response({
            'error': 'Payment IDs are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if new_status not in ['completed', 'rejected']:
        return Response({
            'error': 'Invalid status. Only "completed" or "rejected" allowed for bulk update'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Update payments that are currently in process
    updated_count = Payment.objects.filter(
        id__in=payment_ids,
        status='inprocess'
    ).update(
        status=new_status,
        processed_by=request.user,
        processed_at=timezone.now(),
        notes=notes
    )
    
    return Response({
        'message': f'{updated_count} payments updated successfully',
        'updated_count': updated_count,
        'status': new_status
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_modes_list(request):
    """Get list of available payment modes"""
    return Response({
        'payment_modes': [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Payment.PAYMENT_MODE_CHOICES
        ]
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status_choices(request):
    """Get list of payment status choices"""
    return Response({
        'status_choices': [
            {'value': choice[0], 'label': choice[1]} 
            for choice in Payment.STATUS_CHOICES
        ]
    })