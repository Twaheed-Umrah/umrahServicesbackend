from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard stats endpoints
    path('stats/', views.dashboard_stats, name='dashboard-stats'),
    path('chart-data/', views.chart_data, name='chart-data'),
    path('booking-revenue/', views.booking_revenue_chart, name='booking-revenue-chart'),
    path('enquiry-distribution/', views.enquiry_distribution, name='enquiry-distribution'),
    path('recent-activities/', views.recent_activities, name='recent-activities'),
    path('summary/', views.dashboard_summary, name='dashboard-summary'),
]