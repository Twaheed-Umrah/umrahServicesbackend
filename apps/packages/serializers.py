import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from .models import Package, PackageDeparture, Supplier
from apps.users.serializers import UserSerializer
from django.contrib.auth import get_user_model

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.
    """
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            filename = f"{uuid.uuid4()}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=filename)
        return super().to_internal_value(data)


class PackageDepartureSerializer(serializers.ModelSerializer):
    seats_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = PackageDeparture
        fields = [
            'id', 'package', 'departure_date', 'return_date',
            'departure_city', 'capacity', 'booked_count',
            'seats_available', 'cutoff_date', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'seats_available', 'created_at']


class PackageSerializer(serializers.ModelSerializer):
    """Full serializer for detailed package view (GET operations)"""
    created_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    features_list = serializers.ListField(source='get_features_list', read_only=True)
    departures = PackageDepartureSerializer(many=True, read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    title = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = Package
        fields = [
            'id',
            'name',
            'title',
            'description',
            'package_type',
            'package_type_display',
            'destination',
            'duration_days',
            'currency',
            'price',
            'discount_price',
            'single_price',
            'double_price',
            'triple_price',
            'quad_price',
            'child_price',
            'infant_price',
            'features',
            'features_list',
            'inclusions',
            'exclusions',
            'cancellation_policy',
            'image',
            'is_active',
            'is_featured',
            'show_on_agency_website',
            'created_by',
            'assigned_to',
            'departures',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class PackageCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating packages"""
    assigned_to_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
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
            'currency',
            'price',
            'discount_price',
            'single_price',
            'double_price',
            'triple_price',
            'quad_price',
            'child_price',
            'infant_price',
            'features',
            'inclusions',
            'exclusions',
            'cancellation_policy',
            'image',
            'is_active',
            'is_featured',
            'show_on_agency_website',
            'assigned_to_id',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0.")
        return value

    def validate_discount_price(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Discount price cannot be negative.")
        return value

    def validate_image(self, value):
        if value:
            if hasattr(value, 'size') and value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image file too large. Maximum size is 5MB.")
            if hasattr(value, 'content_type'):
                allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
                if value.content_type not in allowed_types:
                    raise serializers.ValidationError("Unsupported image format. Allowed: JPEG, PNG, GIF, WebP.")
        return value

    def create(self, validated_data):
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        request = self.context.get('request')
        
        if assigned_to_id:
            try:
                assigned_to = User.objects.get(id=assigned_to_id)
                validated_data['assigned_to'] = assigned_to
            except User.DoesNotExist:
                raise serializers.ValidationError({"assigned_to_id": "User does not exist."})
        
        validated_data['created_by'] = request.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        assigned_to_id = validated_data.pop('assigned_to_id', None)
        if assigned_to_id is not None:
            if assigned_to_id:
                try:
                    assigned_to = User.objects.get(id=assigned_to_id)
                    instance.assigned_to = assigned_to
                except User.DoesNotExist:
                    raise serializers.ValidationError({"assigned_to_id": "User does not exist."})
            else:
                instance.assigned_to = None
        
        return super().update(instance, validated_data)


class PackageListSerializer(serializers.ModelSerializer):
    package_type_display = serializers.CharField(source='get_package_type_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    image = Base64ImageField(required=False, allow_null=True)
    title = serializers.CharField(source='name', read_only=True)

    class Meta:
        model = Package
        fields = [
            'id',
            'name',
            'title',
            'description',
            'package_type',
            'package_type_display',
            'destination',
            'duration_days',
            'currency',
            'price',
            'discount_price',
            'single_price',
            'double_price',
            'triple_price',
            'quad_price',
            'image',
            'is_active',
            'is_featured',
            'show_on_agency_website',
            'created_by_name',
            'assigned_to_name',
            'created_at',
        ]


class SupplierSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    supplier_type_display = serializers.CharField(source='get_supplier_type_display', read_only=True)

    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'supplier_type', 'supplier_type_display',
            'country', 'city', 'contact_person', 'email', 'phone',
            'license_reference', 'verification_status', 'payment_terms',
            'created_by', 'created_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
