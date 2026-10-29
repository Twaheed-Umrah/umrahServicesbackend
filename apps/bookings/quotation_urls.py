from django.urls import path
from .views import (
    QuotationListCreateView,
    QuotationDetailView,
    QuotationCloneView,
    QuotationConvertToBookingView,
    QuotationApproveDiscountView,
    QuotationPDFView,
    QuotationStatsView,
    QuotationSendEmailView,
    QuotationStatusUpdateView
)

urlpatterns = [
    path('', QuotationListCreateView.as_view(), name='quotation-list-create'),
    path('stats/', QuotationStatsView.as_view(), name='quotation-stats'),
    path('<int:pk>/', QuotationDetailView.as_view(), name='quotation-detail'),
    path('<int:pk>/clone/', QuotationCloneView.as_view(), name='quotation-clone'),
    path('<int:pk>/convert/', QuotationConvertToBookingView.as_view(), name='quotation-convert'),
    path('<int:pk>/approve-discount/', QuotationApproveDiscountView.as_view(), name='quotation-approve-discount'),
    path('<int:pk>/pdf/', QuotationPDFView.as_view(), name='quotation-pdf'),
    path('<int:pk>/send-email/', QuotationSendEmailView.as_view(), name='quotation-send-email'),
    path('<int:pk>/status/', QuotationStatusUpdateView.as_view(), name='quotation-update-status'),
]
