from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import status
from weasyprint import HTML, CSS
from xhtml2pdf import pisa
from io import BytesIO
import tempfile
import os
from .models import Booking, BookingTraveler, QuickBooking
from .serializers import (
    BookingSerializer, BookingTravelerSerializer, QuickBookingSerializer,
    BookingReceiptSerializer, QuickBookingReceiptSerializer
)
from apps.common.permissions import IsFranchiseOrAgencyAdmin


class BookingListCreateView(generics.ListCreateAPIView):
    """
    GET: List all bookings (filtered by user role)
    POST: Create a new booking
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsFranchiseOrAgencyAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'travel_month', 'payment_type']
    search_fields = ['booking_number', 'first_name', 'last_name', 'email']
    ordering_fields = ['created_at', 'travel_month', 'total_price']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != 'superadmin':
            queryset = queryset.filter(created_by=self.request.user)
        return queryset


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific booking
    PUT/PATCH: Update a specific booking
    DELETE: Delete a specific booking
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsFranchiseOrAgencyAdmin]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != 'superadmin':
            queryset = queryset.filter(created_by=self.request.user)
        return queryset


class QuickBookingListCreateView(generics.ListCreateAPIView):
    """
    GET: List all quick bookings
    POST: Create a new quick booking
    """
    queryset = QuickBooking.objects.all()
    serializer_class = QuickBookingSerializer
    permission_classes = [IsFranchiseOrAgencyAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['preferred_payment', 'is_converted_to_full_booking']
    search_fields = ['booking_number', 'first_name', 'last_name', 'email', 'destination']
    ordering_fields = ['created_at', 'travel_month', 'budget']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != 'superadmin':
            queryset = queryset.filter(created_by=self.request.user)
        return queryset


class QuickBookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific quick booking
    PUT/PATCH: Update a specific quick booking
    DELETE: Delete a specific quick booking
    """
    queryset = QuickBooking.objects.all()
    serializer_class = QuickBookingSerializer
    permission_classes = [IsFranchiseOrAgencyAdmin]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != 'superadmin':
            queryset = queryset.filter(created_by=self.request.user)
        return queryset
    def get_object(self):
        """
        Override to provide better error handling
        """
        try:
            obj = super().get_object()
            return obj
        except QuickBooking.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Quick booking not found or you don't have permission to update it.")
    
    def perform_update(self, serializer):
        """
        Override to add any additional logic before saving
        """
        # You can add any custom logic here before saving
        # For example, logging the update, sending notifications, etc.
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        """
        Override to customize the update response if needed
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        # Return custom response
        return Response({
            'message': 'Quick booking updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)

class BookingConfirmView(APIView):
    """
    POST: Confirm a booking
    """
    permission_classes = [IsFranchiseOrAgencyAdmin]
    
    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            
            # Check permissions
            if request.user.role != 'superadmin' and booking.created_by != request.user:
                return Response(
                    {'detail': 'You do not have permission to confirm this booking.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            booking.status = 'confirmed'
            booking.save()
            return Response({'status': 'Booking confirmed'})
            
        except Booking.DoesNotExist:
            return Response(
                {'detail': 'Booking not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class BookingCancelView(APIView):
    """
    POST: Cancel a booking
    """
    permission_classes = [IsFranchiseOrAgencyAdmin]
    
    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            
            # Check permissions
            if request.user.role != 'superadmin' and booking.created_by != request.user:
                return Response(
                    {'detail': 'You do not have permission to cancel this booking.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            booking.status = 'cancelled'
            booking.save()
            return Response({'status': 'Booking cancelled'})
            
        except Booking.DoesNotExist:
            return Response(
                {'detail': 'Booking not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )



class BookingReceiptView(APIView):
    """
    GET: Generate and return booking receipt/bill as PDF
    """
    permission_classes = [IsFranchiseOrAgencyAdmin]
    
    def get(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            
            # Check permissions
            if request.user.role != 'superadmin' and booking.created_by != request.user:
                return Response(
                    {'detail': 'You do not have permission to view this booking receipt.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get company details from the user who created the booking
            company_user = booking.created_by
            logo_url = None
            if company_user.company_logo:
                if hasattr(company_user.company_logo, 'url'):
                    # It's a file field object - build full URL
                    logo_url = request.build_absolute_uri(company_user.company_logo.url)
                else:
                    # It's already a URL string - check if it's relative or absolute
                    if company_user.company_logo.startswith(('http://', 'https://')):
                        logo_url = company_user.company_logo
                    else:
                        # It's a relative path, make it absolute
                        logo_url = request.build_absolute_uri(company_user.company_logo)
            
            company_details = {
                'name': company_user.company_name or 'Your Travel Company',
                'address': company_user.address or 'Your Company Address',
                'phone': company_user.phone or 'Your Phone Number',
                'email': company_user.email,
                'logo_url': logo_url,
                'website': company_user.website,
            }
            
            # Serialize booking data
            serializer = BookingReceiptSerializer(booking)
            context = {
                'booking': serializer.data,
                'company': company_details
            }
            
            # Render HTML template
            html_string = render_to_string('booking_receipt.html', context)
            
            # Generate PDF using WeasyPrint with base_url
            base_url = request.build_absolute_uri('/')
            html_doc = HTML(string=html_string, base_url=base_url)
            pdf_bytes = html_doc.write_pdf()
            
            # Verify PDF content is not empty
            if not pdf_bytes:
                return Response(
                    {'detail': 'Generated PDF is empty.'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Create HTTP response with proper headers
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="booking_{booking.booking_number}.pdf"'
            response['Content-Length'] = len(pdf_bytes)
            return response
            
        except Booking.DoesNotExist:
            return Response(
                {'detail': 'Booking not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return Response(
                {'detail': 'An error occurred while generating the PDF.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class QuickBookingReceiptView(APIView):
    permission_classes = [IsFranchiseOrAgencyAdmin]
    
    def get(self, request, pk):
        try:
            quick_booking = QuickBooking.objects.get(pk=pk)
            
            # Check permissions
            if request.user.role != 'superadmin' and quick_booking.created_by != request.user:
                return Response(
                    {'detail': 'You do not have permission to view this quick booking receipt.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get company details
            company_user = quick_booking.created_by
            
            # Handle logo URL properly - ensure full URL
            logo_url = None
            if company_user.company_logo:
                if hasattr(company_user.company_logo, 'url'):
                    # It's a file field object - build full URL
                    logo_url = request.build_absolute_uri(company_user.company_logo.url)
                else:
                    # It's already a URL string - check if it's relative or absolute
                    if company_user.company_logo.startswith(('http://', 'https://')):
                        logo_url = company_user.company_logo
                    else:
                        # It's a relative path, make it absolute
                        logo_url = request.build_absolute_uri(company_user.company_logo)
            
            company_details = {
                'name': company_user.company_name or 'Your Travel Company',
                'address': company_user.address or 'Your Company Address',
                'phone': company_user.phone or 'Your Phone Number',
                'email': company_user.email,
                'logo_url': logo_url,
                'website': company_user.website,
            }
            
            # Serialize quick booking data
            serializer = QuickBookingReceiptSerializer(quick_booking)
            context = {
                'quick_booking': serializer.data,
                'company': company_details
            }
            
            # Render HTML template
            html_string = render_to_string('quick_booking_receipt.html', context)
            
            # Generate PDF using WeasyPrint with base_url
            base_url = request.build_absolute_uri('/')
            html_doc = HTML(string=html_string, base_url=base_url)
            pdf_bytes = html_doc.write_pdf()
            
            # Create HTTP response
            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="quick_booking_{quick_booking.booking_number}.pdf"'
            response['Content-Length'] = len(pdf_bytes)
            
            return response
            
        except QuickBooking.DoesNotExist:
            return Response(
                {'detail': 'Quick booking not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return Response(
                {'detail': 'An error occurred while generating the PDF.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
               
class ConvertQuickBookingView(APIView):
    """
    POST: Convert quick booking to full booking
    """
    permission_classes = [IsFranchiseOrAgencyAdmin]
    
    def post(self, request, pk):
        try:
            quick_booking = QuickBooking.objects.get(pk=pk)
            
            # Check permissions
            if request.user.role != 'superadmin' and quick_booking.created_by != request.user:
                return Response(
                    {'detail': 'You do not have permission to convert this quick booking.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if quick_booking.is_converted_to_full_booking:
                return Response(
                    {'detail': 'This quick booking has already been converted.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create full booking from quick booking
            # You'll need to provide additional required fields
            booking_data = request.data
            booking_data.update({
                'first_name': quick_booking.first_name,
                'last_name': quick_booking.last_name,
                'email': quick_booking.email,
                'mobile_no': quick_booking.mobile,
                'travel_month': quick_booking.travel_month,
                'total_adults': quick_booking.number_of_travelers,
                'total_children': 0,
                'total_infants': 0,
            })
            
            serializer = BookingSerializer(data=booking_data, context={'request': request})
            if serializer.is_valid():
                booking = serializer.save()
                
                # Mark quick booking as converted
                quick_booking.is_converted_to_full_booking = True
                quick_booking.converted_booking = booking
                quick_booking.save()
                
                return Response({
                    'message': 'Quick booking converted successfully',
                    'booking_id': booking.id,
                    'booking_number': booking.booking_number
                })
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except QuickBooking.DoesNotExist:
            return Response(
                {'detail': 'Quick booking not found.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
class AllBookingDetailView(generics.ListAPIView):
    """
    GET: List all bookings created by the logged-in user
    """
    serializer_class = BookingSerializer
    permission_classes = [IsFranchiseOrAgencyAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'travel_month', 'payment_type']
    search_fields = ['booking_number', 'first_name', 'last_name', 'email']
    ordering_fields = ['created_at', 'travel_month', 'total_price']
    ordering = ['-created_at']  # Default ordering by latest first
    
    def get_queryset(self):
        """
        Return bookings created by the current logged-in user only
        """
        return Booking.objects.filter(created_by=self.request.user)


class AllQuickBookingDetailView(generics.ListAPIView):
    """
    GET: List all quick bookings created by the logged-in user
    """
    serializer_class = QuickBookingSerializer
    permission_classes = [IsFranchiseOrAgencyAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['preferred_payment', 'is_converted_to_full_booking']
    search_fields = ['booking_number', 'first_name', 'last_name', 'email', 'destination']
    ordering_fields = ['created_at', 'travel_month', 'budget']
    ordering = ['-created_at']  # Default ordering by latest first
    
    def get_queryset(self):
        """
        Return quick bookings created by the current logged-in user only
        """
        return QuickBooking.objects.filter(created_by=self.request.user)


class UserBookingDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve a specific booking by ID for the logged-in user
    """
    serializer_class = BookingSerializer
    permission_classes = [IsFranchiseOrAgencyAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Return bookings created by the current logged-in user only
        """
        return Booking.objects.filter(created_by=self.request.user)
    
    def get_object(self):
        """
        Override to provide better error handling
        """
        try:
            obj = super().get_object()
            return obj
        except Booking.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Booking not found or you don't have permission to view it.")


class UserQuickBookingDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve a specific quick booking by ID for the logged-in user
    """
    serializer_class = QuickBookingSerializer
    permission_classes = [IsFranchiseOrAgencyAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Return quick bookings created by the current logged-in user only
        """
        return QuickBooking.objects.filter(created_by=self.request.user)
    
    def get_object(self):
        """
        Override to provide better error handling
        """
        try:
            obj = super().get_object()
            return obj
        except QuickBooking.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound("Quick booking not found or you don't have permission to view it.")        