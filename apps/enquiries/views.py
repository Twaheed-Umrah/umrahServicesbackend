from datetime import timezone
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import APIKey, Package, HomePage, ContactUs, GalleryImage
from .serializers import (
    APIKeySerializer, PackageSerializer, PackageUpdateSerializer,
    HomePageSerializer, HomePageUpdateSerializer, 
    ContactUsSerializer, ContactUsListSerializer,
    GalleryImageSerializer
)
from .authentication import APIKeyAuthentication
from .permissions import HasValidAPIKey
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import get_user_model

from apps.common.permissions import IsSuperAdmin 
User = get_user_model()
# API Key Management Views (For CRM users)

class APIKeyListCreateView(generics.ListCreateAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class APIKeyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = APIKeySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        return APIKey.objects.filter(user=self.request.user)

# Package Management Views
class PackageListCreateView(generics.ListCreateAPIView):
    """
    List packages (for logged-in users) or Create packages (for logged-in users only)
    """
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        return Package.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class PackageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete package details (for logged-in users only)
    """
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    lookup_field = 'pk'
    
    def get_queryset(self):
        return Package.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PackageUpdateSerializer
        return PackageSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        # ✅ Return a JSON response instead of 204 No Content
        return Response({
                         'success': True,
                        'message': 'Package deleted successfully'
                         }, status=status.HTTP_200_OK)

# Package Views for External Websites (API Key Required)
class PackageListAPIView(generics.ListAPIView):
    """
    Get all active packages for external websites - Requires API Key
    """
    serializer_class = PackageSerializer
    
    def get_queryset(self):
        return Package.objects.filter(user=self.request.user, is_active=True)
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]

class PackageDetailAPIView(generics.RetrieveAPIView):
    """
    Get specific package details for external websites - Requires API Key
    """
    serializer_class = PackageSerializer
    lookup_field = 'package_type'
    
    def get_queryset(self):
        return Package.objects.filter(user=self.request.user, is_active=True)
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]

# HomePage Management Views
class HomePageListCreateView(generics.ListCreateAPIView):
    """
    List homepage content (for logged-in users) or Create homepage content (for logged-in users only)
    """
    serializer_class = HomePageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        return HomePage.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Deactivate all existing homepage content for THIS user before creating new one
        HomePage.objects.filter(user=self.request.user, is_active=True).update(is_active=False)
        serializer.save(user=self.request.user, is_active=True)

class HomePageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete homepage content (for logged-in users only)
    """
    serializer_class = HomePageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        return HomePage.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return HomePageUpdateSerializer
        return HomePageSerializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'success': True}, status=status.HTTP_200_OK)
        
# HomePage Views for External Websites (API Key Required)
class HomePageAPIView(generics.ListAPIView):
    """
    Get homepage content for external websites - Requires API Key
    """
    serializer_class = HomePageSerializer
    
    def get_queryset(self):
        return HomePage.objects.filter(user=self.request.user, is_active=True)
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]

# Contact Us Views
class ContactUsCreateAPIView(generics.CreateAPIView):
    """
    Submit contact form from external websites - Requires API Key
    """
    serializer_class = ContactUsSerializer
    queryset = ContactUs.objects.all()
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]
    
    def perform_create(self, serializer):
        api_key = self.request.auth  # the APIKey object from authentication
        submitted_by_user = api_key.user if api_key else None

        serializer.save(api_key=api_key, submitted_by_user=submitted_by_user)

class ContactUsListView(generics.ListAPIView):
    """
    Get contact submissions based on user's API keys - For logged-in users only
    Shows only contacts submitted through their API keys
    """
    serializer_class = ContactUsListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        # Get all API keys belonging to the logged-in user
        user_api_keys = APIKey.objects.filter(user=user)
        # Return contacts submitted through user's API keys
        return ContactUs.objects.filter(
            api_key__in=user_api_keys
        ).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        # Add additional context
        user_api_keys_count = APIKey.objects.filter(user=request.user).count()
        
        return Response({
            'message': f'Contact submissions from your {user_api_keys_count} API key(s)',
            'total_count': queryset.count(),
            'user_api_keys': user_api_keys_count,
            'data': serializer.data
        })

class ContactUsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete specific contact submission - Only from user's API keys
    """
    serializer_class = ContactUsListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        user_api_keys = APIKey.objects.filter(user=user)
        return ContactUs.objects.filter(api_key__in=user_api_keys)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        data = serializer.data
        # Add API key information
        if instance.api_key:
            data['api_key_info'] = {
                'name': instance.api_key.name,
                'website_url': instance.api_key.website_url,
                'key_id': instance.api_key.id
            }
        
        return Response(data)
class ContactUsAdminView(generics.ListAPIView):
    """
    Admin view for contact submissions:
    - SuperAdmin: sees ALL contact submissions
    - Regular users: see only contacts from their API keys
    """
    queryset = None  # ✅ This tells DRF not to expect a static queryset
    serializer_class = ContactUsListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get_queryset(self):
        user = self.request.user

        if IsSuperAdmin().has_permission(self.request, self):
            return ContactUs.objects.all().order_by('-created_at')

        user_api_keys = APIKey.objects.filter(user=user)
        return ContactUs.objects.filter(
            api_key__in=user_api_keys
        ).order_by('-created_at')
    
class ContactUsAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin detail view for contact submissions:
    - SuperAdmin: can access any contact submission
    - Regular users: can access only contacts from their API keys
    """
    serializer_class = ContactUsListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get_queryset(self):
        user = self.request.user

        if IsSuperAdmin().has_permission(self.request, self):
            return ContactUs.objects.all()

        # Regular users can only access contacts from their API keys
        user_api_keys = APIKey.objects.filter(user=user)
        return ContactUs.objects.filter(api_key__in=user_api_keys)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        if IsSuperAdmin().has_permission(request, self):
            # SuperAdmin gets full details including API key owner info
            if instance.api_key:
                data['api_key_details'] = {
                    'key_id': instance.api_key.id,
                    'key_name': instance.api_key.name,
                    'website_url': instance.api_key.website_url,
                    'owner_username': instance.api_key.user.username,
                    'owner_email': instance.api_key.user.email,
                    'created_at': instance.api_key.created_at,
                    'last_used': instance.api_key.last_used
                }
            return Response(data)

        # Regular users get basic API key info
        if instance.api_key:
            data['api_key_info'] = {
                'name': instance.api_key.name,
                'website_url': instance.api_key.website_url,
                'key_id': instance.api_key.id
            }

        return Response(data)


# API Key Validation
@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
@permission_classes([HasValidAPIKey])
def validate_api_key(request):
    """
    Validate API key and return user info
    """
    return Response({
        'valid': True,
        'user': request.user.username,
        'api_key_name': request.auth.name,
        'website_url': request.auth.website_url,
        'message': 'API Key is valid and active'
    })

# Health check endpoint for websites
@api_view(['GET'])
@authentication_classes([APIKeyAuthentication])
@permission_classes([HasValidAPIKey])
def api_health_check(request):
    """
    Health check endpoint for external websites
    """
    return Response({
        'status': 'healthy',
        'timestamp': timezone.now(),
        'api_key_valid': True,
        'website_url': request.auth.website_url
    })

# Gallery Management Views
class GalleryImageListCreateView(generics.ListCreateAPIView):
    """
    List gallery images for the authenticated user or upload a new one.
    """
    serializer_class = GalleryImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get_queryset(self):
        return GalleryImage.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class GalleryImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Update or delete a gallery image.
    """
    serializer_class = GalleryImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get_queryset(self):
        return GalleryImage.objects.filter(user=self.request.user)

# Gallery API for External Websites
class GalleryImageAPIView(generics.ListAPIView):
    """
    Get gallery images for external websites - Requires API Key.
    Only shows images belonging to the API key owner.
    """
    serializer_class = GalleryImageSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]

    def get_queryset(self):
        return GalleryImage.objects.filter(user=self.request.user, is_active=True)