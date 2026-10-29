from django.urls import path
from .views import (
    LeadListCreateView, LeadDetailView, LeadAddNoteView,
    ExcelLeadUploadView, LeadAssignSingleView, LeadRecallToPoolView,
    LeadReassignFromPoolView, LeadAgencyPoolListView,
    TaskListCreateView, TaskDetailView
)

urlpatterns = [
    # Core Lead CRUD & Status Progression
    path('leads/', LeadListCreateView.as_view(), name='lead-list-create'),
    path('leads/<int:pk>/', LeadDetailView.as_view(), name='lead-detail'),
    path('leads/<int:pk>/update-status/', LeadAddNoteView.as_view(), name='lead-update-status'),

    # Meta Ads / Excel Ingestion & Round-Robin Distribution
    path('leads/upload-excel/', ExcelLeadUploadView.as_view(), name='lead-upload-excel'),

    # Caller Management & Reassignment Workflows
    path('leads/<int:lead_id>/assign-single/', LeadAssignSingleView.as_view(), name='lead-assign-single'),
    path('leads/recall-to-pool/', LeadRecallToPoolView.as_view(), name='lead-recall-to-pool'),
    path('leads/reassign-from-pool/', LeadReassignFromPoolView.as_view(), name='lead-reassign-from-pool'),
    path('leads/agency-pool/', LeadAgencyPoolListView.as_view(), name='lead-agency-pool'),
    # Tasks & Team Management (Module 18)
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
]
