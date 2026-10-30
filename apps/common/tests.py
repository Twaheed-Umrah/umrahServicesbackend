from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

class SystemHealthCheckTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_health_check_api_endpoint(self):
        """Positive: /api/health/ returns 200 OK and database connected"""
        response = self.client.get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['database'], 'connected')

    def test_health_check_root_endpoint(self):
        """Positive: /health/ endpoint for AWS ALB target group returns 200 OK"""
        response = self.client.get('/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
