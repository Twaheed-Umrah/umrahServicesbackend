from django.db import connection
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

class HealthCheckView(APIView):
    """
    AWS Application Load Balancer (ALB) and Container Health Check.
    Checks database connection and service responsiveness.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        db_status = "ok"
        try:
            connection.ensure_connection()
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            return Response(
                {
                    "status": "unhealthy",
                    "database": db_status,
                    "timestamp": timezone.now().isoformat(),
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response(
            {
                "status": "healthy",
                "database": "connected",
                "service": "masar-umrah-backend",
                "timestamp": timezone.now().isoformat(),
            },
            status=status.HTTP_200_OK
        )
