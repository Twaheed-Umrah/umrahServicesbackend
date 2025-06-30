from django.urls import path
from . import views

app_name = 'enquiries'

urlpatterns = [    
    path('keys/', views.APIKeyListCreateView.as_view(), name='apikey_list_create'),
    path('keys/<int:pk>/', views.APIKeyDetailView.as_view(), name='apikey_detail'),
    
    # Package Management (For logged-in CRM Users only)
    path('admin/packages/', views.PackageListCreateView.as_view(), name='admin_package_list_create'),
    path('admin/packages/<int:pk>/', views.PackageDetailView.as_view(), name='admin_package_detail'),
    
    # Homepage Management (For logged-in CRM Users only)
    path('admin/homepage/', views.HomePageListCreateView.as_view(), name='admin_homepage_list_create'),
    path('admin/homepage/<int:pk>/', views.HomePageDetailView.as_view(), name='admin_homepage_detail'),
    
    # Contact Management (For logged-in CRM Users only)
    path('admin/contacts/', views.ContactUsListView.as_view(), name='admin_contact_list'),
    path('admin/contacts/<int:pk>/', views.ContactUsDetailView.as_view(), name='admin_contact_detail'),
    #superAdmin
    path('contact-submissions/', views.ContactUsAdminView.as_view(), name='contact-submissions-list'),
    path('contact-submissions/<int:pk>/', views.ContactUsAdminDetailView.as_view(), name='contact-submission-detail'),
    # API Endpoints for External Websites (Require API Key)
    path('apikey/packages/', views.PackageListAPIView.as_view(), name='api_package_list'),
    path('apikey/packages/<str:package_type>/', views.PackageDetailAPIView.as_view(), name='api_package_detail'),
    path('apikey/homepage/', views.HomePageAPIView.as_view(), name='api_homepage'),
    path('apikey/contact/', views.ContactUsCreateAPIView.as_view(), name='api_contact_create'),
    
    # Utility Endpoints (Require API Key)
    path('apikey/validate-key/', views.validate_api_key, name='validate_api_key'),
    path('apikey/health/', views.api_health_check, name='api_health_check'),
]
