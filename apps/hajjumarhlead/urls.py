from django.urls import path
from . import views

app_name = 'umrah_booking'

urlpatterns = [
    # Demo booking APIs
    path('booking-demo/create/', views.HajjUmrahBookingDemoCreateView.as_view(), name='booking-demo-create'),
    path('booking-demo/list/', views.HajjUmrahBookingDemoListView.as_view(), name='booking-demo-list'),
    
    # Service booking APIs
    path('booking-service/create/', views.HajjUmrahBookingServiceCreateView.as_view(), name='booking-service-create'),
    path('booking-service/list/', views.HajjUmrahBookingServiceListView.as_view(), name='booking-service-list'),
]