from rest_framework import serializers
from .models import APIKey, Package, HomePage, ContactUs, GalleryImage
from django.contrib.auth.models import User
from drf_extra_fields.fields import Base64ImageField, Base64FileField
from rest_framework.exceptions import ValidationError
import mimetypes
import base64
from io import BytesIO

class CustomBase64FileField(Base64FileField):
    # Define allowed file types
    ALLOWED_TYPES = ['pdf', 'doc', 'docx', 'txt', 'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv', 'bin']
    
    def get_file_extension(self, filename, decoded_file):
        """
        Get file extension from MIME type or filename
        """
        try:
            # First try to get extension from content type if available
            if hasattr(self, 'content_type') and self.content_type:
                file_type = mimetypes.guess_extension(self.content_type)
                if file_type:
                    return file_type.replace('.', '')
            
            # Try to guess from filename if provided
            if filename:
                _, ext = filename.rsplit('.', 1) if '.' in filename else ('', '')
                if ext:
                    return ext.lower()
            
            # Try to guess from file content
            if decoded_file:
                # Reset file pointer if it's a file-like object
                if hasattr(decoded_file, 'seek'):
                    decoded_file.seek(0)
                
                # Read first few bytes to determine file type
                if hasattr(decoded_file, 'read'):
                    header = decoded_file.read(16)
                    decoded_file.seek(0)  # Reset pointer
                else:
                    header = decoded_file[:16] if len(decoded_file) >= 16 else decoded_file
                
                # Basic file type detection based on magic numbers
                if header.startswith(b'\xFF\xD8\xFF'):
                    return 'jpg'
                elif header.startswith(b'\x89PNG\r\n\x1A\n'):
                    return 'png'
                elif header.startswith(b'GIF8'):
                    return 'gif'
                elif header.startswith(b'\x00\x00\x00\x20ftypmp4') or header.startswith(b'\x00\x00\x00\x18ftypmp4'):
                    return 'mp4'
                elif header.startswith(b'RIFF') and b'WEBP' in header:
                    return 'webp'
                elif header.startswith(b'%PDF'):
                    return 'pdf'
            
            # Fallback to generic binary extension
            return 'bin'
            
        except Exception:
            return 'bin'

class CustomBase64ImageField(Base64ImageField):
    # Define allowed image types
    ALLOWED_TYPES = ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'webp', 'tiff']
    
    def get_file_extension(self, filename, decoded_file):
        """
        Get image file extension using magic numbers (file signatures)
        """
        try:
            # Get file data
            if decoded_file:
                if hasattr(decoded_file, 'read'):
                    # If it's a file-like object
                    decoded_file.seek(0)
                    file_data = decoded_file.read()
                    decoded_file.seek(0)
                else:
                    # If it's bytes
                    file_data = decoded_file
                
                # Check magic numbers for common image formats
                if len(file_data) >= 2:
                    # JPEG
                    if file_data.startswith(b'\xFF\xD8\xFF'):
                        return 'jpeg'
                    # PNG
                    elif file_data.startswith(b'\x89PNG\r\n\x1A\n'):
                        return 'png'
                    # GIF
                    elif file_data.startswith(b'GIF87a') or file_data.startswith(b'GIF89a'):
                        return 'gif'
                    # WebP
                    elif file_data.startswith(b'RIFF') and b'WEBP' in file_data[:12]:
                        return 'webp'
                    # BMP
                    elif file_data.startswith(b'BM'):
                        return 'bmp'
                    # TIFF
                    elif file_data.startswith(b'II*\x00') or file_data.startswith(b'MM\x00*'):
                        return 'tiff'
            
            # Fallback to filename extension
            if filename and '.' in filename:
                _, ext = filename.rsplit('.', 1)
                ext = ext.lower()
                if ext in self.ALLOWED_TYPES:
                    return 'jpeg' if ext == 'jpg' else ext
            
            # If we still can't determine, raise validation error
            raise ValidationError("Unsupported or unrecognizable image format.")
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError("Error processing image file.")

class APIKeySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = APIKey
        fields = ['id', 'key', 'name', 'is_active', 'created_at', 'last_used', 'website_url', 'username']
        read_only_fields = ['key', 'created_at', 'last_used', 'username']

class PackageSerializer(serializers.ModelSerializer):
    features_list = serializers.ReadOnlyField(source='get_features_list')
    image=CustomBase64ImageField(required=False)
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = Package
        fields = [
            'id', 'package_type', 'title', 'description', 'price', 'currency',
            'image', 'features', 'features_list', 'duration_days', 'is_active',
            'is_featured', 'created_at', 'updated_at', 'username'
        ]

class PackageUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Package
        fields = ['title', 'description', 'image','price', 'currency', 'features', 'duration_days', 'is_featured']

class HomePageSerializer(serializers.ModelSerializer):
    background_image = CustomBase64ImageField(required=False)
    background_video = CustomBase64FileField(required=False)
    
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = HomePage
        fields = [
            'id', 'content', 'background_video', 'background_image',
            'welcome_title', 'welcome_subtitle', 'is_active',
            'created_at', 'updated_at', 'username'
        ]

class HomePageUpdateSerializer(serializers.ModelSerializer):
    background_image = CustomBase64ImageField(required=False)
    background_video = CustomBase64FileField(required=False)
    
    class Meta:
        model = HomePage
        fields = ['content', 'background_image', 'background_video', 'welcome_title', 'welcome_subtitle']

class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = ['name', 'email', 'phone', 'package_type', 'message']

class ContactUsListSerializer(serializers.ModelSerializer):
    api_key_name = serializers.CharField(source='api_key.name', read_only=True)
    api_key_website = serializers.CharField(source='api_key.website_url', read_only=True)
    submitted_by_username = serializers.CharField(source='submitted_by_user.username', read_only=True)
    
    class Meta:
        model = ContactUs
        fields = [
            'id', 'name', 'email', 'phone', 'package_type', 'message', 
            'created_at', 'api_key_name', 'api_key_website', 'submitted_by_username'
        ]
        read_only_fields = ['created_at', 'api_key', 'submitted_by_user']

class GalleryImageSerializer(serializers.ModelSerializer):
    image = CustomBase64ImageField(required=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = GalleryImage
        fields = ['id', 'image', 'title', 'is_active', 'created_at', 'username']
        read_only_fields = ['created_at', 'username']