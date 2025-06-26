from django.urls import path
from .views import (
    LoginView, MeView, UpdateProfileView, ChangePasswordView,
    SendEmailOTPView, VerifyEmailOTPView, SendPhoneOTPView, 
    VerifyPhoneOTPView, RegisterView, LogoutView,    GetAllUsersView,
    GetAgencyUsersView,
    GetUserDetailsByIdView,

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
    
    # OTP verification endpoints
    path('users/send-email-otp/', SendEmailOTPView.as_view(), name='send-email-otp'),
    path('users/verify-email-otp/', VerifyEmailOTPView.as_view(), name='verify-email-otp'),
    path('users/send-phone-otp/', SendPhoneOTPView.as_view(), name='send-phone-otp'),
    path('users/verify-phone-otp/', VerifyPhoneOTPView.as_view(), name='verify-phone-otp'),
     path('users/all/', GetAllUsersView.as_view(), name='get-all-users'),
    path('users/agency/', GetAgencyUsersView.as_view(), name='get-agency-users'),
    path('users/<int:user_id>/', GetUserDetailsByIdView.as_view(), name='get-user-details'),
]