from django.urls import path
from . import views

app_name = 'visa'

urlpatterns = [
    # Payment Processing & Ledger URLs (Module 15)
    path('payments/create/', views.PaymentCreateView.as_view(), name='payment-create'),
    path('payments/my-history/', views.UserPaymentHistoryView.as_view(), name='my-payment-history'),
    path('payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/<int:pk>/update-status/', views.PaymentStatusUpdateView.as_view(), name='payment-status-update'),
    path('payments/dashboard/', views.payment_dashboard, name='payment-dashboard'),
    path('payments/bulk-update/', views.bulk_update_payments, name='bulk-update-payments'),
    path('payments/modes/', views.payment_modes_list, name='payment-modes-list'),
    path('payments/status-choices/', views.payment_status_choices, name='payment-status-choices'),
]
