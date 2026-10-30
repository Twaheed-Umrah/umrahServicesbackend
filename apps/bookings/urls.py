from django.urls import path, include
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
    PassengerManifestView,
    HotelVoucherPDFView,
    TransportVoucherPDFView,
    SupportTicketListCreateView,
    SupportTicketDetailView,
    # Module 6: Quotations
    QuotationListCreateView,
    QuotationDetailView,
    QuotationCloneView,
    QuotationConvertToBookingView,
    QuotationApproveDiscountView,
    QuotationPDFView,
    QuotationStatsView,
    AccountingSummaryView,
    BookingTravelerCreateView,
    BookingTravelerDetailView
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
    # Vouchers and Manifests (Modules 4, 12, 13, 17, 21)
    path('bookings/<int:pk>/manifest/', PassengerManifestView.as_view(), name='passenger-manifest'),
    path('bookings/<int:pk>/hotel-voucher/', HotelVoucherPDFView.as_view(), name='hotel-voucher'),
    path('bookings/<int:pk>/transport-voucher/', TransportVoucherPDFView.as_view(), name='transport-voucher'),
    # Support Tickets & Complaints (Module 20)
    path('support-tickets/', SupportTicketListCreateView.as_view(), name='support-ticket-list-create'),
    path('support-tickets/<int:pk>/', SupportTicketDetailView.as_view(), name='support-ticket-detail'),

    # Module 6: Quotation & Costing URLs
    # Module 15: Accounting & Finance Hub
    path('accounting-summary/', AccountingSummaryView.as_view(), name='accounting-summary'),
    # Module 4: Family & Group Pilgrims Management
    path('bookings/<int:booking_id>/travelers/', BookingTravelerCreateView.as_view(), name='booking-traveler-create'),
    path('travelers/<int:pk>/', BookingTravelerDetailView.as_view(), name='booking-traveler-detail'),
    path('quotations/', QuotationListCreateView.as_view(), name='quotation-list-create'),
    path('quotations/stats/', QuotationStatsView.as_view(), name='quotation-stats'),
    path('quotations/<int:pk>/', QuotationDetailView.as_view(), name='quotation-detail'),
    path('quotations/<int:pk>/clone/', QuotationCloneView.as_view(), name='quotation-clone'),
    path('quotations/<int:pk>/convert/', QuotationConvertToBookingView.as_view(), name='quotation-convert'),
    path('quotations/<int:pk>/approve-discount/', QuotationApproveDiscountView.as_view(), name='quotation-approve-discount'),
    path('quotations/<int:pk>/pdf/', QuotationPDFView.as_view(), name='quotation-pdf'),
]
