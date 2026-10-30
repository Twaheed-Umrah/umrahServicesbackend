from django.urls import path
from . import views

app_name = 'visa'

urlpatterns = [
    # Visa Application endpoints
    path('applications/', views.VisaApplicationListView.as_view(), name='visa-list'),
    path('applications/<int:pk>/', views.VisaApplicationDetailView.as_view(), name='visa-detail'),
    path('applications/create/', views.VisaApplicationCreateView.as_view(), name='visa-create'),
]
