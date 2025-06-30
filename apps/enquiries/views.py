from datetime import timezone
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import APIKey, Package, HomePage, ContactUs
from .serializers import (
    APIKeySerializer, PackageSerializer, PackageUpdateSerializer,
    HomePageSerializer, HomePageUpdateSerializer, 
    ContactUsSerializer, ContactUsListSerializer
)
from .authentication import APIKeyAuthentication
from .permissions import HasValidAPIKey
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import SessionAuthentication
from apps.common.permissions import IsSuperAdmin 
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
        return Package.objects.all().order_by('-created_at')


class PackageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete package details (for logged-in users only)
    """
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    lookup_field = 'pk'
    
    def get_queryset(self):
        return Package.objects.all()
    
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
    queryset = Package.objects.filter(is_active=True)
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [HasValidAPIKey]

class PackageDetailAPIView(generics.RetrieveAPIView):
    """
    Get specific package details for external websites - Requires API Key
    """
    serializer_class = PackageSerializer
    lookup_field = 'package_type'
    queryset = Package.objects.filter(is_active=True)
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
        return HomePage.objects.all().order_by('-created_at')
    
    def perform_create(self, serializer):
        # Deactivate all existing homepage content before creating new one
        HomePage.objects.filter(is_active=True).update(is_active=False)
        serializer.save(is_active=True)

class HomePageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete homepage content (for logged-in users only)
    """
    serializer_class = HomePageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        return HomePage.objects.all()
    
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
    queryset = HomePage.objects.filter(is_active=True)
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
        # You can add additional logic here like sending notifications
        serializer.save()

class ContactUsListView(generics.ListAPIView):
    """
    Get all contact submissions - For logged-in users only
    """
    serializer_class = ContactUsListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        return ContactUs.objects.all().order_by('-created_at')

class ContactUsDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete specific contact submission - For logged-in users only
    """
    serializer_class = ContactUsListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]
    
    def get_queryset(self):
        return ContactUs.objects.all()
class ContactUsAdminView(generics.ListAPIView):
    """
    Get all contact submissions with user details - 
    SuperAdmin can see all, others see only their own submissions.
    """
    serializer_class = ContactUsListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get_queryset(self):
        user = self.request.user

        if IsSuperAdmin().has_permission(self.request, self):  # Use custom permission class
            return ContactUs.objects.all().order_by('-created_at')

        return ContactUs.objects.filter(user=user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        if IsSuperAdmin().has_permission(request, self):
            return Response({
                'message': 'All contact submissions (SuperAdmin view)',
                'total_count': queryset.count(),
                'data': serializer.data
            })

        return Response({
            'message': 'Your contact submissions',
            'total_count': queryset.count(),
            'data': serializer.data
        })


class ContactUsAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Get/Update/Delete specific contact submission - 
    SuperAdmin can access all, others only their own.
    """
    serializer_class = ContactUsListSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication, SessionAuthentication]

    def get_queryset(self):
        user = self.request.user

        if IsSuperAdmin().has_permission(self.request, self):
            return ContactUs.objects.all()

        return ContactUs.objects.filter(user=user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        if IsSuperAdmin().has_permission(request, self):
            data = serializer.data
            if hasattr(instance, 'user') and instance.user:
                data['user_details'] = {
                    'username': instance.user.username,
                    'email': instance.user.email,
                    'role': getattr(instance.user, 'role', 'N/A')
                }
            return Response(data)

        return Response(serializer.data)

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