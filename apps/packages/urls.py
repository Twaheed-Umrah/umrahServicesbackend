from django.urls import path
from . import views

urlpatterns = [
    # Main package CRUD operations
    path('packages/', views.PackageListCreateView.as_view(), name='package-list-create'),
    path('packages/<int:pk>/', views.PackageDetailView.as_view(), name='package-detail'),
    path('packages/<int:pk>/superadmin-update/', views.SuperAdminPackageUpdateView.as_view(), name='superadmin-package-update'),
    # User-specific package views
    path('packages/my/', views.MyPackagesView.as_view(), name='my-packages'),
    path('packages/assigned/', views.AssignedPackagesView.as_view(), name='assigned-packages'),
    path('packages/delete/<int:pk>/', views.SuperAdminPackageDeleteView.as_view(), name='superadmin-package-delete'),

    # Package Departures
    path('departures/', views.PackageDepartureListCreateView.as_view(), name='departure-list-create'),
    path('departures/<int:pk>/', views.PackageDepartureDetailView.as_view(), name='departure-detail'),
    # Supplier & Contract Management (Module 14)
    path('suppliers/', views.SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),
]
