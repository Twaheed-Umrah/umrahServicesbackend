from django.urls import path
from . import views

app_name = 'poster_generator'

urlpatterns = [
    # Template endpoints
    path('templates/', views.PosterTemplateListView.as_view(), name='template_list'),
    path('templates/<int:template_id>/', views.PosterTemplateDetailView.as_view(), name='template_detail'),
    
    # Poster endpoints
    path('posters/', views.PackagePosterListView.as_view(), name='poster_list'),
    path('posters/<int:poster_id>/', views.PackagePosterDetailView.as_view(), name='poster_detail'),
    path('admin/templates/', views.PosterTemplateManagementView.as_view(), name='admin-template-create'),
    path('admin/templates/<int:template_id>/', views.PosterTemplateManagementView.as_view(), name='admin-template-delete'),
    # Poster generation and download
    path('posters/poster/', views.PosterGeneratorView.as_view(), name='poster_generate'),
    path('<int:poster_id>/download/<str:format_type>/', 
         views.PosterDownloadView.as_view(), 
         name='poster_download'),
]