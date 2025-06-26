import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from .models import Package
from apps.users.serializers import UserSerializer  # Adjust import path as needed
from django.contrib.auth import get_user_model

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.
    """
    
    def to_internal_value(self, data):
        # Check if this is a base64 string
        if isinstance(data, str) and data.startswith('data:image'):
            # Parse the base64 string
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.{ext}"
            
            # Decode the base64 string
            data = ContentFile(base64.b64decode(imgstr), name=filename)
        
        return super().to_internal_value(data)


class PackageSerializer(serializers.ModelSerializer):
    """Full serializer for detailed package view (GET operations)"""
    # Nested serializers for user relationships (read-only)
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    
    # Display the choice label instead of value
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    
    # Use custom base64 image field
    image = Base64ImageField(required=False, allow_null=True)
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Package
        fields = [
            'id',
            'name',
            'description',
            'package_type',
            'package_type_display',
            'destination',
            'duration_days',
            'price',
            'discount_price',
            'image',
            'is_active',
            'created_by',
            'assigned_to',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class PackageCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating packages - excludes created_by as it's set automatically"""
    # Write-only field for assigned_to
    assigned_to_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    # Display fields for response
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    
    # Use custom base64 image field
    image = Base64ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Package
        fields = [
            'id',
            'name',
            'description',
            'package_type',
            'package_type_display',
            'destination',
            'duration_days',
            'price',
            'discount_price',
            'image',
            'is_active',
            'assigned_to_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_price(self, value):
        """Custom validation for price"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value
    
    def validate_discount_price(self, value):
        """Custom validation for discount_price"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Discount price cannot be negative.")
        return value
    
    def validate_image(self, value):
        """Custom validation for image"""
        if value:
            # Check file size (limit to 5MB)
            if hasattr(value, 'size') and value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image file too large. Maximum size is 5MB.")
            
            # Check file type
            if hasattr(value, 'content_type'):
                allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
                if value.content_type not in allowed_types:
                    raise serializers.ValidationError(
                        f"Unsupported file type. Allowed types: {', '.join(allowed_types)}"
                    )
        
        return value
    
    def validate(self, data):
        """Custom validation for the entire object"""
        # Set discount_price to 0 if not provided
        if 'discount_price' not in data or data['discount_price'] is None:
            data['discount_price'] = 0.00
        
        # Validate discount_price against price
        price = data.get('price')
        discount_price = data.get('discount_price', 0)
        
        if discount_price > price:
            raise serializers.ValidationError({
                'discount_price': 'Discount price cannot be greater than the original price.'
            })
        
        return data
    
    def create(self, validated_data):
        """Create package - assigned_to_id will be handled separately"""
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        
        package = Package.objects.create(
            assigned_to_id=assigned_to_id,
            **validated_data
        )
        return package
    
    def update(self, instance, validated_data):
        """Update package - handle assigned_to_id separately"""
        if 'assigned_to_id' in validated_data:
            instance.assigned_to_id = validated_data.pop('assigned_to_id')
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class PackageListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    # Use custom base64 image field for consistent handling
    image = Base64ImageField(required=False, allow_null=True)
    
    class Meta:
        model = Package
        fields = [
            'id',
            'name',
            'description',
            'package_type',
            'package_type_display',
            'destination',
            'duration_days',
            'price',
            'discount_price',
            'image',
            'is_active',
            'created_by_name',
            'assigned_to_name',
            'created_at',
        ]