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
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import logout
from apps.common.permissions import IsSuperAdmin, IsAgencyAdmin
from .emailformate import send_password_reset_otp
import random
import string

from .models import OTPVerification
from .serializers import (
    LoginSerializer, UserSerializer,
    ChangePasswordSerializer, SendOTPSerializer, VerifyOTPSerializer,ResetPasswordSerializer
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

class VerifyTokenView(APIView):
    """
    Verify if the provided token is valid and not expired
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': 'Token is required', 'is_valid': False}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verify the token
            UntypedToken(token)
            
            # Additional check: decode and verify token payload
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
            
            if not user.is_active:
                return Response(
                    {'error': 'User account is disabled', 'is_valid': False}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            return Response({
                'message': 'Token is valid',
                'is_valid': True,
                'user_id': user.id,
                'username': user.username
            })
            
        except TokenError as e:
            return Response(
                {'error': 'Token is invalid or expired', 'is_valid': False}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': 'Token verification failed', 'is_valid': False}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

class RefreshTokenView(APIView):
    """
    Refresh access token using refresh token
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh')
        
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            refresh = RefreshToken(refresh_token)
            
            # Check if refresh token is blacklisted
            if refresh.check_blacklist():
                return Response(
                    {'error': 'Refresh token is blacklisted'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Generate new access token
            new_access_token = refresh.access_token
            
            return Response({
                'access': str(new_access_token),
                'message': 'Token refreshed successfully'
            })
            
        except TokenError as e:
            return Response(
                {'error': 'Invalid or expired refresh token'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': 'Token refresh failed'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user and request.user.is_authenticated:
            user = serializer.save(created_by=request.user)
        else:
            user = serializer.save()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Pass request context to serializer for full URLs
        user_serializer = UserSerializer(user, context={'request': request})
        
        return Response({
            "message": "User registered successfully",
            "user": user_serializer.data,
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
        # Pass request context to serializer for full URLs
        return Response(UserSerializer(request.user, context={'request': request}).data)


class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        """Update user profile"""
        serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
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
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'})
        except Exception:
            return Response(
                {'error': 'Invalid or expired token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )



# Add these new view classes to your existing views.py file

class GetAllUsersView(APIView):
    """Get all users - Only for Superadmin"""
    permission_classes = [IsSuperAdmin]  # Use your custom permission class

    def get(self, request):
        # Get all users
        users = User.objects.all().order_by('-date_joined')
        # Pass request context to serializer for building absolute URLs
        serializer = UserSerializer(users, many=True, context={'request': request})
        
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
            Q(role__in=['franchisesadmin', 'operations', 'sales_agent', 'caller', 'accountant'])
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
        
       
# DownloadCertificateView removed

class GetAgencyCallersView(APIView):
    """Get all telecallers created by or belonging to logged-in agency/admin"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role == 'superadmin':
            tenant_id = request.query_params.get('tenant_id', None)
            if tenant_id and tenant_id != 'all':
                callers = User.objects.filter(created_by_id=tenant_id, role__in=['caller', 'sales_agent']).order_by('-date_joined')
            else:
                callers = User.objects.filter(role__in=['caller', 'sales_agent']).order_by('-date_joined')
        else:
            callers = User.objects.filter(
                Q(created_by=request.user) & Q(role__in=['caller', 'sales_agent'])
            ).order_by('-date_joined')

        from .serializers import CallerAttendanceSerializer
        serializer = CallerAttendanceSerializer(callers, many=True)
        return Response({
            'success': True,
            'count': callers.count(),
            'callers': serializer.data
        })


class ToggleCallerAttendanceView(APIView):
    """Toggle caller attendance status (Present vs Absent)"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, user_id):
        try:
            if request.user.role == 'superadmin':
                caller = User.objects.get(id=user_id, role__in=['caller', 'sales_agent'])
            else:
                caller = User.objects.get(id=user_id, created_by=request.user, role__in=['caller', 'sales_agent'])
        except User.DoesNotExist:
            return Response({'error': 'Caller not found or permission denied'}, status=status.HTTP_404_NOT_FOUND)

        is_present = request.data.get('is_present')
        if is_present is not None:
            caller.is_present = bool(is_present)
            caller.caller_status = 'available' if caller.is_present else 'absent'
        
        caller_status = request.data.get('caller_status')
        if caller_status:
            caller.caller_status = caller_status
            if caller_status == 'absent':
                caller.is_present = False

        caller.save()
        from .serializers import CallerAttendanceSerializer
        status_text = 'PRESENT' if caller.is_present else 'ABSENT'
        return Response({
            'success': True,
            'message': f"Caller '{caller.username}' is now {status_text}",
            'caller': CallerAttendanceSerializer(caller).data
        })


class TenantListView(APIView):
    """
    SuperAdmin Multi-Tenant SaaS Hub:
    List all subscribed Tenants (franchisesadmin & agencyadmin) with staff and business statistics.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'superadmin':
            return Response({'detail': 'Only SuperAdmin can access Tenant SaaS Hub.'}, status=status.HTTP_403_FORBIDDEN)

        tenants = User.objects.filter(role__in=['franchisesadmin', 'agencyadmin']).order_by('-date_joined')
        
        from apps.crm.models import Lead
        from apps.bookings.models import Booking, Quotation

        data = []
        for t in tenants:
            staff_qs = User.objects.filter(created_by=t)
            op_count = staff_qs.filter(role='operations').count()
            sales_count = staff_qs.filter(role='sales_agent').count()
            caller_count = staff_qs.filter(role='caller').count()
            acct_count = staff_qs.filter(role='accountant').count()
            total_staff = staff_qs.count()

            lead_count = Lead.objects.filter(Q(user=t) | Q(assigned_caller__created_by=t)).count()
            booking_qs = Booking.objects.filter(Q(created_by=t) | Q(created_by__created_by=t))
            booking_count = booking_qs.count()
            total_rev = booking_qs.aggregate(models.Sum('total_price'))['total_price__sum'] or 0
            quote_count = Quotation.objects.filter(Q(created_by=t) | Q(created_by__created_by=t)).count()

            data.append({
                'id': t.id,
                'company_name': t.company_name or t.get_full_name() or t.username,
                'owner_name': t.get_full_name() or t.username,
                'email': t.email,
                'phone': t.phone or 'N/A',
                'role': t.role,
                'role_display': t.get_role_display(),
                'address': t.address or '',
                'date_joined': t.date_joined.strftime('%Y-%m-%d') if t.date_joined else '',
                'is_active': t.is_active,
                'staff': {
                    'operations': op_count,
                    'sales_agents': sales_count,
                    'callers': caller_count,
                    'accountants': acct_count,
                    'total': total_staff,
                },
                'metrics': {
                    'leads_count': lead_count,
                    'bookings_count': booking_count,
                    'quotations_count': quote_count,
                    'total_revenue': float(total_rev),
                }
            })

        return Response({
            'total_tenants': len(data),
            'active_tenants': sum(1 for x in data if x['is_active']),
            'total_staff': sum(x['staff']['total'] for x in data),
            'total_leads': sum(x['metrics']['leads_count'] for x in data),
            'total_revenue': sum(x['metrics']['total_revenue'] for x in data),
            'tenants': data
        })


class TenantDetailView(APIView):
    """
    SuperAdmin Multi-Tenant SaaS Hub:
    Deep-dive into a specific tenant: their staff, leads, bookings, quotes, and profile.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, tenant_id):
        if request.user.role != 'superadmin':
            return Response({'detail': 'Only SuperAdmin can access Tenant details.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            tenant = User.objects.get(id=tenant_id, role__in=['franchisesadmin', 'agencyadmin'])
        except User.DoesNotExist:
            return Response({'detail': 'Tenant not found.'}, status=status.HTTP_404_NOT_FOUND)

        from apps.crm.models import Lead
        from apps.bookings.models import Booking, Quotation

        staff_qs = User.objects.filter(created_by=tenant).order_by('role', '-date_joined')
        staff_list = []
        for s in staff_qs:
            staff_list.append({
                'id': s.id,
                'name': s.get_full_name() or s.username,
                'email': s.email,
                'phone': s.phone or 'N/A',
                'role': s.role,
                'role_display': s.get_role_display(),
                'is_present': s.is_present,
                'caller_status': s.caller_status,
                'date_joined': s.date_joined.strftime('%Y-%m-%d') if s.date_joined else '',
            })

        leads_qs = Lead.objects.filter(Q(user=tenant) | Q(assigned_caller__created_by=tenant)).order_by('-created_at')[:50]
        leads_data = []
        for l in leads_qs:
            leads_data.append({
                'id': l.id,
                'name': l.name,
                'mobile': l.mobile_number,
                'email': l.email,
                'city': l.city,
                'status': l.status,
                'assigned_caller_name': l.assigned_caller.get_full_name() if l.assigned_caller else 'In Agency Pool',
                'created_at': l.created_at.strftime('%Y-%m-%d'),
            })

        status_counts = dict(Lead.objects.filter(Q(user=tenant) | Q(assigned_caller__created_by=tenant)).values_list('status').annotate(models.Count('status')))

        booking_qs = Booking.objects.filter(Q(created_by=tenant) | Q(created_by__created_by=tenant)).order_by('-created_at')[:20]
        bookings_data = []
        for b in booking_qs:
            bookings_data.append({
                'id': b.id,
                'booking_number': b.booking_number,
                'customer_name': f"{b.first_name} {b.last_name}",
                'travel_month': b.travel_month,
                'package_name': b.package_name,
                'total_price': float(b.total_price or 0),
                'payable_amount': float(b.payable_amount or 0),
                'balance': float(b.balance or 0),
                'status': b.status,
                'created_at': b.created_at.strftime('%Y-%m-%d'),
            })

        quote_qs = Quotation.objects.filter(Q(created_by=tenant) | Q(created_by__created_by=tenant)).order_by('-created_at')[:20]
        quotes_data = []
        for q in quote_qs:
            quotes_data.append({
                'id': q.id,
                'quotation_number': q.quotation_number,
                'contact_name': q.contact_name,
                'package_name': q.package_name,
                'total_customer_price': float(q.total_customer_price or 0),
                'gross_margin_percentage': float(q.gross_margin_percentage or 0),
                'status': q.status,
                'created_at': q.created_at.strftime('%Y-%m-%d'),
            })

        return Response({
            'tenant': {
                'id': tenant.id,
                'company_name': tenant.company_name or tenant.get_full_name() or tenant.username,
                'owner_name': tenant.get_full_name() or tenant.username,
                'email': tenant.email,
                'phone': tenant.phone,
                'role': tenant.role,
                'address': tenant.address,
                'website': tenant.website,
                'is_active': tenant.is_active,
                'date_joined': tenant.date_joined.strftime('%Y-%m-%d') if tenant.date_joined else '',
            },
            'staff': staff_list,
            'leads': {
                'total_count': Lead.objects.filter(Q(user=tenant) | Q(assigned_caller__created_by=tenant)).count(),
                'status_breakdown': status_counts,
                'recent': leads_data
            },
            'bookings': {
                'total_count': Booking.objects.filter(Q(created_by=tenant) | Q(created_by__created_by=tenant)).count(),
                'total_revenue': float(Booking.objects.filter(Q(created_by=tenant) | Q(created_by__created_by=tenant)).aggregate(models.Sum('total_price'))['total_price__sum'] or 0),
                'recent': bookings_data
            },
            'quotations': {
                'total_count': Quotation.objects.filter(Q(created_by=tenant) | Q(created_by__created_by=tenant)).count(),
                'recent': quotes_data
            }
        })
