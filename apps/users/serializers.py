# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import base64
import uuid
from django.core.files.base import ContentFile
from .models import User

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


class Base64FileField(serializers.FileField):
    """
    A Django REST framework field for handling file uploads through raw post data.
    It uses base64 for encoding and decoding the contents of the file.
    """
    
    def to_internal_value(self, data):
        # Check if this is a base64 string
        if isinstance(data, str) and data.startswith('data:'):
            # Parse the base64 string
            format, filestr = data.split(';base64,')
            ext = format.split('/')[-1]
            
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.{ext}"
            
            # Decode the base64 string
            data = ContentFile(base64.b64decode(filestr), name=filename)
        
        return super().to_internal_value(data)
    
    def to_representation(self, value):
        """Return full URL for the file"""
        if not value:
            return None
        
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(value.url)
        return value.url


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    # Use Base64ImageField for both input and output with full URLs
    profile_image = Base64ImageField(required=False, allow_null=True)
    company_logo = Base64ImageField(required=False, allow_null=True)
    # Use Base64FileField for agreement letter
    agreement_letter = Base64FileField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'phone', 'address', 'profile_image', 'is_active',
            'bio', 'website', 'company_name', 'agreement_letter', 'company_logo',
            'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_email(self, value):
        """Validate that the email is unique"""
        if self.instance:
            # For updates, exclude current instance
            if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("This email is already in use")
        else:
            # For creation, check if email already exists
            if User.objects.filter(email=value).exists():
                raise serializers.ValidationError("This email is already in use")
        return value

    def validate_phone(self, value):
        """Validate that the phone is unique if provided"""
        if value:  # Only validate if phone is provided
            if self.instance:
                # For updates, exclude current instance
                if User.objects.filter(phone=value).exclude(id=self.instance.id).exists():
                    raise serializers.ValidationError("This phone number is already in use")
            else:
                # For creation, check if phone already exists
                if User.objects.filter(phone=value).exists():
                    raise serializers.ValidationError("This phone number is already in use")
        return value

    def validate_agreement_letter(self, value):
        """Validate that the agreement letter is a PDF file"""
        if value:
            # Check file extension
            if hasattr(value, 'name') and not value.name.lower().endswith('.pdf'):
                raise serializers.ValidationError("Agreement letter must be a PDF file")
            
            # Check file size (limit to 10MB)
            if hasattr(value, 'size') and value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("Agreement letter file size cannot exceed 10MB")
        
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        
        # Create user with all fields (including file fields)
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # Update user fields (including file fields)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance

    def to_representation(self, instance):
        """Override to ensure context is passed to file fields"""
        representation = super().to_representation(instance)
        
        # Ensure the file fields get the request context
        if hasattr(self, 'context') and 'request' in self.context:
            request = self.context['request']
            
            # Handle profile_image
            if instance.profile_image:
                representation['profile_image'] = request.build_absolute_uri(instance.profile_image.url)
            
            # Handle company_logo
            if instance.company_logo:
                representation['company_logo'] = request.build_absolute_uri(instance.company_logo.url)
            
            # Handle agreement_letter
            if instance.agreement_letter:
                representation['agreement_letter'] = request.build_absolute_uri(instance.agreement_letter.url)
        
        return representation


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Authenticate using email instead of username
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        """Validate the new password using Django's password validators"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        """Validate that new password and confirm password match"""
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if new_password != confirm_password:
            raise serializers.ValidationError("New password and confirm password do not match")
        
        return attrs


class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(required=False, max_length=20)

    def validate(self, attrs):
        """Ensure either email or phone is provided, but not both"""
        email = attrs.get('email')
        phone = attrs.get('phone')
        
        if not email and not phone:
            raise serializers.ValidationError("Either email or phone must be provided")
        
        if email and phone:
            raise serializers.ValidationError("Provide either email or phone, not both")
        
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    reset_token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        """Validate the new password using Django's password validators"""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value

    def validate(self, attrs):
        """Validate that new password and confirm password match"""
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')
        
        if new_password != confirm_password:
            raise serializers.ValidationError("New password and confirm password do not match")
        
        return attrs


class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate_otp(self, value):
        """Validate that OTP contains only digits"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP must contain only digits")
        return value


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for certificate data"""
    full_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    company_logo = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'role', 'date_joined', 'full_name', 'company_name', 'company_logo'
        ]
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username
    
    def get_company_name(self, obj):
        """Get company name from creator or self"""
        company_user = obj.created_by if obj.created_by else obj
        return company_user.company_name or 'Your Travel Company'
    
    def get_company_logo(self, obj):
        """Get company logo URL from creator or self"""
        company_user = obj.created_by if obj.created_by else obj
        if company_user.company_logo:
            return company_user.company_logo.url
        return None