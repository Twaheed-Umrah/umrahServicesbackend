from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import APIKey
from django.utils import timezone

class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        api_key = request.META.get('HTTP_X_API_KEY')
        
        if not api_key:
            return None
        
        try:
            key_obj = APIKey.objects.get(key=api_key, is_active=True)
            # Update last used timestamp
            key_obj.last_used = timezone.now()
            key_obj.save(update_fields=['last_used'])
            return (key_obj.user, key_obj)
        except APIKey.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')


