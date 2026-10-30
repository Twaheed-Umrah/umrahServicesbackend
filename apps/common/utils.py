from rest_framework import serializers
from django.conf import settings

def build_absolute_media_url(value, request=None):
    """
    Guarantees returning a complete, fully-qualified absolute URL
    (e.g., http://your-domain:8000/media/traveler_photos/img.jpg)
    whether running on a remote server, VPS, IP address, or localhost.
    Saves files on the local server filesystem and returns complete URLs.
    """
    if not value:
        return None
        
    url = getattr(value, 'url', None) or str(value)
    if not url:
        return None
    
    # If already an absolute URL (e.g. external link), return as is
    if url.startswith('http://') or url.startswith('https://'):
        return url

    # If active HTTP request context exists, use it to construct full URI
    if request is not None:
        try:
            return request.build_absolute_uri(url)
        except Exception:
            pass

    # Fallback to configured server domain / IP
    base = (
        getattr(settings, 'BACKEND_URL', None) or
        getattr(settings, 'SERVER_BASE_URL', None) or
        'http://127.0.0.1:8000'
    ).rstrip('/')
    
    if not url.startswith('/'):
        url = '/' + url
    return f"{base}{url}"


class AbsoluteFileField(serializers.FileField):
    """
    FileField that always returns a complete, fully-qualified URL in API responses.
    """
    def to_representation(self, value):
        if not value:
            return None
        return build_absolute_media_url(value, self.context.get('request'))


class AbsoluteImageField(serializers.ImageField):
    """
    ImageField that always returns a complete, fully-qualified URL in API responses.
    """
    def to_representation(self, value):
        if not value:
            return None
        return build_absolute_media_url(value, self.context.get('request'))

