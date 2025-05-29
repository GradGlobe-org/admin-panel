from django.http import JsonResponse
from functools import wraps
from authentication.models import api_key
import uuid

def api_key_required(view_func):
    """
    Decorator to verify API key in request headers.
    Expects 'key' header with a valid UUID key.
    Returns JSON responses with appropriate HTTP status codes.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Get API key from headers
        api_key_value = request.headers.get('key')
        
        if not api_key_value:
            return JsonResponse(
                {'error': 'API key required'}, 
                status=401
            )
        
        try:
            # Convert string to UUID object for proper comparison
            key_uuid = uuid.UUID(api_key_value)
        except ValueError:
            return JsonResponse(
                {'error': 'Invalid API key format'}, 
                status=400
            )
        
        # Check if key exists in database
        if not api_key.objects.filter(key=key_uuid).exists():
            return JsonResponse(
                {'error': 'Invalid API key'}, 
                status=403
            )
            
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view