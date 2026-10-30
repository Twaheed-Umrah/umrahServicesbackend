import datetime
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from apps.crm.models import Lead
from .models import (
    Booking, BookingTraveler, Quotation, QuotationHotel, QuotationActivity
)

User = get_user_model()

class QuotationAndBookingEngineTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. SuperAdmin
        self.superadmin = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@masarumrah.com',
            password='Password123!',
            role='superadmin'
        )

        # 2. Tenant 1 Admin
        self.tenant1 = User.objects.create_user(
            username='tenant1_admin',
            email='tenant1@agency.com',
            password='Password123!',
            role='franchisesadmin',
            company_name='Al-Safwah Umrah Travels',
            phone='+919999900010'
        )

        # 3. Tenant 1 Caller
        self.caller1 = User.objects.create_user(
            username='caller_t1',
            email='caller1@agency.com',
            password='Password123!',
            role='caller',
            created_by=self.tenant1,
            is_present=True
        )

        # 4. Tenant 2 Admin (Isolated)
        self.tenant2 = User.objects.create_user(
            username='tenant2_admin',
            email='tenant2@agency.com',
            password='Password123!',
            role='franchisesadmin',
            company_name='Noor Al-Haram Tours',
            phone='+919999900020'
        )

        # Lead for Tenant 1
        self.lead1 = Lead.objects.create(
            user=self.tenant1,
            assigned_caller=self.caller1,
            name='Haji Abdul Rahman',
            mobile_number='+919876543300',
            email='abdulrahman@example.com',
            city='Mumbai',
            status='NEW'
        )

        # Sample Quotation for Tenant 1
        self.quotation1 = Quotation.objects.create(
            created_by=self.tenant1,
            lead=self.lead1,
            contact_name='Haji Abdul Rahman',
            mobile_no='+919876543300',
            email='abdulrahman@example.com',
            city='Mumbai',
            journey_type='umrah',
            package_name='15-Day Premium Umrah Package',
            package_category='premium',
            departure_city='Mumbai',
            duration_days=15,
            adults_count=2,
            children_count=0,
            infants_count=0,
            flight_included=True,
            flight_cost_per_pax=Decimal('35000.00'),
            total_flight_cost=Decimal('70000.00'),
            transport_included=True,
            total_transport_cost=Decimal('15000.00'),
            visa_included=True,
            visa_cost_per_pax=Decimal('12000.00'),
            total_visa_cost=Decimal('24000.00'),
            total_hotel_cost=Decimal('20000.00'),
            pricing_method='markup',
            markup_percentage=Decimal('15.00'),
            tax_percentage=Decimal('5.00')
        )

        # Hotel for Quotation 1
        self.hotel1 = QuotationHotel.objects.create(
            quotation=self.quotation1,
            city='makkah',
            hotel_name='Swissôtel Al Maqam',
            hotel_rating='5 Star',
            nights=7,
            room_count=1,
            occupancy=2,
            cost_per_night=Decimal('5000.00'),
            total_hotel_cost=Decimal('35000.00')
        )

    # ----------------- POSITIVE TESTS -----------------

    def test_quotation_creation_and_auto_numbering(self):
        """
        Positive: Creating a quotation calculates costs, markup, tax, and auto-generates number QT-YYYYMM-XXXX.
        """
        self.client.force_authenticate(user=self.tenant1)
        payload = {
            'contact_name': 'Zaid Farooqui',
            'mobile_no': '+919876500099',
            'email': 'zaid@example.com',
            'city': 'Delhi',
            'journey_type': 'umrah',
            'package_name': 'Ramadan Special Economy',
            'departure_city': 'Delhi',
            'duration_days': 14,
            'adults_count': 2,
            'children_count': 0,
            'infants_count': 0,
            'flight_included': True,
            'flight_cost_per_pax': '30000.00',
            'transport_included': True,
            'total_transport_cost': '10000.00',
            'visa_included': True,
            'visa_cost_per_pax': '12000.00',
            'pricing_method': 'markup',
            'markup_percentage': '15.00',
            'tax_percentage': '5.00',
            'hotels': [
                {
                    'city': 'makkah',
                    'hotel_name': 'Anjum Hotel Makkah',
                    'hotel_rating': '5 Star',
                    'nights': 7,
                    'room_count': 1,
                    'occupancy': 2,
                    'cost_per_night': '4000.00'
                }
            ]
        }
        res = self.client.post('/api/bookings/quotations/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.data
        self.assertTrue(data['quotation_number'].startswith('QT-'))
        self.assertEqual(data['version'], 1)
        self.assertEqual(data['status'], 'draft')
        
        # Verify supplier cost:
        # Hotel: 7 * 1 * 4000 = 28000
        # Flight: 2 * 30000 = 60000
        # Transport: 10000
        # Visa: 2 * 12000 = 24000
        # Total Supplier = 122000.00
        self.assertEqual(Decimal(str(data['total_supplier_cost'])), Decimal('122000.00'))
        
        # Markup 15%: 122000 * 1.15 = 140300.00
        self.assertEqual(Decimal(str(data['selling_price'])), Decimal('140300.00'))
        
        # Tax 5%: 140300 * 0.05 = 7015.00 -> Total = 147315.00
        self.assertEqual(Decimal(str(data['tax_amount'])), Decimal('7015.00'))
        self.assertEqual(Decimal(str(data['total_customer_price'])), Decimal('147315.00'))

    def test_quotation_target_margin_pricing(self):
        """
        Positive: Pricing method 'target_margin' calculates selling price = cost / (1 - margin).
        """
        self.client.force_authenticate(user=self.tenant1)
        payload = {
            'contact_name': 'Khadija Begum',
            'mobile_no': '+919876500088',
            'journey_type': 'umrah',
            'package_name': 'VIP Executive Package',
            'adults_count': 1,
            'total_flight_cost': '30000.00',
            'total_transport_cost': '20000.00',
            'pricing_method': 'target_margin',
            'target_margin_percentage': '20.00',
            'tax_percentage': '0.00',
            'hotels': [
                {
                    'city': 'makkah',
                    'hotel_name': 'Fairmont Makkah Clock Royal Tower',
                    'hotel_rating': '5 Star',
                    'nights': 5,
                    'room_count': 1,
                    'occupancy': 1,
                    'cost_per_night': '10000.00'
                }
            ]
        }
        res = self.client.post('/api/bookings/quotations/', payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Total supplier = 50,000 (hotel) + 30,000 (flight) + 20,000 (transport) = 100,000.
        # Selling price at 20% margin = 100,000 / (1 - 0.20) = 125,000.00
        self.assertEqual(Decimal(str(res.data['selling_price'])), Decimal('125000.00'))
        self.assertEqual(Decimal(str(res.data['gross_margin_percentage'])), Decimal('20.00'))

    def test_quotation_discount_requires_approval_if_under_8_percent(self):
        """
        Positive: Applying a discount that drops gross margin below 8% sets requires_discount_approval = True.
        """
        self.client.force_authenticate(user=self.tenant1)
        # In quotation1: supplier cost = 129,000 (after hotel recalculation).
        # Selling price = 129000 * 1.15 = 148350.
        # If discount is 12,000 -> discounted price = 136350 -> profit = 7350 -> margin = 7350/136350 = 5.39% (< 8%).
        patch_res = self.client.patch(
            f'/api/bookings/quotations/{self.quotation1.id}/',
            {'discount_amount': '12000.00', 'discount_reason': 'Special customer loyalty concession'},
            format='json'
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertTrue(patch_res.data['requires_discount_approval'])

    def test_quotation_approve_discount_by_admin(self):
        """
        Positive: Agency Admin can approve low-margin quotation, transitioning status to 'ready'.
        """
        self.quotation1.discount_amount = Decimal('12000.00')
        self.quotation1.requires_discount_approval = True
        self.quotation1.save()

        self.client.force_authenticate(user=self.tenant1)
        res = self.client.post(f'/api/bookings/quotations/{self.quotation1.id}/approve-discount/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.quotation1.refresh_from_db()
        self.assertTrue(self.quotation1.is_approved)
        self.assertEqual(self.quotation1.status, 'ready')
        self.assertEqual(self.quotation1.approved_by, self.tenant1)

    def test_quotation_clone_and_revision_versioning(self):
        """
        Positive:
        - Cloning creates a new independent quotation (version 1).
        - Creating a revision increments version (version 2) and references parent.
        """
        self.client.force_authenticate(user=self.tenant1)

        # 1. Clone (independent duplicate)
        clone_res = self.client.post(
            f'/api/bookings/quotations/{self.quotation1.id}/clone/',
            {'is_revision': False},
            format='json'
        )
        self.assertEqual(clone_res.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(clone_res.data['id'], self.quotation1.id)
        self.assertNotEqual(clone_res.data['quotation_number'], self.quotation1.quotation_number)
        self.assertEqual(clone_res.data['version'], 1)
        self.assertIsNone(clone_res.data['parent_quotation'])

        # 2. Revision (increment version)
        rev_res = self.client.post(
            f'/api/bookings/quotations/{self.quotation1.id}/clone/',
            {'is_revision': True},
            format='json'
        )
        self.assertEqual(rev_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(rev_res.data['version'], 2)
        self.assertEqual(rev_res.data['parent_quotation'], self.quotation1.id)
        self.assertIn('-V2', rev_res.data['quotation_number'])

    def test_quotation_convert_to_booking(self):
        """
        Positive: Converting accepted quotation automatically creates confirmed Booking,
        sets Quotation status to 'converted', and updates Lead status to 'CONVERTED'.
        """
        self.client.force_authenticate(user=self.tenant1)
        res = self.client.post(f'/api/bookings/quotations/{self.quotation1.id}/convert/')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertIn('booking_id', res.data)
        booking_id = res.data['booking_id']

        # Verify Booking created
        booking = Booking.objects.get(id=booking_id)
        self.assertEqual(booking.first_name, 'Haji')
        self.assertEqual(booking.last_name, 'Abdul Rahman')
        self.assertEqual(booking.mobile_no, '+919876543300')
        self.assertEqual(booking.total_adults, 2)
        self.assertEqual(booking.status, 'confirmed')

        # Verify Quotation updated
        self.quotation1.refresh_from_db()
        self.assertEqual(self.quotation1.status, 'converted')
        self.assertEqual(self.quotation1.converted_booking, booking)

        # Verify Lead converted
        self.lead1.refresh_from_db()
        self.assertEqual(self.lead1.status, 'CONVERTED')

    def test_quotation_pdf_export_all_templates(self):
        """
        Positive: Dynamic PDF generation returns application/pdf for royal_emerald and compact_quick templates.
        """
        self.client.force_authenticate(user=self.tenant1)

        # 1. Royal Emerald Template
        res1 = self.client.get(f'/api/bookings/quotations/{self.quotation1.id}/pdf/?template=royal_emerald')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        self.assertEqual(res1.get('Content-Type'), 'application/pdf')
        self.assertGreater(len(res1.content), 1000)

        # 2. WhatsApp Flyer / Compact Quick Template
        res2 = self.client.get(f'/api/bookings/quotations/{self.quotation1.id}/pdf/?template=compact_quick')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        self.assertEqual(res2.get('Content-Type'), 'application/pdf')
        self.assertGreater(len(res2.content), 1000)

    def test_quotation_stats_reporting(self):
        """
        Positive: Quotation stats returns conversion rate and financial aggregates.
        """
        self.client.force_authenticate(user=self.tenant1)
        res = self.client.get('/api/bookings/quotations/stats/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('total_quotes', res.data)
        self.assertIn('converted_quotes', res.data)
        self.assertIn('conversion_rate_pct', res.data)
        self.assertIn('total_quoted_value', res.data)
        self.assertGreaterEqual(res.data['total_quotes'], 1)

    def test_booking_passenger_manifest_csv_download(self):
        """
        Positive: Booking passenger manifest endpoint returns downloadable CSV with traveler details.
        """
        self.client.force_authenticate(user=self.tenant1)
        booking = Booking.objects.create(
            first_name='Rashid',
            last_name='Khan',
            email='rashid@example.com',
            mobile_no='+919876543311',
            address='Mumbai',
            travel_month='November',
            departure_city='Mumbai',
            package_name='15-Day Umrah',
            package_days=15,
            room_sharing='double',
            adult_price=Decimal('50000.00'),
            total_adults=2,
            total_adult_price=Decimal('100000.00'),
            total_price=Decimal('100000.00'),
            payable_amount=Decimal('100000.00'),
            balance=Decimal('100000.00'),
            payment_type='cash',
            created_by=self.tenant1
        )
        BookingTraveler.objects.create(
            booking=booking,
            name='Rashid Khan',
            age=45,
            gender='M',
            traveler_type='adult',
            passport_number='A1234567'
        )
        BookingTraveler.objects.create(
            booking=booking,
            name='Naseem Khan',
            age=40,
            gender='F',
            traveler_type='adult',
            passport_number='B7654321'
        )

        res = self.client.get(f'/api/bookings/bookings/{booking.id}/manifest/?format=csv')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.get('Content-Type'), 'text/csv')
        csv_content = res.content.decode('utf-8')
        self.assertIn('Rashid Khan', csv_content)
        self.assertIn('A1234567', csv_content)
        self.assertIn('Naseem Khan', csv_content)

    def test_booking_hotel_and_transport_vouchers(self):
        """
        Positive: Hotel and transport vouchers can be generated as PDF documents.
        """
        self.client.force_authenticate(user=self.tenant1)
        booking = Booking.objects.create(
            first_name='Salim',
            last_name='Shaikh',
            email='salim@example.com',
            mobile_no='+919876543322',
            address='Delhi',
            travel_month='December',
            departure_city='Delhi',
            package_name='Deluxe Umrah',
            package_days=14,
            room_sharing='quad',
            adult_price=Decimal('60000.00'),
            total_adults=1,
            total_adult_price=Decimal('60000.00'),
            total_price=Decimal('60000.00'),
            payable_amount=Decimal('60000.00'),
            balance=Decimal('60000.00'),
            payment_type='cash',
            created_by=self.tenant1
        )

        # Hotel Voucher
        res_hotel = self.client.get(f'/api/bookings/bookings/{booking.id}/hotel-voucher/')
        self.assertEqual(res_hotel.status_code, status.HTTP_200_OK)
        self.assertEqual(res_hotel.get('Content-Type'), 'application/pdf')

        # Transport Voucher
        res_transport = self.client.get(f'/api/bookings/bookings/{booking.id}/transport-voucher/')
        self.assertEqual(res_transport.status_code, status.HTTP_200_OK)
        self.assertEqual(res_transport.get('Content-Type'), 'application/pdf')

    # ----------------- NEGATIVE TESTS -----------------

    def test_tenant_quotation_isolation(self):
        """
        Negative: Tenant 2 cannot access or convert Tenant 1's quotation.
        """
        self.client.force_authenticate(user=self.tenant2)
        
        # In list view, quotation1 does not appear in tenant2's results
        list_res = self.client.get('/api/bookings/quotations/')
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        results = list_res.data.get('results', list_res.data)
        ids = [q['id'] for q in results]
        self.assertNotIn(self.quotation1.id, ids)

        # Direct access to quotation 1 returns 404
        get_res = self.client.get(f'/api/bookings/quotations/{self.quotation1.id}/')
        self.assertEqual(get_res.status_code, status.HTTP_404_NOT_FOUND)

        # Convert attempt by Tenant 2 returns 404
        convert_res = self.client.post(f'/api/bookings/quotations/{self.quotation1.id}/convert/')
        self.assertEqual(convert_res.status_code, status.HTTP_404_NOT_FOUND)

    def test_caller_cannot_approve_discount(self):
        """
        Negative: A caller cannot approve a discount (HTTP 403 Forbidden).
        Only Agency Head / SuperAdmin has approval permission.
        """
        self.client.force_authenticate(user=self.caller1)
        res = self.client.post(f'/api/bookings/quotations/{self.quotation1.id}/approve-discount/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_cannot_convert_already_converted_quotation(self):
        """
        Negative: Attempting to convert an already converted quotation returns HTTP 400 Bad Request.
        """
        self.client.force_authenticate(user=self.tenant1)
        # Convert first time
        res1 = self.client.post(f'/api/bookings/quotations/{self.quotation1.id}/convert/')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # Attempt to convert second time
        res2 = self.client.post(f'/api/bookings/quotations/{self.quotation1.id}/convert/')
        self.assertEqual(res2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already converted', res2.data['detail'])

    def test_convert_nonexistent_quotation(self):
        """
        Negative: Converting a non-existent quotation returns HTTP 404 Not Found.
        """
        self.client.force_authenticate(user=self.tenant1)
        res = self.client.post('/api/bookings/quotations/999999/convert/')
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_quotation_access(self):
        """
        Negative: Unauthenticated requests return HTTP 401 Unauthorized.
        """
        res = self.client.get('/api/bookings/quotations/')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
