from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from .models import Package
from .serializers import (
    PackageSerializer, 
    PackageListSerializer, 
    PackageCreateUpdateSerializer
)


class PackageListCreateView(generics.ListCreateAPIView):
    """
    GET: List all packages (filtered by user role)
    POST: Create a new package (supports base64 image upload)
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PackageListSerializer
        return PackageCreateUpdateSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'superadmin':
            # SuperAdmin can see all packages
            return Package.objects.all().select_related('created_by', 'assigned_to')
        
        elif user.role == 'agencyadmin':
            # AgencyAdmin can see:
            # 1. Packages they created
            # 2. Packages assigned to their franchises/freelancers
            # 3. Packages created by their franchises/freelancers
            
            # Get all users created by this agency admin (franchises and freelancers)
            subordinate_users = user.created_users.all()
            subordinate_user_ids = list(subordinate_users.values_list('id', flat=True))
            subordinate_user_ids.append(user.id)  # Include agency admin themselves
            
            return Package.objects.filter(
                Q(created_by_id__in=subordinate_user_ids) |
                Q(assigned_to_id__in=subordinate_user_ids)
            ).select_related('created_by', 'assigned_to').distinct()
        
        elif user.role == 'franchiseadmin':
            # FranchiseAdmin can see:
            # 1. Packages they created (if their creator allows them to create)
            # 2. Packages assigned to them
            # 3. Packages created by their freelancers
            
            # Get freelancers created by this franchise admin
            subordinate_users = user.created_users.all()
            subordinate_user_ids = list(subordinate_users.values_list('id', flat=True))
            subordinate_user_ids.append(user.id)  # Include franchise admin themselves
            
            return Package.objects.filter(
                Q(created_by_id__in=subordinate_user_ids) |
                Q(assigned_to_id__in=subordinate_user_ids)
            ).select_related('created_by', 'assigned_to').distinct()
        
        elif user.role == 'freelanceradmin':
            # FreelancerAdmin can only see packages assigned to them
            return Package.objects.filter(
                assigned_to=user
            ).select_related('created_by', 'assigned_to')
        
        else:
            # Default: return empty queryset for unknown roles
            return Package.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Check if user has permission to create packages
        if user.role == 'freelanceradmin':
            raise PermissionDenied("Freelancers do not have permission to create packages.")
        
        # Set the created_by field to current user
        serializer.save(created_by=user)
    
    def create(self, request, *args, **kwargs):
        """
        Override create to handle base64 image uploads and provide better error handling
        """
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            # Return detailed response with the created package
            headers = self.get_success_headers(serializer.data)
            return Response(
                {
                    'success': True,
                    'message': 'Package created successfully',
                    'data': serializer.data
                },
                status=status.HTTP_201_CREATED,
                headers=headers
            )
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'message': 'Failed to create package',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def list(self, request, *args, **kwargs):
        """
        Override list to add filtering by package type, destination, etc.
        Also handles base64 image encoding in responses
        """
        queryset = self.get_queryset()
        
        # Apply filters
        package_type = request.query_params.get('package_type', None)
        destination = request.query_params.get('destination', None)
        is_active = request.query_params.get('is_active', None)
        
        if package_type:
            queryset = queryset.filter(package_type=package_type)
        
        if destination:
            queryset = queryset.filter(destination__icontains=destination)
        
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Ordering
        ordering = request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


class PackageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific package
    PUT/PATCH: Update a package (supports base64 image upload)
    DELETE: Delete a package
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PackageSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'superadmin':
            return Package.objects.all().select_related('created_by', 'assigned_to')
        
        elif user.role == 'agencyadmin':
            subordinate_users = user.created_users.all()
            subordinate_user_ids = list(subordinate_users.values_list('id', flat=True))
            subordinate_user_ids.append(user.id)
            
            return Package.objects.filter(
                Q(created_by_id__in=subordinate_user_ids) |
                Q(assigned_to_id__in=subordinate_user_ids)
            ).select_related('created_by', 'assigned_to').distinct()
        
        elif user.role == 'franchiseadmin':
            subordinate_users = user.created_users.all()
            subordinate_user_ids = list(subordinate_users.values_list('id', flat=True))
            subordinate_user_ids.append(user.id)
            
            return Package.objects.filter(
                Q(created_by_id__in=subordinate_user_ids) |
                Q(assigned_to_id__in=subordinate_user_ids)
            ).select_related('created_by', 'assigned_to').distinct()
        
        elif user.role == 'freelanceradmin':
            return Package.objects.filter(
                assigned_to=user
            ).select_related('created_by', 'assigned_to')
        
        else:
            return Package.objects.none()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PackageCreateUpdateSerializer
        return PackageSerializer
    
    def update(self, request, *args, **kwargs):
        """
        Override update to handle base64 image uploads
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Check if user has permission to update this package
        user = request.user
        if user.role == 'freelanceradmin':
            raise PermissionDenied("Freelancers do not have permission to update packages.")
        
        # For non-superadmin users, check if they can update this package
        if user.role != 'superadmin':
            if instance.created_by != user:
                # Check if the package is assigned to user's subordinates
                subordinate_users = user.created_users.all()
                subordinate_user_ids = list(subordinate_users.values_list('id', flat=True))
                subordinate_user_ids.append(user.id)
                
                if instance.created_by_id not in subordinate_user_ids and instance.assigned_to_id not in subordinate_user_ids:
                    raise PermissionDenied("You don't have permission to update this package.")
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        try:
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            
            return Response({
                'success': True,
                'message': 'Package updated successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response(
                {
                    'success': False,
                    'message': 'Failed to update package',
                    'errors': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to add permission checks and better response
        """
        instance = self.get_object()
        user = request.user
        
        # Check permissions
        if user.role == 'freelanceradmin':
            raise PermissionDenied("Freelancers do not have permission to delete packages.")
        
        if user.role != 'superadmin' and instance.created_by != user:
            raise PermissionDenied("You can only delete packages you created.")
        
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'Package deleted successfully'
        }, status=status.HTTP_200_OK)
    
class PackageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific package
    PUT/PATCH: Update a specific package
    DELETE: Delete a specific package
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.role == 'superadmin':
            return Package.objects.all().select_related('created_by', 'assigned_to')
        
        elif user.role == 'agencyadmin':
            subordinate_users = user.created_users.all()
            subordinate_user_ids = list(subordinate_users.values_list('id', flat=True))
            subordinate_user_ids.append(user.id)
            
            return Package.objects.filter(
                Q(created_by_id__in=subordinate_user_ids) |
                Q(assigned_to_id__in=subordinate_user_ids)
            ).select_related('created_by', 'assigned_to').distinct()
        
        elif user.role == 'franchiseadmin':
            subordinate_users = user.created_users.all()
            subordinate_user_ids = list(subordinate_users.values_list('id', flat=True))
            subordinate_user_ids.append(user.id)
            
            return Package.objects.filter(
                Q(created_by_id__in=subordinate_user_ids) |
                Q(assigned_to_id__in=subordinate_user_ids)
            ).select_related('created_by', 'assigned_to').distinct()
        
        elif user.role == 'freelanceradmin':
            return Package.objects.filter(
                assigned_to=user
            ).select_related('created_by', 'assigned_to')
        
        else:
            return Package.objects.none()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PackageCreateUpdateSerializer
        return PackageSerializer
    
    def perform_update(self, serializer):
        user = self.request.user
        package = self.get_object()
        
        # Check if user has permission to update this package
        if user.role == 'freelanceradmin':
            raise PermissionDenied("Freelancers do not have permission to update packages.")
        
        # SuperAdmin can update any package
        if user.role == 'superadmin':
            serializer.save()
            return
        
        # AgencyAdmin can update packages they created or assigned to their network
        if user.role == 'agencyadmin':
            subordinate_users = user.created_users.all()
            subordinate_user_ids = list(subordinate_users.values_list('id', flat=True))
            subordinate_user_ids.append(user.id)
            
            if (package.created_by_id in subordinate_user_ids or 
                package.assigned_to_id in subordinate_user_ids):
                serializer.save()
                return
        
        # FranchiseAdmin can update packages they created or assigned to them/their freelancers
        if user.role == 'franchiseadmin':
            subordinate_users = user.created_users.all()
            subordinate_user_ids = list(subordinate_users.values_list('id', flat=True))
            subordinate_user_ids.append(user.id)
            
            if (package.created_by_id in subordinate_user_ids or 
                package.assigned_to_id in subordinate_user_ids):
                serializer.save()
                return
        
        raise PermissionDenied("You do not have permission to update this package.")
    
    def perform_destroy(self, instance):
        user = self.request.user
        
        # Only SuperAdmin and package creator can delete packages
        if user.role == 'superadmin' or instance.created_by == user:
            instance.delete()
        else:
            raise PermissionDenied("You do not have permission to delete this package.")


class MyPackagesView(generics.ListAPIView):
    """
    GET: Get all active packages for all authenticated users
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PackageListSerializer
    
    def get_queryset(self):
        # All authenticated users see all active packages
        return Package.objects.filter(is_active=True).select_related('created_by', 'assigned_to')


class AssignedPackagesView(generics.ListAPIView):
    """
    GET: Get packages assigned to the current user
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PackageListSerializer
    
    def get_queryset(self):
        user = self.request.user
        return Package.objects.filter(assigned_to=user).select_related('created_by', 'assigned_to')


class SuperAdminPackageUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH: Update a package - Only accessible to SuperAdmin
    Supports base64 image uploads through the Base64ImageField
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PackageCreateUpdateSerializer
    queryset = Package.objects.all()
    
    def get_object(self):
        """
        Override to ensure only superadmins can access this endpoint
        """
        user = self.request.user
        
        if user.role != 'superadmin':
            raise PermissionDenied("Only SuperAdmins can access this endpoint.")
        
        return super().get_object()
    
    def perform_update(self, serializer):
        """
        Only superadmins can update packages through this endpoint
        The Base64ImageField in the serializer will automatically handle base64 image conversion
        """
        user = self.request.user
        
        if user.role != 'superadmin':
            raise PermissionDenied("Only SuperAdmins can update packages through this endpoint.")
        
        # The serializer will automatically handle base64 image conversion
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """
        Override update method to add additional validation and handle base64 images
        """
        user = request.user
        
        if user.role != 'superadmin':
            return Response(
                {"detail": "Only SuperAdmins can update packages through this endpoint."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the package instance
        instance = self.get_object()
        
        # Create serializer with the request data
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        
        if serializer.is_valid():
            # The Base64ImageField will automatically convert base64 to file
            self.perform_update(serializer)
            
            # Return the updated package data
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, *args, **kwargs):
        """
        Override partial_update method to add additional validation and handle base64 images
        """
        user = request.user
        
        if user.role != 'superadmin':
            return Response(
                {"detail": "Only SuperAdmins can update packages through this endpoint."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the package instance
        instance = self.get_object()
        
        # Create serializer with the request data (partial=True for PATCH)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        
        if serializer.is_valid():
            # The Base64ImageField will automatically convert base64 to file
            self.perform_update(serializer)
            
            # Return the updated package data
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
class SuperAdminPackageDeleteView(generics.DestroyAPIView):
    """
    DELETE: Delete a package - Only accessible to SuperAdmin
    """
    permission_classes = [IsAuthenticated]
    queryset = Package.objects.all()
    
    def get_object(self):
        """
        Override to ensure only superadmins can access this endpoint
        """
        user = self.request.user
        
        if user.role != 'superadmin':
            raise PermissionDenied("Only SuperAdmins can delete packages through this endpoint.")
        
        return super().get_object()
    
    def perform_destroy(self, instance):
        """
        Only superadmins can delete packages through this endpoint
        """
        user = self.request.user
        
        if user.role != 'superadmin':
            raise PermissionDenied("Only SuperAdmins can delete packages through this endpoint.")
        
        instance.delete()
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy method to provide better response format
        """
        user = request.user
        
        if user.role != 'superadmin':
            return Response({
                'success': False,
                'message': "Only SuperAdmins can delete packages through this endpoint."
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # First check if package exists at all
            package_id = kwargs.get('pk')
            if not package_id:
                return Response({
                    'success': False,
                    'message': 'Package ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if package exists in database
            try:
                package_exists = Package.objects.filter(id=package_id).exists()
                if not package_exists:
                    return Response({
                        'success': False,
                        'message': f'Package with ID {package_id} does not exist'
                    }, status=status.HTTP_404_NOT_FOUND)
            except ValueError:
                return Response({
                    'success': False,
                    'message': 'Invalid package ID format'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            instance = self.get_object()
            self.perform_destroy(instance)
            
            return Response({
                'success': True,
                'message': 'Package deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Failed to delete package',
                'errors': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


