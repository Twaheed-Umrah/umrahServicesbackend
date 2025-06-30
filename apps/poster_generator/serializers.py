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
            # Parse the base64 string
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.{ext}"
            
            # Decode the base64 string
            data = ContentFile(base64.b64decode(imgstr), name=filename)
        
        return super().to_internal_value(data)
    
    def to_representation(self, value):
        """Return full URL for the image"""
        if not value:
            return None
        
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(value.url)
        return value.url

class PosterTemplateSerializer(serializers.ModelSerializer):
    background_image = serializers.SerializerMethodField()
    
    class Meta:
        model = PosterTemplate
        fields = ['id', 'name', 'template_type', 'background_image']
    
    def get_background_image(self, obj):
        """Return full URL for background image"""
        if not obj.background_image:
            return None
        
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.background_image.url)
        return obj.background_image.url

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