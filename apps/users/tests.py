from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class UserAuthAndTenantTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. SuperAdmin
        self.superadmin = User.objects.create_superuser(
            username='superadmin',
            email='superadmin@masarumrah.com',
            password='Password123!',
            role='superadmin',
            phone='+919999900001'
        )

        # 2. Tenant 1 (franchisesadmin)
        self.tenant1 = User.objects.create_user(
            username='tenant1_admin',
            email='tenant1@agency.com',
            password='Password123!',
            role='franchisesadmin',
            phone='+919999900002',
            company_name='Al-Haram Travels'
        )

        # 3. Tenant 1 Staff: Caller 1 & Operations
        self.caller1 = User.objects.create_user(
            username='caller1',
            email='caller1@agency.com',
            password='Password123!',
            role='sells_caller',
            phone='+919999900003',
            created_by=self.tenant1,
            is_present=True
        )

        self.ops1 = User.objects.create_user(
            username='ops1',
            email='ops1@agency.com',
            password='Password123!',
            role='operations',
            phone='+919999900004',
            created_by=self.tenant1
        )

        # 4. Tenant 2 (Different agency)
        self.tenant2 = User.objects.create_user(
            username='tenant2_admin',
            email='tenant2@agency.com',
            password='Password123!',
            role='franchisesadmin',
            phone='+919999900005',
            company_name='Noor Al-Madinah Tours'
        )

    # ----------------- POSITIVE TESTS -----------------

    def test_login_success(self):
        """Positive: Valid login returns access and refresh JWT tokens"""
        response = self.client.post('/api/auth/login/', {
            'email': 'tenant1@agency.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['role'], 'franchisesadmin')

    def test_token_verify_and_refresh(self):
        """Positive: Valid token can be verified and refreshed"""
        login_res = self.client.post('/api/auth/login/', {
            'email': 'tenant1@agency.com',
            'password': 'Password123!'
        })
        access = login_res.data['access']
        refresh = login_res.data['refresh']

        # Verify token
        verify_res = self.client.post('/api/auth/verify-token/', {'token': access})
        self.assertEqual(verify_res.status_code, status.HTTP_200_OK)

        # Refresh token
        refresh_res = self.client.post('/api/auth/refresh-token/', {'refresh': refresh})
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_res.data)

    def test_get_current_user_profile(self):
        """Positive: Authenticated user can fetch their profile"""
        self.client.force_authenticate(user=self.tenant1)
        response = self.client.get('/api/auth/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'tenant1@agency.com')
        self.assertEqual(response.data['company_name'], 'Al-Haram Travels')

    def test_superadmin_tenant_list(self):
        """Positive: SuperAdmin can view all SaaS tenants and aggregate metrics"""
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get('/api/auth/tenants/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tenants', response.data)
        self.assertGreaterEqual(len(response.data['tenants']), 2)
        # Check tenant staff breakdown
        tenant1_data = next((t for t in response.data['tenants'] if t['id'] == self.tenant1.id), None)
        self.assertIsNotNone(tenant1_data)
        self.assertEqual(tenant1_data['staff']['callers'], 1)
        self.assertEqual(tenant1_data['staff']['operations'], 1)

    def test_superadmin_tenant_detail(self):
        """Positive: SuperAdmin can fetch deep dive for a specific tenant"""
        self.client.force_authenticate(user=self.superadmin)
        response = self.client.get(f'/api/auth/tenants/{self.tenant1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['tenant']['company_name'], 'Al-Haram Travels')
        self.assertIn('staff', response.data)
        self.assertIn('leads', response.data)

    def test_tenant_get_own_agency_users(self):
        """Positive: Tenant can fetch users created under their workspace"""
        self.client.force_authenticate(user=self.tenant1)
        response = self.client.get('/api/auth/users/agency/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        usernames = [u['username'] for u in response.data['users']]
        self.assertIn('caller1', usernames)
        self.assertIn('ops1', usernames)

    def test_caller_attendance_toggle(self):
        """Positive: Tenant can toggle caller attendance status"""
        self.client.force_authenticate(user=self.tenant1)
        self.assertTrue(self.caller1.is_present)

        response = self.client.patch(
            f'/api/auth/callers/{self.caller1.id}/toggle-attendance/',
            {'is_present': False},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.caller1.refresh_from_db()
        self.assertFalse(self.caller1.is_present)

    # ----------------- NEGATIVE TESTS -----------------

    def test_login_invalid_password(self):
        """Negative: Login with wrong password returns 400 Bad Request"""
        response = self.client.post('/api/auth/login/', {
            'email': 'tenant1@agency.com',
            'password': 'WrongPassword999!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_email(self):
        """Negative: Login with non-existent email returns 400 Bad Request"""
        response = self.client.post('/api/auth/login/', {
            'email': 'doesnotexist@example.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_access_denied(self):
        """Negative: Protected endpoints reject requests without token"""
        response = self.client.get('/api/auth/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_superadmin_forbidden_tenants_hub(self):
        """Negative: Regular tenant or staff cannot access SuperAdmin tenant list"""
        self.client.force_authenticate(user=self.tenant1)
        response = self.client.get('/api/auth/tenants/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tenant_cannot_toggle_another_tenant_caller(self):
        """Negative: Tenant 2 cannot toggle attendance of Tenant 1's caller"""
        self.client.force_authenticate(user=self.tenant2)
        response = self.client.patch(
            f'/api/auth/callers/{self.caller1.id}/toggle-attendance/',
            {'is_present': False},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
