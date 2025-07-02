from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from django.db.models import Q
from apps.common.permissions import IsSuperAdmin, IsAgencyAdmin
from .emailformate import send_password_reset_otp
import random
import string

from .models import OTPVerification
from .serializers import (
    LoginSerializer, UserSerializer,
    ChangePasswordSerializer, SendOTPSerializer, VerifyOTPSerializer,CertificateSerializer,ResetPasswordSerializer
)

User = get_user_model()


def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def send_email_otp(email, otp):
    """Send OTP via email"""
    try:
        send_mail(
            'Email Verification OTP',
            f'Your OTP for email verification is: {otp}. This OTP will expire in 10 minutes.',
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


def send_sms_otp(phone, otp):
    """Send OTP via SMS - implement your SMS provider here"""
    # TODO: Implement actual SMS sending logic
    print(f"Sending SMS to {phone}: Your OTP is {otp}")
    return True


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "message": "User registered successfully",
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
            'message': 'Login successful'
        })


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get current user profile"""
        return Response(UserSerializer(request.user).data)


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """Update user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Profile updated successfully',
            'user': serializer.data
        })

    def patch(self, request):
        """Partial update user profile"""
        return self.put(request)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']

        # Verify old password
        if not check_password(old_password, user.password):
            return Response(
                {'error': 'Current password is incorrect'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': 'Password changed successfully'
        })


class SendEmailOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        # Check if email already exists for another user
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'No account found with this email address'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate and save OTP
        otp = generate_otp()
        OTPVerification.objects.update_or_create(
            user=user,
            verification_type='email',
            defaults={
                'otp': otp,
                'new_value': email,
                'expires_at': timezone.now() + timedelta(minutes=10),
                'is_verified': False
            }
        )
        user_name = f"{user.first_name} {user.last_name}".strip() or user.username or "Valued Customer"
        # Send OTP via email
        if send_password_reset_otp(email, otp,user_name):
            return Response({
                'message': 'OTP sent to your email successfully',
                'email': email
            })
        else:
            return Response(
                {'error': 'Failed to send OTP. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyEmailOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data['otp']

        try:
            # Find valid OTP record
            otp_record = OTPVerification.objects.get(
                user=request.user,
                verification_type='email',
                otp=otp,
                is_verified=False,
                expires_at__gt=timezone.now()
            )
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update user email and mark OTP as verified
        request.user.email = otp_record.new_value
        request.user.save()
        
        otp_record.is_verified = True
        otp_record.save()
        
        return Response({
            'message': 'Email updated successfully'
        })


class SendPhoneOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data.get('phone')

        # Check if phone already exists for another user
        if User.objects.filter(phone=phone).exclude(id=request.user.id).exists():
            return Response(
                {'error': 'This phone number is already registered to another account'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate and save OTP
        otp = generate_otp()
        OTPVerification.objects.update_or_create(
            user=request.user,
            verification_type='phone',
            defaults={
                'otp': otp,
                'new_value': phone,
                'expires_at': timezone.now() + timedelta(minutes=10),
                'is_verified': False
            }
        )

        # Send OTP via SMS
        if send_sms_otp(phone, otp):
            return Response({
                'message': 'OTP sent to your phone successfully'
            })
        else:
            return Response(
                {'error': 'Failed to send OTP. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class ForgotPasswordSendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        # Check if user exists with this email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'No account found with this email address'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate and save OTP
        otp = generate_otp()
        OTPVerification.objects.update_or_create(
            user=user,
            verification_type='password_reset',
            defaults={
                'otp': otp,
                'new_value': email,  # Store email for reference
                'expires_at': timezone.now() + timedelta(minutes=10),
                'is_verified': False
            }
        )
        user_name = f"{user.first_name} {user.last_name}".strip() or user.username or "Valued Customer"

        # Send OTP via email
        if send_password_reset_otp(email, otp,user_name):
            return Response({
                'message': 'OTP sent to your email successfully',
                'email': email
            })
        else:
            return Response(
                {'error': 'Failed to send OTP. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ForgotPasswordVerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data['otp']
        email = request.data.get('email')

        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid request'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Find valid OTP record
            otp_record = OTPVerification.objects.get(
                user=user,
                verification_type='password_reset',
                otp=otp,
                is_verified=False,
                expires_at__gt=timezone.now()
            )
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark OTP as verified but don't delete it yet
        otp_record.is_verified = True
        otp_record.save()
        
        return Response({
            'message': 'OTP verified successfully',
            'reset_token': str(otp_record.id)  # Use OTP record ID as reset token
        })


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        reset_token = serializer.validated_data['reset_token']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid request'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Verify the reset token (OTP record ID)
            otp_record = OTPVerification.objects.get(
                id=reset_token,
                user=user,
                verification_type='password_reset',
                is_verified=True,
                expires_at__gt=timezone.now()
            )
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired reset token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Reset the password
        user.set_password(new_password)
        user.save()
        
        # Delete the OTP record as it's no longer needed
        otp_record.delete()
        
        return Response({
            'message': 'Password reset successfully'
        })
class VerifyPhoneOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data['otp']

        try:
            # Find valid OTP record
            otp_record = OTPVerification.objects.get(
                user=request.user,
                verification_type='phone',
                otp=otp,
                is_verified=False,
                expires_at__gt=timezone.now()
            )
        except OTPVerification.DoesNotExist:
            return Response(
                {'error': 'Invalid or expired OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update user phone and mark OTP as verified
        request.user.phone = otp_record.new_value
        request.user.save()
        
        otp_record.is_verified = True
        otp_record.save()
        
        return Response({
            'message': 'Phone number updated successfully'
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Logout user by blacklisting refresh token"""
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({
                'message': 'Logged out successfully'
            })
        except Exception as e:
            return Response(
                {'error': 'Invalid token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


# Add these new view classes to your existing views.py file

class GetAllUsersView(APIView):
    """Get all users - Only for Superadmin"""
    permission_classes = [IsSuperAdmin]  # Use your custom permission class

    def get(self, request):
        # Get all users
        users = User.objects.all().order_by('-date_joined')
        serializer = UserSerializer(users, many=True)
        
        return Response({
            'message': 'All users retrieved successfully',
            'count': users.count(),
            'users': serializer.data
        })


class GetAgencyUsersView(APIView):
    """Get all franchise admins and freelancers created by logged-in agency admin"""
    permission_classes = [IsAgencyAdmin]

    def get(self, request):
        # Corrected 'user_type' to 'role'
        users = User.objects.filter(
            Q(created_by=request.user) & 
            Q(role__in=['franchisesadmin', 'freelancer'])
        ).order_by('-date_joined')

        serializer = UserSerializer(users, many=True)

        return Response({
            'message': 'Agency users retrieved successfully',
            'count': users.count(),
            'users': serializer.data
        })
    
class GetUserDetailsByIdView(APIView):
    """Get user details by ID - accessible from anywhere"""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)            
            serializer = UserSerializer(user)
            
            return Response({
                'message': 'User details retrieved successfully',
                'user': serializer.data
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
       
class DownloadCertificateView(APIView):
    """
    GET: Generate and return user certificate as PDF
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            # Get company details from the user who created this user (their parent/creator)
            company_user = user.created_by if user.created_by else user
            company_details = {
                'name': company_user.company_name or 'Your Travel Company',
                'logo_url': company_user.company_logo.url if company_user.company_logo else None,
                  }
            
            # Serialize user data (similar to QuickBookingReceiptSerializer)
            serializer = CertificateSerializer(user)
            context = {
                'user': serializer.data,
                'company': company_details
            }
            
            # Render HTML template
            html_string = render_to_string('certificate.html', context)
            
            # Generate PDF using WeasyPrint
            html_doc = HTML(string=html_string)
            pdf_bytes = html_doc.write_pdf()
            if not pdf_bytes:
                return Response(
                    {'detail': 'Generated PDF is empty.'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            # Create HTTP response
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="certificate_{user.username}.pdf"'
            response['Content-Length'] = len(pdf_bytes)
            
            return response
            
        except Exception as e:
            print(f"Error generating certificate PDF: {str(e)}")
            return Response(
                {'detail': 'An error occurred while generating the certificate.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )