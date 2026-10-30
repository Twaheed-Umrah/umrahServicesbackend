import io
import csv
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Lead, LeadNote, Task

User = get_user_model()

class CRMAndLeadEngineTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. SuperAdmin
        self.superadmin = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@masarumrah.com',
            password='Password123!',
            role='superadmin'
        )

        # 2. Tenant 1
        self.tenant1 = User.objects.create_user(
            username='tenant1_admin',
            email='tenant1@agency.com',
            password='Password123!',
            role='franchisesadmin',
            phone='+919999900010'
        )

        # 3. Tenant 1 Callers: Caller A (Present) & Caller B (Absent)
        self.caller_a = User.objects.create_user(
            username='caller_a',
            email='callera@agency.com',
            password='Password123!',
            role='sells_caller',
            phone='+919999900011',
            created_by=self.tenant1,
            is_present=True
        )

        self.caller_b = User.objects.create_user(
            username='caller_b',
            email='callerb@agency.com',
            password='Password123!',
            role='sells_caller',
            phone='+919999900012',
            created_by=self.tenant1,
            is_present=False  # ABSENT! Must be skipped in Round-Robin
        )

        # 4. Tenant 2
        self.tenant2 = User.objects.create_user(
            username='tenant2_admin',
            email='tenant2@agency.com',
            password='Password123!',
            role='franchisesadmin',
            phone='+919999900013'
        )

        # Lead for Tenant 1
        self.lead1 = Lead.objects.create(
            user=self.tenant1,
            assigned_caller=self.caller_a,
            name='Mohammad Tariq',
            mobile_number='+919876543210',
            email='tariq@gmail.com',
            city='Mumbai',
            status='NEW'
        )

        # Lead for Tenant 2
        self.lead2 = Lead.objects.create(
            user=self.tenant2,
            name='Fatima Zahra',
            mobile_number='+919876543211',
            email='fatima@gmail.com',
            city='Hyderabad',
            status='NEW'
        )

    # ----------------- POSITIVE TESTS -----------------

    def test_create_lead_success(self):
        """Positive: Tenant can create a new lead with valid information"""
        self.client.force_authenticate(user=self.tenant1)
        payload = {
            'name': 'Ahmed Raza',
            'mobile_number': '+919876543220',
            'email': 'ahmed@gmail.com',
            'city': 'Delhi',
            'source': 'Website',
            'journey_type': 'Umrah',
            'pax_count': 3
        }
        response = self.client.post('/api/crm/leads/', payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Ahmed Raza')
        self.assertEqual(response.data['pax_count'], 3)

    def test_tenant_lead_isolation(self):
        """Positive: Tenant 1 sees only Tenant 1's leads; Tenant 2 sees only Tenant 2's leads"""
        # Tenant 1 check
        self.client.force_authenticate(user=self.tenant1)
        res1 = self.client.get('/api/crm/leads/')
        self.assertEqual(res1.status_code, status.HTTP_200_OK)
        results1 = res1.data.get('results', res1.data)
        lead_ids1 = [l['id'] for l in results1]
        self.assertIn(self.lead1.id, lead_ids1)
        self.assertNotIn(self.lead2.id, lead_ids1)

        # Tenant 2 check
        self.client.force_authenticate(user=self.tenant2)
        res2 = self.client.get('/api/crm/leads/')
        self.assertEqual(res2.status_code, status.HTTP_200_OK)
        results2 = res2.data.get('results', res2.data)
        lead_ids2 = [l['id'] for l in results2]
        self.assertIn(self.lead2.id, lead_ids2)
        self.assertNotIn(self.lead1.id, lead_ids2)

    def test_superadmin_tenant_lead_filtering(self):
        """Positive: SuperAdmin can view all leads or filter by ?tenant_id="""
        self.client.force_authenticate(user=self.superadmin)
        
        # Scoped to Tenant 1
        res = self.client.get(f'/api/crm/leads/?tenant_id={self.tenant1.id}')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data.get('results', res.data)
        lead_ids = [l['id'] for l in results]
        self.assertIn(self.lead1.id, lead_ids)
        self.assertNotIn(self.lead2.id, lead_ids)

    def test_update_lead_status_and_note(self):
        """Positive: Caller or Admin can update lead status and append note"""
        self.client.force_authenticate(user=self.caller_a)
        response = self.client.post(
            f'/api/crm/leads/{self.lead1.id}/update-status/',
            {
                'status': 'INTERESTED',
                'note': 'Customer requested 15-day Ramadan package quotation for 4 pax.'
            }
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lead1.refresh_from_db()
        self.assertEqual(self.lead1.status, 'INTERESTED')
        # Verify history note appended
        self.assertTrue(self.lead1.history_notes.filter(note__contains='Ramadan package').exists())

    def test_round_robin_distribution_skips_absent_callers(self):
        """
        Positive: Excel/Bulk upload distributes leads via Round-Robin ONLY to present callers.
        Caller A (is_present=True) must get all leads.
        Caller B (is_present=False) must get ZERO leads.
        """
        self.client.force_authenticate(user=self.tenant1)

        # Create a CSV in-memory with 3 leads
        csv_file = io.StringIO()
        writer = csv.writer(csv_file)
        writer.writerow(['name', 'mobile_number', 'city', 'email'])
        writer.writerow(['Lead One', '+919111111111', 'Lucknow', 'one@test.com'])
        writer.writerow(['Lead Two', '+919222222222', 'Kanpur', 'two@test.com'])
        writer.writerow(['Lead Three', '+919333333333', 'Agra', 'three@test.com'])
        csv_file.seek(0)

        uploaded = SimpleUploadedFile(
            'leads.csv',
            csv_file.getvalue().encode('utf-8'),
            content_type='text/csv'
        )

        response = self.client.post(
            '/api/crm/leads/upload-excel/',
            {'file': uploaded, 'campaign_name': 'Meta Ramadan 2026', 'source': 'Meta Ads'},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['present_callers_count'], 1)

        # Verify Caller A received the leads
        caller_a_leads = Lead.objects.filter(assigned_caller=self.caller_a, campaign_name='Meta Ramadan 2026')
        self.assertEqual(caller_a_leads.count(), 3)

        # Verify Caller B received 0 leads
        caller_b_leads = Lead.objects.filter(assigned_caller=self.caller_b, campaign_name='Meta Ramadan 2026')
        self.assertEqual(caller_b_leads.count(), 0)

    def test_recall_leads_to_pool_and_reassign(self):
        """Positive: Agency head can recall unworked leads to agency pool and reassign"""
        self.client.force_authenticate(user=self.tenant1)

        # Recall lead 1 to pool
        recall_res = self.client.post('/api/crm/leads/recall-to-pool/', {
            'caller_id': self.caller_a.id,
            'lead_ids': [self.lead1.id],
            'reason': 'Caller reassignment'
        })
        self.assertEqual(recall_res.status_code, status.HTTP_200_OK)
        self.lead1.refresh_from_db()
        self.assertTrue(self.lead1.is_in_agency_pool)
        self.assertIsNone(self.lead1.assigned_caller)

        # Reassign from pool to Caller A
        reassign_res = self.client.post('/api/crm/leads/reassign-from-pool/', {
            'lead_ids': [self.lead1.id],
            'target_caller_id': self.caller_a.id
        })
        self.assertEqual(reassign_res.status_code, status.HTTP_200_OK)
        self.lead1.refresh_from_db()
        self.assertFalse(self.lead1.is_in_agency_pool)
        self.assertEqual(self.lead1.assigned_caller, self.caller_a)

    def test_task_create_and_list(self):
        """Positive: Can create and list tasks for lead follow-ups"""
        from django.utils import timezone
        self.client.force_authenticate(user=self.tenant1)
        payload = {
            "related_lead": self.lead1.id,
            "task_type": "call",
            "priority": "high",
            "title": "Call pilgrim regarding passport copies",
            "assigned_to": self.caller_a.id,
            "due_date": (timezone.now() + timezone.timedelta(days=1)).isoformat()
        }
        res = self.client.post("/api/crm/tasks/", payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["title"], "Call pilgrim regarding passport copies")

    # ----------------- NEGATIVE TESTS -----------------

    def test_create_lead_missing_required_fields(self):
        """Negative: Missing mobile number returns 400 Bad Request"""
        self.client.force_authenticate(user=self.tenant1)
        response = self.client.post('/api/crm/leads/', {
            'name': 'Incomplete Lead'
            # Missing mobile_number
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tenant_cannot_read_or_edit_other_tenant_lead(self):
        """Negative: Tenant 2 cannot view or update Tenant 1's lead"""
        self.client.force_authenticate(user=self.tenant2)

        # GET request returns 404
        get_res = self.client.get(f'/api/crm/leads/{self.lead1.id}/')
        self.assertEqual(get_res.status_code, status.HTTP_404_NOT_FOUND)

        # UPDATE request returns 404
        update_res = self.client.post(
            f'/api/crm/leads/{self.lead1.id}/update-status/',
            {'status': 'LOST', 'note': 'Unauthorized hijack attempt'}
        )
        self.assertEqual(update_res.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_crm_access_denied(self):
        """Negative: Unauthenticated access returns 401 Unauthorized"""
        response = self.client.get('/api/crm/leads/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
