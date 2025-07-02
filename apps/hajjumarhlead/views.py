from rest_framework import generics, status
from rest_framework.response import Response
from .models import HajjUmrahBookingDemo, HajjUmrahBookingService
from .serializers import HajjUmrahBookingDemoSerializer, HajjUmrahBookingServiceSerializer
from .permissions import IsSuperAdmin, HasValidSecretKey


class HajjUmrahBookingDemoCreateView(generics.CreateAPIView):
    queryset = HajjUmrahBookingDemo.objects.all()
    serializer_class = HajjUmrahBookingDemoSerializer
    permission_classes = [HasValidSecretKey]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Hajj Umrah booking demo created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class HajjUmrahBookingDemoListView(generics.ListAPIView):
    queryset = HajjUmrahBookingDemo.objects.all().order_by('-created_at')
    serializer_class = HajjUmrahBookingDemoSerializer
    permission_classes = [IsSuperAdmin]


class HajjUmrahBookingServiceCreateView(generics.CreateAPIView):
    queryset = HajjUmrahBookingService.objects.all()
    serializer_class = HajjUmrahBookingServiceSerializer
    permission_classes = [HasValidSecretKey]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Hajj Umrah booking service created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'message': 'Validation failed',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class HajjUmrahBookingServiceListView(generics.ListAPIView):
    queryset = HajjUmrahBookingService.objects.all().order_by('-created_at')
    serializer_class = HajjUmrahBookingServiceSerializer
    permission_classes = [IsSuperAdmin]
