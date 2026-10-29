from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Travel Management API",
        default_version='v1',
        description="API for Travel Management System",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/packages/', include('apps.packages.urls')),
    path('api/bookings/', include('apps.bookings.urls')),
    path('api/quotations/', include('apps.bookings.quotation_urls')),
    path('api/enquiries/', include('apps.enquiries.urls')),
    path('api/visa/', include('apps.visa.urls')),
    path('api/dashboard/', include('apps.dashboard.urls')),
    path('api/posters-generate/', include('apps.poster_generator.urls')), 
    path('api/crm/', include('apps.crm.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
