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

]