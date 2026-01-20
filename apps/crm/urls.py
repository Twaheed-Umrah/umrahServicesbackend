from django.urls import path
from .views import LeadListCreateView, LeadDetailView, LeadAddNoteView

urlpatterns = [
    path('leads/', LeadListCreateView.as_view(), name='lead-list-create'),
    path('leads/<int:pk>/', LeadDetailView.as_view(), name='lead-detail'),
    path('leads/<int:pk>/update-status/', LeadAddNoteView.as_view(), name='lead-update-status'),
]
