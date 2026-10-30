from django.urls import path
from .views import (
    LoginView, MeView, UpdateProfileView, ChangePasswordView,
    SendEmailOTPView, VerifyEmailOTPView, SendPhoneOTPView, 
    VerifyPhoneOTPView, RegisterView, LogoutView, GetAllUsersView,
    GetTenantUsersView, GetUserDetailsByIdView,
    ForgotPasswordSendOTPView, ForgotPasswordVerifyOTPView, ResetPasswordView,
    RefreshTokenView, VerifyTokenView, GetAgencyCallersView, ToggleCallerAttendanceView,
    TenantListView, TenantDetailView
)

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # User profile endpoints
    path('users/me/', MeView.as_view(), name='user-me'),
    path('users/update-profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('users/change-password/', ChangePasswordView.as_view(), name='change-password'),

    # Forgot Password endpoints
    path('users/forgot-password/send-otp/', ForgotPasswordSendOTPView.as_view(), name='forgot-password-send-otp'),
    path('users/forgot-password/verify-otp/', ForgotPasswordVerifyOTPView.as_view(), name='forgot-password-verify-otp'),
    path('users/forgot-password/reset/', ResetPasswordView.as_view(), name='reset-password'),
    
    # OTP verification endpoints
    path('users/send-email-otp/', SendEmailOTPView.as_view(), name='send-email-otp'),
    path('users/verify-email-otp/', VerifyEmailOTPView.as_view(), name='verify-email-otp'),
    path('users/send-phone-otp/', SendPhoneOTPView.as_view(), name='send-phone-otp'),
    path('users/verify-phone-otp/', VerifyPhoneOTPView.as_view(), name='verify-phone-otp'),
    
    # SaaS Multi-Tenant Management Hub (SuperAdmin)
    path('tenants/', TenantListView.as_view(), name='tenant-list'),
    path('tenants/<int:tenant_id>/', TenantDetailView.as_view(), name='tenant-detail'),

    # Team & Caller management
    path('users/all/', GetAllUsersView.as_view(), name='get-all-users'),
    path('users/agency/', GetTenantUsersView.as_view(), name='get-agency-users'),
    path('callers/', GetAgencyCallersView.as_view(), name='get-agency-callers'),
    path('callers/<int:user_id>/toggle-attendance/', ToggleCallerAttendanceView.as_view(), name='toggle-caller-attendance'),
    path('users/<int:user_id>/', GetUserDetailsByIdView.as_view(), name='get-user-details'),
    path('verify-token/', VerifyTokenView.as_view(), name='verify-token'),
    path('refresh-token/', RefreshTokenView.as_view(), name='refresh-token'),
]
