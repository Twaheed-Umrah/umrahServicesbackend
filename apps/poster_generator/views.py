# views.py
from django.http import HttpResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import FileResponse, Http404
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from .models import PackagePoster, PosterTemplate
from apps.common.permissions import IsSuperAdmin
import base64
from .serializers import (
    PackagePosterSerializer, 
    PosterTemplateSerializer,
    PosterGenerationSerializer
)
from .services import PosterGeneratorService
from .permissions import CanCreatePosterPermission

import logging

logger = logging.getLogger(__name__)

class PosterTemplateListView(APIView):
    def get(self, request):
        """Get all poster templates with full image URLs"""
        templates = PosterTemplate.objects.all()
        # Pass request context to get full URLs
        serializer = PosterTemplateSerializer(templates, many=True, context={'request': request})
        return Response({
            'results': serializer.data
        })

class PosterTemplateDetailView(APIView):
    """
    API endpoint to get specific poster template details
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, template_id):
        """Get specific template by ID"""
        try:
            template = get_object_or_404(PosterTemplate, id=template_id, is_active=True)
            # Pass request context to get full URLs
            serializer = PosterTemplateSerializer(template, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Template not found: {str(e)}'}, 
                status=status.HTTP_404_NOT_FOUND
            )

class PosterTemplateManagementView(APIView):
    """
    API endpoint for super admin to manage poster templates (add/delete)
    """
    permission_classes = [IsSuperAdmin]  # Use custom permission
    
    def post(self, request):
        """Add new poster template (Super Admin only)"""
        try:
            # Pass request context to serializer
            serializer = PosterTemplateSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Template created successfully',
                    'template': serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create template: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, template_id):
        """Delete poster template (Super Admin only)"""
        try:
            try:
                template = PosterTemplate.objects.get(id=template_id)
            except PosterTemplate.DoesNotExist:
                return Response(
                    {'error': 'Template not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if template is being used by any posters
            posters_using_template = PackagePoster.objects.filter(template=template).count()
            if posters_using_template > 0:
                return Response(
                    {'error': f'Cannot delete template. It is being used by {posters_using_template} poster(s).'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            template_name = template.name
            template.delete()
            
            return Response({
                'message': f'Template "{template_name}" deleted successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to delete template: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class PackagePosterListView(APIView):
    """
    API endpoint to list and create package posters
    """
    permission_classes = [IsAuthenticated, CanCreatePosterPermission]
    
    def get(self, request):
        """Get all posters for the authenticated user"""
        try:
            posters = PackagePoster.objects.filter(user=request.user).order_by('-created_at')
            # Pass request context to get full URLs for all poster files and template images
            serializer = PackagePosterSerializer(posters, many=True, context={'request': request})
            return Response({
                'results': serializer.data,
                'count': posters.count()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Failed to fetch posters: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request):
        """Create a new package poster"""
        try:
            # Pass request context for full URLs
            serializer = PackagePosterSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': f'Failed to create poster: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PackagePosterDetailView(APIView):
    """
    API endpoint to get, update, or delete specific poster
    """
    permission_classes = [IsAuthenticated, CanCreatePosterPermission]
    
    def get_object(self, poster_id, user):
        """Get poster object for the authenticated user"""
        return get_object_or_404(PackagePoster, id=poster_id, user=user)
    
    def get(self, request, poster_id):
        """Get specific poster details"""
        try:
            poster = self.get_object(poster_id, request.user)
            # Pass request context to get full URLs
            serializer = PackagePosterSerializer(poster, context={'request': request})
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': f'Poster not found: {str(e)}'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    def put(self, request, poster_id):
        """Update specific poster"""
        try:
            poster = self.get_object(poster_id, request.user)
            # Pass request context to get full URLs
            serializer = PackagePosterSerializer(poster, data=request.data, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {'error': f'Failed to update poster: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def delete(self, request, poster_id):
        """Delete specific poster"""
        try:
            poster = self.get_object(poster_id, request.user)
            poster.delete()
            return Response(
                {'message': 'Poster deleted successfully'}, 
                status=status.HTTP_204_NO_CONTENT
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to delete poster: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PosterGeneratorView(APIView):
    """
    API endpoint to generate posters and return JSON response
    """
    permission_classes = [IsAuthenticated, CanCreatePosterPermission]

    def post(self, request):
        try:
            serializer = PosterGenerationSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {'success': False, 'error': 'Invalid data', 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = serializer.validated_data
            format_type = data.get('format', 'jpg').lower()

            # Validate format
            if format_type not in ['jpg', 'png', 'pdf']:
                return Response(
                    {'success': False, 'error': 'Invalid format. Supported formats: jpg, png, pdf'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Try to fetch existing poster
            existing_poster = PackagePoster.objects.filter(
                user=request.user,
                package_name=data['package_name'],
                package_type=data['package_type'],
                price=data['price'],
                template_id=data['template_id']
            ).first()

            if existing_poster:
                file_field = getattr(existing_poster, f'poster_{format_type}', None)
                if file_field and hasattr(file_field, 'file') and file_field.file:
                    try:
                        file_content = file_field.read()
                        filename = f"{existing_poster.package_name}_{format_type}.{format_type}"
                        
                        # Option A: Return base64 encoded file
                        file_base64 = base64.b64encode(file_content).decode('utf-8')
                        return Response({
                            'success': True,
                            'message': 'Poster retrieved successfully',
                            'filename': filename,
                            'file_data': file_base64,
                            'content_type': self._get_content_type(format_type),
                            'poster_id': existing_poster.id
                        })
                        
                    except Exception as e:
                        logger.warning(f"Could not read existing file: {e}")

            # Get the template
            try:
                template = PosterTemplate.objects.get(id=data['template_id'], is_active=True)
            except PosterTemplate.DoesNotExist:
                return Response(
                    {'success': False, 'error': 'Template not found or inactive'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not template.background_image or not hasattr(template.background_image, 'path'):
                return Response(
                    {'success': False, 'error': 'Template background image not found or not accessible'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user_data = {
                'company_name': getattr(request.user, 'company_name', 'Your Company'),
                'phone': getattr(request.user, 'phone', ''),
                'email': getattr(request.user, 'email', ''),
            }

            service = PosterGeneratorService()

            try:
                poster_file = service.generate_poster(
                    data, user_data, template.background_image.path, format_type
                )
            except Exception as e:
                logger.exception("Poster generation failed")
                return Response(
                    {'success': False, 'error': f'Failed to generate poster: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            if not poster_file or not hasattr(poster_file, 'getvalue'):
                return Response(
                    {'success': False, 'error': 'Poster generation failed - no file returned'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            if existing_poster:
                package_poster = existing_poster
            else:
                package_poster = PackagePoster.objects.create(
                    user=request.user,
                    package_name=data['package_name'],
                    package_type=data['package_type'],
                    price=data['price'],
                    template=template
                )

            filename = f"poster_{package_poster.id}_{format_type}.{format_type}"
            file_field = getattr(package_poster, f'poster_{format_type}')

            try:
                file_field.save(filename, ContentFile(poster_file.getvalue()))
                package_poster.save()
            except Exception as e:
                logger.exception("Failed to save poster file")
                return Response(
                    {'success': False, 'error': f'Failed to save poster file: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Return JSON response with file data
            poster_file.seek(0)
            file_base64 = base64.b64encode(poster_file.getvalue()).decode('utf-8')
            
            return Response({
                'success': True,
                'message': 'Poster generated successfully',
                'filename': filename,
                'file_data': file_base64,
                'content_type': self._get_content_type(format_type),
                'poster_id': package_poster.id
            })

        except Exception as e:
            logger.exception("Unexpected error occurred in PosterGeneratorView")
            return Response(
                {'success': False, 'error': f'Unexpected error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_content_type(self, format_type):
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'pdf': 'application/pdf'
        }
        return content_types.get(format_type, 'application/octet-stream')
    
class PosterDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, poster_id, format_type):
        poster = PackagePoster.objects.filter(id=poster_id, user=request.user).first()
        if not poster:
            raise Http404("Poster not found")

        file_field = getattr(poster, f'poster_{format_type}', None)

        if not file_field or not file_field.name:
            raise Http404("Requested poster file not available")

        # Optional logging
        print(f"Serving poster: {file_field.name}")
        print(f"Exists: {file_field.storage.exists(file_field.name)} | Size: {file_field.size}")

        try:
            return FileResponse(
                file_field.open("rb"),
                content_type=self._get_content_type(format_type),
                as_attachment=True,
                filename=f"{poster.package_name}_{format_type}.{format_type}"
            )
        except Exception as e:
            print(f"Failed to serve file: {e}")
            raise Http404("Error while serving file")

    def _get_content_type(self, format_type):
        return {
            'pdf': 'application/pdf',
            'png': 'image/png',
            'jpg': 'image/jpeg',
        }.get(format_type, 'application/octet-stream')