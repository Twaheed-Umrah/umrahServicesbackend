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
]