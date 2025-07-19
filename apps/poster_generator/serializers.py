from rest_framework import serializers
from .models import PackagePoster, PosterTemplate
from django.contrib.auth import get_user_model
import base64
import uuid
from django.core.files.base import ContentFile

User = get_user_model()

class Base64ImageField(serializers.ImageField):
    """
    A Django REST framework field for handling image-uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.
    """
    
    def to_internal_value(self, data):
        # Check if this is a base64 string
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                # Parse the base64 string
                header, imgstr = data.split(';base64,')
                ext = header.split('/')[1]  # Get extension from data:image/jpeg
                
                # Handle different image formats
                if ext == 'jpeg':
                    ext = 'jpg'
                
                # Generate a unique filename
                filename = f"{uuid.uuid4()}.{ext}"
                
                # Decode the base64 string
                decoded_data = base64.b64decode(imgstr)
                data = ContentFile(decoded_data, name=filename)
                
            except (ValueError, IndexError) as e:
                raise serializers.ValidationError(f"Invalid base64 image data: {str(e)}")
        
        return super().to_internal_value(data)
    
    def to_representation(self, value):
        """Return full URL for the image"""
        if not value:
            return None
        
        # Check if the file actually exists
        try:
            if not value.storage.exists(value.name):
                return None
        except Exception:
            return None
        
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(value.url)
        return value.url

class PosterTemplateSerializer(serializers.ModelSerializer):
    # Handle both base64 input and URL output for the same field
    background_image = Base64ImageField(required=False)
    
    class Meta:
        model = PosterTemplate
        fields = ['id', 'name', 'template_type', 'background_image', 'is_active', 'created_at', 'updated_at']
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True},
        }
    
    def create(self, validated_data):
        """Override create to ensure proper file handling"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Creating PosterTemplate with validated_data: {validated_data}")
        
        instance = super().create(validated_data)
        
        # Log the created instance details
        logger.info(f"Created instance ID: {instance.id}")
        logger.info(f"Background image field: {instance.background_image}")
        
        if instance.background_image:
            logger.info(f"Image name: {instance.background_image.name}")
            logger.info(f"Image path: {instance.background_image.path}")
            logger.info(f"Image URL: {instance.background_image.url}")
            
            # Check if file actually exists
            import os
            file_exists = os.path.exists(instance.background_image.path)
            logger.info(f"File exists on disk: {file_exists}")
        
        return instance


class PackagePosterSerializer(serializers.ModelSerializer):
    user_company_name = serializers.CharField(source='user.company_name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    template_details = PosterTemplateSerializer(source='template', read_only=True)
    
    # Add SerializerMethodField for poster files to return full URLs
    poster_jpg = serializers.SerializerMethodField()
    poster_png = serializers.SerializerMethodField()
    poster_pdf = serializers.SerializerMethodField()
    
    class Meta:
        model = PackagePoster
        fields = [
            'id', 'package_name', 'package_type', 'price', 'template',
            'user_company_name', 'user_phone', 'user_email', 'template_details',
            'poster_jpg', 'poster_png', 'poster_pdf', 'created_at'
        ]
    
    def get_poster_jpg(self, obj):
        """Return full URL for JPG poster"""
        if not obj.poster_jpg:
            return None
        
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.poster_jpg.url)
        return obj.poster_jpg.url
    
    def get_poster_png(self, obj):
        """Return full URL for PNG poster"""
        if not obj.poster_png:
            return None
        
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.poster_png.url)
        return obj.poster_png.url
    
    def get_poster_pdf(self, obj):
        """Return full URL for PDF poster"""
        if not obj.poster_pdf:
            return None
        
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.poster_pdf.url)
        return obj.poster_pdf.url
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class PosterGenerationSerializer(serializers.Serializer):
    package_name = serializers.CharField(max_length=200)
    package_type = serializers.ChoiceField(choices=PackagePoster.PACKAGE_TYPE_CHOICES)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    template_id = serializers.IntegerField()
    format = serializers.ChoiceField(choices=['jpg', 'png', 'pdf'], default='jpg')