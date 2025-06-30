from django.urls import path
from . import views

app_name = 'visa'

urlpatterns = [
    # Visa Application URLs
    path('applications/', views.VisaApplicationListView.as_view(), name='application-list'),
    path('applications/create/', views.VisaApplicationCreateView.as_view(), name='application-create'),
    path('applications/<int:pk>/', views.VisaApplicationDetailView.as_view(), name='application-detail'),
    path('applications/<int:pk>/update/', views.VisaApplicationUpdateView.as_view(), name='application-update'),
    path('applications/<int:pk>/delete/', views.VisaApplicationDeleteView.as_view(), name='application-delete'),
    path('applications/<int:pk>/submit/', views.submit_visa_application, name='application-submit'),
    
    # SuperAdmin only URLs
    path('applications/<int:pk>/status-update/', views.VisaApplicationStatusUpdateView.as_view(), name='application-status-update'),
    path('dashboard/', views.visa_application_dashboard, name='dashboard'),
    
    # Document URLs
    path('applications/<int:application_id>/documents/', views.VisaDocumentListView.as_view(), name='document-list'),
    path('applications/<int:application_id>/documents/upload/', views.VisaDocumentUploadView.as_view(), name='document-upload'),
    path('applications/<int:application_id>/documents/<int:pk>/delete/', views.VisaDocumentDeleteView.as_view(), name='document-delete'),
    path('documents/<int:document_id>/verify/', views.verify_document, name='document-verify'),
    
    # Utility URLs
    path('visa-types/', views.visa_types_list, name='visa-types'),
    path('status-choices/', views.application_status_choices, name='status-choices'),
     path('payments/create/', views.PaymentCreateView.as_view(), name='payment-create'),
    
    # User's own payment history
    path('payments/my-history/', views.UserPaymentHistoryView.as_view(), name='my-payment-history'),
    
    # SuperAdmin only views
    path('payments/', views.PaymentListView.as_view(), name='payment-list'),
    path('payments/<int:pk>/', views.PaymentDetailView.as_view(), name='payment-detail'),
    path('payments/<int:pk>/update-status/', views.PaymentStatusUpdateView.as_view(), name='payment-status-update'),
    
    # Dashboard and utility endpoints
    path('payments/dashboard/', views.payment_dashboard, name='payment-dashboard'),
    path('payments/bulk-update/', views.bulk_update_payments, name='bulk-update-payments'),
    
    # Choice lists
    path('payments/modes/', views.payment_modes_list, name='payment-modes-list'),
    path('payments/status-choices/', views.payment_status_choices, name='payment-status-choices'),
    
]