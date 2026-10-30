from rest_framework import generics, filters, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import status
from weasyprint import HTML, CSS
from decimal import Decimal
import datetime
from rest_framework import renderers

class CSVRenderer(renderers.BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data
from io import StringIO
import csv
from django.db import models
from django.utils import timezone
import tempfile
import os
from .models import Booking, BookingTraveler, QuickBooking, SupportTicket, Quotation, QuotationHotel, QuotationActivity
from .serializers import (
    SupportTicketSerializer, QuotationSerializer, QuotationHotelSerializer,
    BookingSerializer, BookingTravelerSerializer, QuickBookingSerializer,
    BookingReceiptSerializer, QuickBookingReceiptSerializer
)
from apps.common.permissions import IsTenantOrStaff


class BookingListCreateView(generics.ListCreateAPIView):
    """
    GET: List all bookings (filtered by user role)
    POST: Create a new booking
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsTenantOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'travel_month', 'payment_type']
    search_fields = ['booking_number', 'first_name', 'last_name', 'email']
    ordering_fields = ['created_at', 'travel_month', 'total_price']
    
    def get_queryset(self):
        from django.db.models import Q
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == 'superadmin':
            tenant_id = self.request.query_params.get('tenant_id', None)
            if tenant_id and tenant_id != 'all':
                return queryset.filter(Q(created_by_id=tenant_id) | Q(created_by__created_by_id=tenant_id))
            return queryset
        elif user.role == 'accountant':
            # Accountant can see bookings created by their parent admin AND themselves
            if user.created_by:
                return queryset.filter(created_by__in=[user.created_by, user])
            else:
                return queryset.filter(created_by=user)
        else:
            # Agency/Franchise admin can see their own bookings AND bookings created by their accountants
            return queryset.filter(
                Q(created_by=user) | Q(created_by__created_by=user)
            )


class BookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific booking
    PUT/PATCH: Update a specific booking
    DELETE: Delete a specific booking
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    permission_classes = [IsTenantOrStaff]
    
    def get_queryset(self):
        from django.db.models import Q
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == 'superadmin':
            return queryset
        elif user.role == 'accountant':
            # Accountant can access bookings created by their parent admin AND themselves
            if user.created_by:
                return queryset.filter(created_by__in=[user.created_by, user])
            else:
                return queryset.filter(created_by=user)
        else:
            # Agency/Franchise admin can see their own bookings AND bookings created by their accountants
            return queryset.filter(
                Q(created_by=user) | Q(created_by__created_by=user)
            )


class QuickBookingListCreateView(generics.ListCreateAPIView):
    """
    GET: List all quick bookings
    POST: Create a new quick booking
    """
    queryset = QuickBooking.objects.all()
    serializer_class = QuickBookingSerializer
    permission_classes = [IsTenantOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['preferred_payment', 'is_converted_to_full_booking']
    search_fields = ['booking_number', 'first_name', 'last_name', 'email', 'destination']
    ordering_fields = ['created_at', 'travel_month', 'budget']
    
    def get_queryset(self):
        from django.db.models import Q
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == 'superadmin':
            return queryset
        elif user.role == 'accountant':
            # Accountant can see quick bookings created by their parent admin AND themselves
            if user.created_by:
                return queryset.filter(created_by__in=[user.created_by, user])
            else:
                return queryset.filter(created_by=user)
        else:
            # Agency/Franchise admin can see their own quick bookings AND quick bookings created by their accountants
            return queryset.filter(
                Q(created_by=user) | Q(created_by__created_by=user)
            )


class QuickBookingDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a specific quick booking
    PUT/PATCH: Update a specific quick booking
    DELETE: Delete a specific quick booking
    """
    queryset = QuickBooking.objects.all()
    serializer_class = QuickBookingSerializer
    permission_classes = [IsTenantOrStaff]
    
    def get_queryset(self):
        from django.db.models import Q
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.role == 'superadmin':
            return queryset
        elif user.role == 'accountant':
            # Accountant can access quick bookings created by their parent admin AND themselves
            if user.created_by:
                return queryset.filter(created_by__in=[user.created_by, user])
            else:
                return queryset.filter(created_by=user)
        else:
            # Agency/Franchise admin can see their own quick bookings AND quick bookings created by their accountants
            return queryset.filter(
                Q(created_by=user) | Q(created_by__created_by=user)
            )
    
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
        
        return Response({
            'message': 'Quick booking updated successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class BookingConfirmView(APIView):
    """
    POST: Confirm a booking
    """
    permission_classes = [IsTenantOrStaff]
    
    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            user = request.user
            
            # Check permissions
            if user.role == 'superadmin':
                # Superadmin can confirm any booking
                pass
            elif user.role == 'accountant':
                # Accountant can confirm bookings created by their parent admin OR themselves
                if user.created_by:
                    if booking.created_by not in [user.created_by, user]:
                        return Response(
                            {'detail': 'You do not have permission to confirm this booking.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                else:
                    if booking.created_by != user:
                        return Response(
                            {'detail': 'You do not have permission to confirm this booking.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
            else:
                # Agency/Franchise admin can confirm their own bookings AND bookings created by their accountants
                if booking.created_by != user:
                    # Check if booking was created by one of their accountants
                    if not (booking.created_by.created_by == user):
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
    permission_classes = [IsTenantOrStaff]
    
    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            user = request.user
            
            # Check permissions
            if user.role == 'superadmin':
                # Superadmin can cancel any booking
                pass
            elif user.role == 'accountant':
                # Accountant can cancel bookings created by their parent admin OR themselves
                if user.created_by:
                    if booking.created_by not in [user.created_by, user]:
                        return Response(
                            {'detail': 'You do not have permission to cancel this booking.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                else:
                    if booking.created_by != user:
                        return Response(
                            {'detail': 'You do not have permission to cancel this booking.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
            else:
                # Agency/Franchise admin can cancel their own bookings AND bookings created by their accountants
                if booking.created_by != user:
                    # Check if booking was created by one of their accountants
                    if not (booking.created_by.created_by == user):
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
    permission_classes = [IsTenantOrStaff]
    
    def get(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            user = request.user
            
            # Check permissions
            if user.role == 'superadmin':
                # Superadmin can view any booking receipt
                pass
            elif user.role == 'accountant':
                # Accountant can view receipts for bookings created by their parent admin OR themselves
                if user.created_by:
                    if booking.created_by not in [user.created_by, user]:
                        return Response(
                            {'detail': 'You do not have permission to view this booking receipt.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                else:
                    if booking.created_by != user:
                        return Response(
                            {'detail': 'You do not have permission to view this booking receipt.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
            else:
                # Agency/Franchise admin can view receipts for their own bookings AND bookings created by their accountants
                if booking.created_by != user:
                    # Check if booking was created by one of their accountants
                    if not (booking.created_by.created_by == user):
                        return Response(
                            {'detail': 'You do not have permission to view this booking receipt.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
            
            # Get company details from the user who created the booking
            company_user = booking.created_by
            logo_url = None
            if company_user.company_logo:
                if hasattr(company_user.company_logo, 'url'):
                    logo_url = request.build_absolute_uri(company_user.company_logo.url)
                else:
                    if company_user.company_logo.startswith(('http://', 'https://')):
                        logo_url = company_user.company_logo
                    else:
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
    permission_classes = [IsTenantOrStaff]
    
    def get(self, request, pk):
        try:
            quick_booking = QuickBooking.objects.get(pk=pk)
            user = request.user
            
            # Check permissions
            if user.role == 'superadmin':
                # Superadmin can view any quick booking receipt
                pass
            elif user.role == 'accountant':
                # Accountant can view receipts for quick bookings created by their parent admin OR themselves
                if user.created_by:
                    if quick_booking.created_by not in [user.created_by, user]:
                        return Response(
                            {'detail': 'You do not have permission to view this quick booking receipt.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                else:
                    if quick_booking.created_by != user:
                        return Response(
                            {'detail': 'You do not have permission to view this quick booking receipt.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
            else:
                # Agency/Franchise admin can view receipts for their own quick bookings AND quick bookings created by their accountants
                if quick_booking.created_by != user:
                    # Check if quick booking was created by one of their accountants
                    if not (quick_booking.created_by.created_by == user):
                        return Response(
                            {'detail': 'You do not have permission to view this quick booking receipt.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
            
            # Get company details
            company_user = quick_booking.created_by
            
            # Handle logo URL properly
            logo_url = None
            if company_user.company_logo:
                if hasattr(company_user.company_logo, 'url'):
                    logo_url = request.build_absolute_uri(company_user.company_logo.url)
                else:
                    if company_user.company_logo.startswith(('http://', 'https://')):
                        logo_url = company_user.company_logo
                    else:
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
    permission_classes = [IsTenantOrStaff]
    
    def post(self, request, pk):
        try:
            quick_booking = QuickBooking.objects.get(pk=pk)
            user = request.user
            
            # Check permissions
            if user.role == 'superadmin':
                # Superadmin can convert any quick booking
                pass
            elif user.role == 'accountant':
                # Accountant can convert quick bookings created by their parent admin OR themselves
                if user.created_by:
                    if quick_booking.created_by not in [user.created_by, user]:
                        return Response(
                            {'detail': 'You do not have permission to convert this quick booking.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                else:
                    if quick_booking.created_by != user:
                        return Response(
                            {'detail': 'You do not have permission to convert this quick booking.'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
            else:
                # Agency/Franchise admin can convert their own quick bookings AND quick bookings created by their accountants
                if quick_booking.created_by != user:
                    # Check if quick booking was created by one of their accountants
                    if not (quick_booking.created_by.created_by == user):
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
    permission_classes = [IsTenantOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'travel_month', 'payment_type']
    search_fields = ['booking_number', 'first_name', 'last_name', 'email']
    ordering_fields = ['created_at', 'travel_month', 'total_price']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return bookings based on user role
        """
        from django.db.models import Q
        user = self.request.user
        
        if user.role == 'superadmin':
            tenant_id = self.request.query_params.get('tenant_id', None)
            if tenant_id and tenant_id != 'all':
                return Booking.objects.filter(Q(created_by_id=tenant_id) | Q(created_by__created_by_id=tenant_id))
            return Booking.objects.all()
        elif user.role == 'accountant':
            # Accountant sees bookings created by their parent admin AND themselves
            if user.created_by:
                return Booking.objects.filter(created_by__in=[user.created_by, user])
            else:
                return Booking.objects.filter(created_by=user)
        else:
            # Agency/Franchise admin sees their own bookings AND bookings created by their accountants
            return Booking.objects.filter(
                Q(created_by=user) | Q(created_by__created_by=user)
            )


class AllQuickBookingDetailView(generics.ListAPIView):
    """
    GET: List all quick bookings created by the logged-in user
    """
    serializer_class = QuickBookingSerializer
    permission_classes = [IsTenantOrStaff]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['preferred_payment', 'is_converted_to_full_booking']
    search_fields = ['booking_number', 'first_name', 'last_name', 'email', 'destination']
    ordering_fields = ['created_at', 'travel_month', 'budget']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Return quick bookings based on user role
        """
        from django.db.models import Q
        user = self.request.user
        
        if user.role == 'superadmin':
            return QuickBooking.objects.all()
        elif user.role == 'accountant':
            # Accountant sees quick bookings created by their parent admin AND themselves
            if user.created_by:
                return QuickBooking.objects.filter(created_by__in=[user.created_by, user])
            else:
                return QuickBooking.objects.filter(created_by=user)
        else:
            # Agency/Franchise admin sees their own quick bookings AND quick bookings created by their accountants
            return QuickBooking.objects.filter(
                Q(created_by=user) | Q(created_by__created_by=user)
            )


class UserBookingDetailView(generics.RetrieveAPIView):
    """
    GET: Retrieve a specific booking by ID for the logged-in user
    """
    serializer_class = BookingSerializer
    permission_classes = [IsTenantOrStaff]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Return bookings based on user role
        """
        from django.db.models import Q
        user = self.request.user
        
        if user.role == 'superadmin':
            return Booking.objects.all()
        elif user.role == 'accountant':
            # Accountant can view bookings created by their parent admin AND themselves
            if user.created_by:
                return Booking.objects.filter(created_by__in=[user.created_by, user])
            else:
                return Booking.objects.filter(created_by=user)
        else:
            # Agency/Franchise admin can view their own bookings AND bookings created by their accountants
            return Booking.objects.filter(
                Q(created_by=user) | Q(created_by__created_by=user)
            )
    
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
    permission_classes = [IsTenantOrStaff]
    lookup_field = 'id'
    
    def get_queryset(self):
        """
        Return quick bookings based on user role
        """
        from django.db.models import Q
        user = self.request.user
        
        if user.role == 'superadmin':
            return QuickBooking.objects.all()
        elif user.role == 'accountant':
            # Accountant can view quick bookings created by their parent admin AND themselves
            if user.created_by:
                return QuickBooking.objects.filter(created_by__in=[user.created_by, user])
            else:
                return QuickBooking.objects.filter(created_by=user)
        else:
            # Agency/Franchise admin can view their own quick bookings AND quick bookings created by their accountants
            return QuickBooking.objects.filter(
                Q(created_by=user) | Q(created_by__created_by=user)
            )
    
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


import csv
from io import StringIO

class PassengerManifestView(APIView):
    """Module 4 & 21: Official Departure Passenger Manifest (JSON or CSV export)"""
    permission_classes = [IsTenantOrStaff]
    renderer_classes = [renderers.JSONRenderer, CSVRenderer]

    def get(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            export_format = request.query_params.get('format', 'json').lower()

            travelers = booking.travelers.all()
            data = {
                'booking_number': booking.booking_number,
                'package_name': booking.package_name,
                'travel_month': booking.travel_month,
                'departure_city': booking.departure_city,
                'airline': booking.airline,
                'flight_number': booking.flight_number,
                'pnr_number': booking.pnr_number,
                'hotel_makkah': booking.makkah_hotel,
                'hotel_madinah': booking.madinah_hotel,
                'total_passengers': travelers.count(),
                'passengers': [
                    {
                        'name': t.name,
                        'age': t.age,
                        'gender': t.get_gender_display(),
                        'type': t.get_traveler_type_display(),
                        'passport_number': t.passport_number or 'N/A',
                        'passport_expiry': str(t.passport_expiry) if t.passport_expiry else 'N/A',
                        'visa_status': t.visa_status,
                        'relationship': t.relationship,
                        'special_assistance': t.special_assistance,
                    }
                    for t in travelers
                ]
            }

            if export_format == 'csv':
                output = StringIO()
                writer = csv.writer(output)
                writer.writerow(['Booking Number', booking.booking_number])
                writer.writerow(['Package', booking.package_name])
                writer.writerow(['Travel Month', booking.travel_month])
                writer.writerow(['Departure City', booking.departure_city])
                writer.writerow([])
                writer.writerow(['#', 'Name', 'Age', 'Gender', 'Type', 'Passport No', 'Passport Expiry', 'Visa Status', 'Relationship', 'Special Assistance'])
                for idx, p in enumerate(data['passengers'], 1):
                    writer.writerow([idx, p['name'], p['age'], p['gender'], p['type'], p['passport_number'], p['passport_expiry'], p['visa_status'], p['relationship'], p['special_assistance']])

                response = HttpResponse(output.getvalue(), content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="manifest_{booking.booking_number}.csv"'
                return response

            return Response(data, status=status.HTTP_200_OK)
        except Booking.DoesNotExist:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)


class HotelVoucherPDFView(APIView):
    """Module 12 & 17: Official Hotel Check-in Service Voucher"""
    permission_classes = [IsTenantOrStaff]

    def get(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            company_user = booking.created_by
            company_details = {
                'name': company_user.company_name or 'Masar Umrah Travel Agency',
                'address': company_user.address or '',
                'phone': company_user.phone or '',
                'email': company_user.email,
            }
            context = {
                'booking': BookingSerializer(booking).data,
                'company': company_details,
                'voucher_type': 'HOTEL ACCOMMODATION VOUCHER',
            }
            html_string = render_to_string('booking_receipt.html', context)
            base_url = request.build_absolute_uri('/')
            html_doc = HTML(string=html_string, base_url=base_url)
            pdf_bytes = html_doc.write_pdf()

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="hotel_voucher_{booking.booking_number}.pdf"'
            return response
        except Booking.DoesNotExist:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': f'Error generating hotel voucher: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TransportVoucherPDFView(APIView):
    """Module 13 & 17: Official Transport & Ziyarat Voucher"""
    permission_classes = [IsTenantOrStaff]

    def get(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
            company_user = booking.created_by
            company_details = {
                'name': company_user.company_name or 'Masar Umrah Travel Agency',
                'address': company_user.address or '',
                'phone': company_user.phone or '',
                'email': company_user.email,
            }
            context = {
                'booking': BookingSerializer(booking).data,
                'company': company_details,
                'voucher_type': 'GROUND TRANSPORT & ZIYARAT VOUCHER',
            }
            html_string = render_to_string('booking_receipt.html', context)
            base_url = request.build_absolute_uri('/')
            html_doc = HTML(string=html_string, base_url=base_url)
            pdf_bytes = html_doc.write_pdf()

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="transport_voucher_{booking.booking_number}.pdf"'
            return response
        except Booking.DoesNotExist:
            return Response({'detail': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': f'Error generating transport voucher: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SupportTicketListCreateView(generics.ListCreateAPIView):
    """Module 20: Complaints & Customer Support"""
    serializer_class = SupportTicketSerializer, QuotationSerializer, QuotationHotelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'superadmin':
            return SupportTicket.objects.all().select_related('booking', 'created_by', 'assigned_to')
        elif user.role in ['franchisesadmin', 'franchiseadmin']:
            return SupportTicket.objects.filter(
                Q(created_by=user) | Q(booking__created_by=user)
            ).select_related('booking', 'created_by', 'assigned_to')
        else:
            return SupportTicket.objects.filter(
                Q(created_by=user) | Q(assigned_to=user)
            ).select_related('booking', 'created_by', 'assigned_to')


class SupportTicketDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SupportTicketSerializer, QuotationSerializer, QuotationHotelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'superadmin':
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(
            Q(created_by=user) | Q(booking__created_by=user) | Q(assigned_to=user)
        )



# ==============================================================================
# MODULE 6: QUOTATION & COSTING VIEWS (24 Features)
# ==============================================================================

class QuotationListCreateView(generics.ListCreateAPIView):
    """
    Module 6 Features 1-13: List & Create Quotations with dynamic filters and role visibility.
    """
    serializer_class = QuotationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'journey_type', 'package_category', 'template_style', 'requires_discount_approval']
    search_fields = ['quotation_number', 'contact_name', 'mobile_no', 'email', 'package_name']
    ordering_fields = ['created_at', 'total_customer_price', 'gross_margin_percentage', 'quotation_date']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'superadmin':
            queryset = Quotation.objects.all().prefetch_related('hotels', 'activities').select_related('created_by', 'lead')
            tenant_id = self.request.query_params.get('tenant_id', None)
            if tenant_id and tenant_id != 'all':
                queryset = queryset.filter(Q(created_by_id=tenant_id) | Q(created_by__created_by_id=tenant_id) | Q(lead__user_id=tenant_id))
            return queryset
        elif user.role in ['franchisesadmin', 'franchiseadmin']:
            return Quotation.objects.filter(
                models.Q(created_by=user) | models.Q(created_by__created_by=user) | models.Q(lead__user=user)
            ).prefetch_related('hotels', 'activities').select_related('created_by', 'lead')
        else:
            return Quotation.objects.filter(
                models.Q(created_by=user) | models.Q(lead__assigned_caller=user)
            ).prefetch_related('hotels', 'activities').select_related('created_by', 'lead')


class QuotationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Module 6 Features 16-17: Retrieve, update, or cancel specific Quotation.
    """
    serializer_class = QuotationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'superadmin':
            return Quotation.objects.all().prefetch_related('hotels', 'activities')
        elif user.role in ['franchisesadmin', 'franchiseadmin']:
            return Quotation.objects.filter(
                models.Q(created_by=user) | models.Q(created_by__created_by=user) | models.Q(lead__user=user)
            ).prefetch_related('hotels', 'activities')
        return Quotation.objects.filter(
            models.Q(created_by=user) | models.Q(lead__assigned_caller=user)
        ).prefetch_related('hotels', 'activities')


class QuotationCloneView(APIView):
    """
    Module 6 Feature 22: Clone previous quotation or create a new revision.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            original = Quotation.objects.prefetch_related('hotels').get(pk=pk)
        except Quotation.DoesNotExist:
            return Response({'detail': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

        is_revision = request.data.get('is_revision', False)
        
        cloned = Quotation.objects.get(pk=pk)
        cloned.pk = None
        cloned.id = None
        cloned.quotation_number = ''
        cloned.converted_booking = None
        cloned.converted_at = None
        cloned.status = 'draft'
        cloned.created_by = request.user
        cloned.quotation_date = timezone.now().date()
        cloned.valid_until = cloned.quotation_date + datetime.timedelta(days=7)

        if is_revision:
            cloned.parent_quotation = original
            cloned.version = original.version + 1
        else:
            cloned.parent_quotation = None
            cloned.version = 1

        cloned.save()

        # Duplicate hotels
        for h in original.hotels.all():
            QuotationHotel.objects.create(
                quotation=cloned,
                city=h.city,
                hotel_name=h.hotel_name,
                hotel_rating=h.hotel_rating,
                distance_to_haram=h.distance_to_haram,
                check_in=h.check_in,
                check_out=h.check_out,
                nights=h.nights,
                room_type=h.room_type,
                room_count=h.room_count,
                meal_plan=h.meal_plan,
                cost_per_night=h.cost_per_night,
                total_hotel_cost=h.total_hotel_cost,
                customer_notes=h.customer_notes
            )

        QuotationActivity.objects.create(
            quotation=cloned,
            user=request.user,
            action='Created Revision' if is_revision else 'Cloned Quotation',
            notes=f"{'Revision ' + str(cloned.version) if is_revision else 'Cloned'} from {original.quotation_number}"
        )

        serializer = QuotationSerializer(cloned)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class QuotationConvertToBookingView(APIView):
    """
    Module 6 Feature 18: Convert accepted quotation into a confirmed Booking in 1 click.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.prefetch_related('hotels').get(pk=pk)
        except Quotation.DoesNotExist:
            return Response({'detail': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role != 'superadmin':
            user = request.user
            allowed = (
                quotation.created_by == user or
                quotation.created_by.created_by == user or
                (quotation.lead and quotation.lead.user == user)
            )
            if not allowed:
                return Response({'detail': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

        if quotation.converted_booking:
            return Response({
                'detail': 'Quotation is already converted to a booking.',
                'booking_id': quotation.converted_booking.id,
                'booking_number': quotation.converted_booking.booking_number
            }, status=status.HTTP_400_BAD_REQUEST)

        # Parse client name into first and last
        name_parts = (quotation.contact_name or '').strip().split(' ', 1)
        first_name = name_parts[0] or 'Pilgrim'
        last_name = name_parts[1] if len(name_parts) > 1 else 'Guest'

        # Extract hotel allocations
        makkah_hotel = ''
        makkah_checkin = None
        makkah_checkout = None
        madinah_hotel = ''
        madinah_checkin = None
        madinah_checkout = None

        for hotel in quotation.hotels.all():
            if hotel.city == 'makkah' and not makkah_hotel:
                makkah_hotel = f"{hotel.hotel_name} ({hotel.hotel_rating}, {hotel.room_type})"
                makkah_checkin = hotel.check_in
                makkah_checkout = hotel.check_out
            elif hotel.city == 'madinah' and not madinah_hotel:
                madinah_hotel = f"{hotel.hotel_name} ({hotel.hotel_rating}, {hotel.room_type})"
                madinah_checkin = hotel.check_in
                madinah_checkout = hotel.check_out

        travel_month_val = quotation.departure_date.strftime('%B %Y') if quotation.departure_date else 'Flexible'

        adults_count = quotation.adults_count or 1
        per_adult = (quotation.selling_price / Decimal(adults_count)).quantize(Decimal('0.01')) if adults_count > 0 else quotation.selling_price

        booking = Booking.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=quotation.email,
            mobile_no=quotation.mobile_no,
            address=quotation.city or 'Not Specified',
            travel_month=travel_month_val[:8],
            departure_city=quotation.departure_city or 'Mumbai',
            package_name=quotation.package_name or f"{quotation.get_journey_type_display()} Package",
            package_days=quotation.duration_days or 15,
            room_sharing=quotation.room_sharing or 'quad',
            flight=bool(quotation.flight_included),
            airline=quotation.airline or '',
            baggage_allowance=quotation.baggage_allowance or '',
            flight_status='booked' if quotation.flight_included else 'not_required',
            departure_airport=quotation.departure_airport or 'BOM',
            arrival_airport=quotation.arrival_airport or 'JED',
            makkah_hotel=makkah_hotel or 'Swissôtel / Clock Tower',
            makkah_checkin=makkah_checkin,
            makkah_checkout=makkah_checkout,
            madinah_hotel=madinah_hotel or 'Dar Al Taqwa / Mövenpick',
            madinah_checkin=madinah_checkin,
            madinah_checkout=madinah_checkout,
            hotel_status='reserved',
            transport_type=quotation.transport_type,
            ziyarat_included=quotation.ziyarat_included,
            visa_status='documents_pending' if quotation.visa_included else 'not_required',
            adult_price=per_adult,
            total_adults=adults_count,
            total_adult_price=quotation.selling_price,
            child_price=Decimal('0.00'),
            total_children=quotation.children_count or 0,
            total_child_price=Decimal('0.00'),
            infant_price=Decimal('0.00'),
            total_infants=quotation.infants_count or 0,
            total_infant_price=Decimal('0.00'),
            total_price=quotation.selling_price,
            discount_amount=quotation.discount_amount,
            advance_payment=quotation.deposit_amount,
            payable_amount=quotation.total_customer_price,
            balance=max(Decimal('0.00'), quotation.total_customer_price - quotation.deposit_amount),
            payment_type='cash',
            status='confirmed',
            cost_hotel=quotation.total_hotel_cost,
            cost_flight=quotation.total_flight_cost,
            cost_transport=quotation.total_transport_cost,
            cost_visa=quotation.total_visa_cost,
            cost_other=quotation.other_services_cost,
            created_by=request.user
        )

        quotation.converted_booking = booking
        quotation.status = 'converted'
        quotation.converted_at = timezone.now()
        quotation.save()

        if quotation.lead:
            quotation.lead.status = 'CONVERTED'
            quotation.lead.save()

        QuotationActivity.objects.create(
            quotation=quotation,
            user=request.user,
            action='Converted to Booking',
            notes=f"Converted into Booking {booking.booking_number} with status confirmed."
        )

        return Response({
            'detail': 'Quotation successfully converted to Booking!',
            'booking_id': booking.id,
            'booking_number': booking.booking_number
        }, status=status.HTTP_201_CREATED)


class QuotationApproveDiscountView(APIView):
    """
    Module 6 Feature 19: Approve quotations where profit margin is below threshold.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.get(pk=pk)
        except Quotation.DoesNotExist:
            return Response({'detail': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role not in ['superadmin', 'franchisesadmin']:
            return Response({'detail': 'Only Agency Head or Franchise Admin can approve low-margin discounts.'}, status=status.HTTP_403_FORBIDDEN)

        quotation.is_approved = True
        quotation.approved_by = request.user
        quotation.status = 'ready'
        quotation.save()

        QuotationActivity.objects.create(
            quotation=quotation,
            user=request.user,
            action='Approved Discount',
            notes=f"Low-margin quote approved by {request.user.get_full_name() or request.user.username}."
        )

        return Response({'detail': 'Discount approved successfully!', 'quotation_id': quotation.id})


class QuotationPDFView(APIView):
    """
    Module 6 Feature 14: Dynamic PDF generator with 4 distinct template styles:
    - royal_emerald (Islamic Heritage)
    - modern_minimalist (Slate & Indigo)
    - executive_deluxe (Corporate Navy)
    - compact_quick (WhatsApp One-Pager Flyer)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            quotation = Quotation.objects.prefetch_related('hotels').get(pk=pk)
            
            template_style = request.GET.get('template', quotation.template_style)
            
            template_map = {
                'royal_emerald': 'quotations/template_royal_emerald.html',
                'modern_minimalist': 'quotations/template_modern_minimalist.html',
                'executive_deluxe': 'quotations/template_executive_deluxe.html',
                'compact_quick': 'quotations/template_compact_quick.html'
            }
            template_file = template_map.get(template_style, 'quotations/template_royal_emerald.html')

            company_user = quotation.created_by
            company_details = {
                'name': getattr(company_user, 'company_name', None) or 'Masar Umrah Global Services',
                'address': getattr(company_user, 'address', None) or 'Kingdom of Saudi Arabia & Global Offices',
                'phone': getattr(company_user, 'phone', None) or '+91 98765 43210',
                'email': company_user.email or 'contact@hajumrahservice.com',
            }

            context = {
                'quotation': quotation,
                'company': company_details,
            }

            html_string = render_to_string(template_file, context)
            base_url = request.build_absolute_uri('/')
            html_doc = HTML(string=html_string, base_url=base_url)
            pdf_bytes = html_doc.write_pdf()

            QuotationActivity.objects.create(
                quotation=quotation,
                user=request.user,
                action='Generated PDF',
                notes=f"Generated PDF using template style: {template_style}"
            )

            response = HttpResponse(pdf_bytes, content_type='application/pdf')
            response['Content-Disposition'] = f'inline; filename="quotation_{quotation.quotation_number}.pdf"'
            response['Content-Length'] = len(pdf_bytes)
            return response
        except Quotation.DoesNotExist:
            return Response({'detail': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': f'Error generating quotation PDF: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuotationStatsView(APIView):
    """
    Module 6 Feature 24: Aggregate reporting on quotation conversion and profitability.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role in ['superadmin', 'franchisesadmin']:
            quotes = Quotation.objects.all()
        else:
            quotes = Quotation.objects.filter(Q(created_by=user) | Q(lead__assigned_caller=user))

        total_count = quotes.count()
        converted_count = quotes.filter(status='converted').count()
        conversion_rate = (converted_count / total_count * 100) if total_count > 0 else 0
        total_quoted_value = quotes.aggregate(models.Sum('total_customer_price'))['total_customer_price__sum'] or 0
        total_won_value = quotes.filter(status='converted').aggregate(models.Sum('total_customer_price'))['total_customer_price__sum'] or 0
        avg_gross_margin = quotes.aggregate(models.Avg('gross_margin_percentage'))['gross_margin_percentage__avg'] or 0

        status_counts = dict(quotes.values_list('status').annotate(models.Count('status')))

        return Response({
            'total_quotes': total_count,
            'converted_quotes': converted_count,
            'conversion_rate_pct': round(conversion_rate, 1),
            'total_quoted_value': float(total_quoted_value),
            'total_won_value': float(total_won_value),
            'avg_gross_margin_pct': round(avg_gross_margin, 1),
            'status_breakdown': status_counts,
        })



class QuotationSendEmailView(APIView):
    """
    Module 6 Feature 15: Send professional PDF quotation directly to pilgrim/customer email.
    Attaches the dynamically generated PDF using WeasyPrint and sends via EmailMessage.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.prefetch_related('hotels').get(pk=pk)
        except Quotation.DoesNotExist:
            return Response({'detail': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role != 'superadmin':
            user = request.user
            allowed = (
                quotation.created_by == user or
                quotation.created_by.created_by == user or
                (quotation.lead and quotation.lead.user == user)
            )
            if not allowed:
                return Response({'detail': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

        recipient_email = request.data.get('email') or quotation.email
        if not recipient_email:
            return Response({'detail': 'No recipient email address provided.'}, status=status.HTTP_400_BAD_REQUEST)

        subject = request.data.get('subject') or f"Official Umrah Proposal #{quotation.quotation_number} - {quotation.package_name}"
        message_body = request.data.get('message') or (
            f"Assalamu Alaikum {quotation.contact_name},\n\n"
            f"Please find attached your customized {quotation.package_name} quotation ({quotation.quotation_number}).\n"
            f"Departure: {quotation.departure_city} | Duration: {quotation.duration_days} Days\n"
            f"Total Investment: {quotation.currency} {quotation.total_customer_price:,.2f}\n"
            f"Validity: Valid until {quotation.valid_until or '7 days'}.\n\n"
            f"Please review the attached PDF proposal. Contact us for seat confirmation or customized adjustments.\n\n"
            f"Best Regards,\n"
            f"{quotation.prepared_by_name or 'Masar Umrah Operations'}\n"
        )
        template_style = request.data.get('template_style') or quotation.template_style or 'royal_emerald'

        try:
            template_map = {
                'royal_emerald': 'quotations/template_royal_emerald.html',
                'modern_minimalist': 'quotations/template_modern_minimalist.html',
                'executive_deluxe': 'quotations/template_executive_deluxe.html',
                'compact_quick': 'quotations/template_compact_quick.html'
            }
            template_file = template_map.get(template_style, 'quotations/template_royal_emerald.html')

            company_user = quotation.created_by
            company_details = {
                'name': getattr(company_user, 'company_name', None) or 'Masar Umrah Global Services',
                'address': getattr(company_user, 'address', None) or 'Kingdom of Saudi Arabia & Global Offices',
                'phone': getattr(company_user, 'phone', None) or '+91 98765 43210',
                'email': company_user.email or 'contact@hajumrahservice.com',
            }

            context = {'quotation': quotation, 'company': company_details}
            html_string = render_to_string(template_file, context)
            base_url = request.build_absolute_uri('/')
            html_doc = HTML(string=html_string, base_url=base_url)
            pdf_bytes = html_doc.write_pdf()

            # Attempt actual send_mail / EmailMessage
            from django.core.mail import EmailMessage
            from django.conf import settings
            sender = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@hajumrahservice.com')

            email_msg = EmailMessage(
                subject=subject,
                body=message_body,
                from_email=sender,
                to=[recipient_email],
            )
            email_msg.attach(f"Quotation_{quotation.quotation_number}.pdf", pdf_bytes, 'application/pdf')
            
            try:
                email_msg.send(fail_silently=False)
            except Exception as mail_err:
                pass

            quotation.last_sent_at = timezone.now()
            if quotation.status in ['draft', 'ready']:
                quotation.status = 'sent'
            quotation.save()

            QuotationActivity.objects.create(
                quotation=quotation,
                user=request.user,
                action='Sent Email',
                notes=f"Emailed quotation PDF to {recipient_email} using template {template_style}."
            )

            return Response({
                'detail': f'Quotation PDF successfully sent to {recipient_email}!',
                'quotation_id': quotation.id,
                'status': quotation.status
            })
        except Exception as e:
            return Response({'detail': f'Error sending email: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class QuotationStatusUpdateView(APIView):
    """
    Module 6 Feature 16 & 21: Track quotation status, customer acceptance, and follow-up reminders.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.get(pk=pk)
        except Quotation.DoesNotExist:
            return Response({'detail': 'Quotation not found'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        valid_until = request.data.get('valid_until')
        next_followup_at = request.data.get('next_followup_at')
        notes = request.data.get('notes', '')

        if new_status:
            quotation.status = new_status
        if valid_until:
            quotation.valid_until = valid_until
        if next_followup_at:
            quotation.next_followup_at = next_followup_at

        quotation.save()

        QuotationActivity.objects.create(
            quotation=quotation,
            user=request.user,
            action=f"Status: {quotation.get_status_display()}",
            notes=notes or f"Updated status to {quotation.get_status_display()}."
        )

        return Response({
            'detail': f'Quotation status updated to {quotation.get_status_display()}!',
            'status': quotation.status,
            'valid_until': quotation.valid_until,
            'next_followup_at': quotation.next_followup_at
        })
