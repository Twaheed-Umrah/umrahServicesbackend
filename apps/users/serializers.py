# serializers.py
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'phone', 'address', 'profile_image', 'is_active',
            'bio', 'website', 'company_name', 'license_number', 'company_logo',
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

    def create(self, validated_data):
        password = validated_data.pop('password')
        
        # Create user with all fields
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Update password if provided
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance

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
# Add this to your serializers.py file (optional)

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