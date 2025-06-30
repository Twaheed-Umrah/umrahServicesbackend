from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import VisaApplication, VisaDocument,Payment

User = get_user_model()

class VisaDocumentSerializer(serializers.ModelSerializer):
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    
    class Meta:
        model = VisaDocument
        fields = [
            'id', 'document_type', 'document_file', 'description', 
            'is_verified', 'verified_by', 'verified_by_name', 'verified_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['is_verified', 'verified_by', 'verified_at']

class VisaApplicationListSerializer(serializers.ModelSerializer):
    """Serializer for listing visa applications"""
    applied_by_name = serializers.CharField(source='applied_by.get_full_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    visa_type_display = serializers.CharField(source='get_visa_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    documents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = VisaApplication
        fields = [
            'id', 'application_number', 'applicant_name', 'nationality',
            'destination_country', 'visa_type', 'visa_type_display',
            'status', 'status_display', 'travel_date', 'return_date',
            'total_fee', 'applied_by_name', 'processed_by_name',
            'documents_count', 'created_at', 'updated_at'
        ]
    
    def get_documents_count(self, obj):
        return obj.documents.count()

class VisaApplicationDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed visa application view"""
    applied_by_name = serializers.CharField(source='applied_by.get_full_name', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    visa_type_display = serializers.CharField(source='get_visa_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    documents = VisaDocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = VisaApplication
        fields = [
            'id', 'application_number', 'applicant_name', 'passport_number',
            'nationality', 'destination_country', 'visa_type', 'visa_type_display',
            'travel_date', 'return_date', 'purpose_of_visit', 'status', 'status_display',
            'processing_fee', 'embassy_fee', 'service_fee', 'total_fee',
            'applied_by', 'applied_by_name', 'processed_by', 'processed_by_name',
            'processed_at', 'remarks', 'documents', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'application_number', 'total_fee', 'applied_by', 'processed_by', 'processed_at'
        ]

class VisaApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating visa applications (Agency use)"""
    
    class Meta:
        model = VisaApplication
        fields = [
            'applicant_name', 'passport_number', 'nationality', 
            'destination_country', 'visa_type', 'travel_date', 'return_date',
            'purpose_of_visit', 'processing_fee', 'embassy_fee', 'service_fee'
        ]
    
    def validate(self, data):
        """Custom validation"""
        if data['travel_date'] >= data['return_date']:
            raise serializers.ValidationError("Return date must be after travel date")
        
        if data['processing_fee'] < 0 or data['embassy_fee'] < 0 or data['service_fee'] < 0:
            raise serializers.ValidationError("Fees cannot be negative")
        
        return data
    
    def create(self, validated_data):
        # Set the applied_by to current user (agency)
        validated_data['applied_by'] = self.context['request'].user
        return super().create(validated_data)

class VisaApplicationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating visa applications (Agency use - only draft status)"""
    
    class Meta:
        model = VisaApplication
        fields = [
            'applicant_name', 'passport_number', 'nationality', 
            'destination_country', 'visa_type', 'travel_date', 'return_date',
            'purpose_of_visit', 'processing_fee', 'embassy_fee', 'service_fee'
        ]
    
    def validate(self, data):
        """Only allow updates if status is draft"""
        if self.instance.status != 'draft':
            raise serializers.ValidationError("Cannot update submitted applications")
        return data

class VisaApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for status updates (SuperAdmin only)"""
    
    class Meta:
        model = VisaApplication
        fields = ['status', 'remarks']
    
    def validate_status(self, value):
        """Validate status transitions"""
        current_status = self.instance.status
        valid_transitions = {
            'submitted': ['under_review', 'rejected'],
            'under_review': ['approved', 'rejected'],
            'approved': ['issued', 'rejected'],
        }
        
        if current_status in valid_transitions:
            if value not in valid_transitions[current_status]:
                raise serializers.ValidationError(
                    f"Cannot change status from {current_status} to {value}"
                )
        
        return value
    
    def update(self, instance, validated_data):
        # Set processed_by and processed_at when status is updated
        if 'status' in validated_data:
            from django.utils import timezone
            instance.processed_by = self.context['request'].user
            instance.processed_at = timezone.now()
        
        return super().update(instance, validated_data)

class VisaApplicationSubmitSerializer(serializers.Serializer):
    """Serializer for submitting applications"""
    confirm = serializers.BooleanField(required=True)
    
    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError("Please confirm submission")
        return value

class VisaDocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer for uploading documents"""
    
    class Meta:
        model = VisaDocument
        fields = ['document_type', 'document_file', 'description']
    
    def validate(self, data):
        """Validate file upload"""
        if not data.get('document_file'):
            raise serializers.ValidationError("Document file is required")
        
        # Check file size (10MB limit)
        if data['document_file'].size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        return data
    
class PaymentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payments (Other users)"""
    
    class Meta:
        model = Payment
        fields = [
            'payment_amount', 
            'payment_mode', 
            'no_of_travelers',
            'reference_number',
            'notes'
        ]
    
    def validate_payment_amount(self, value):
        """Validate payment amount"""
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than 0")
        return value
    
    def validate_no_of_travelers(self, value):
        """Validate number of travelers"""
        if value <= 0:
            raise serializers.ValidationError("Number of travelers must be greater than 0")
        return value
    
    def create(self, validated_data):
        # Set the paid_by to current user
        validated_data['paid_by'] = self.context['request'].user
        return super().create(validated_data)

class PaymentListSerializer(serializers.ModelSerializer):
    """Serializer for listing payments (SuperAdmin view)"""
    paid_by_name = serializers.CharField(source='paid_by.get_full_name', read_only=True)
    paid_by_email = serializers.CharField(source='paid_by.email', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_mode_display = serializers.CharField(source='get_payment_mode_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 
            'payment_amount', 
            'payment_mode', 
            'payment_mode_display',
            'no_of_travelers',
            'status',
            'status_display',
            'paid_by_name',
            'paid_by_email',
            'processed_by_name',
            'processed_at',
            'reference_number',
            'notes',
            'created_at',
            'updated_at'
        ]

class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed payment view (SuperAdmin)"""
    paid_by_name = serializers.CharField(source='paid_by.get_full_name', read_only=True)
    paid_by_email = serializers.CharField(source='paid_by.email', read_only=True)
    paid_by_phone = serializers.CharField(source='paid_by.phone_number', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_mode_display = serializers.CharField(source='get_payment_mode_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 
            'payment_amount', 
            'payment_mode', 
            'payment_mode_display',
            'no_of_travelers',
            'status',
            'status_display',
            'paid_by',
            'paid_by_name',
            'paid_by_email',
            'paid_by_phone',
            'processed_by',
            'processed_by_name',
            'processed_at',
            'reference_number',
            'notes',
            'created_at',
            'updated_at'
        ]

class PaymentStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating payment status (SuperAdmin only)"""
    
    class Meta:
        model = Payment
        fields = ['status', 'notes']
    
    def validate_status(self, value):
        """Validate status transitions"""
        current_status = self.instance.status
        
        # Define valid status transitions
        valid_transitions = {
            'inprocess': ['completed', 'rejected'],
            'completed': [],  # Cannot change from completed
            'rejected': ['inprocess'],  # Can reprocess rejected payments
        }
        
        if current_status in valid_transitions:
            if value not in valid_transitions[current_status] and value != current_status:
                raise serializers.ValidationError(
                    f"Cannot change status from {current_status} to {value}"
                )
        
        return value
    
    def update(self, instance, validated_data):
        # Set processed_by and processed_at when status is updated
        if 'status' in validated_data and validated_data['status'] != instance.status:
            from django.utils import timezone
            instance.processed_by = self.context['request'].user
            instance.processed_at = timezone.now()
        
        return super().update(instance, validated_data)

class UserPaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for user's own payment history"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_mode_display = serializers.CharField(source='get_payment_mode_display', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 
            'payment_amount', 
            'payment_mode',
            'payment_mode_display',
            'no_of_travelers',
            'status',
            'status_display',
            'processed_by_name',
            'processed_at',
            'reference_number',
            'notes',
            'created_at'
        ]