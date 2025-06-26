from django.urls import path
from .views import (
    BookingListCreateView,
    BookingDetailView,
    QuickBookingListCreateView,
    QuickBookingDetailView,
    BookingConfirmView,
    BookingCancelView,
    BookingReceiptView,
    QuickBookingReceiptView,
    ConvertQuickBookingView,
    AllBookingDetailView,
    AllQuickBookingDetailView,
    UserBookingDetailView,
    UserQuickBookingDetailView,
)

urlpatterns = [
    # Existing URLs
    path('bookings/', BookingListCreateView.as_view(), name='booking-list-create'),
    path('bookings/<int:pk>/', BookingDetailView.as_view(), name='booking-detail'),
    path('quick-bookings/', QuickBookingListCreateView.as_view(), name='quick-booking-list-create'),
    path('quick-bookings/<int:pk>/', QuickBookingDetailView.as_view(), name='quick-booking-detail'),
    path('bookings/<int:pk>/confirm/', BookingConfirmView.as_view(), name='booking-confirm'),
    path('bookings/<int:pk>/cancel/', BookingCancelView.as_view(), name='booking-cancel'),
    path('bookings/<int:pk>/receipt/', BookingReceiptView.as_view(), name='booking-receipt'),
    path('quick-bookings/<int:pk>/receipt/', QuickBookingReceiptView.as_view(), name='quick-booking-receipt'),
    path('quick-bookings/<int:pk>/convert/', ConvertQuickBookingView.as_view(), name='convert-quick-booking'),
    
    # New URLs for user-specific views
    path('my-bookings/', AllBookingDetailView.as_view(), name='user-all-bookings'),
    path('my-quick-bookings/', AllQuickBookingDetailView.as_view(), name='user-all-quick-bookings'),
    path('my-bookings/<int:id>/', UserBookingDetailView.as_view(), name='user-booking-detail'),
    path('my-quick-bookings/<int:id>/', UserQuickBookingDetailView.as_view(), name='user-quick-booking-detail'),
]