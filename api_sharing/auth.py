from functools import wraps
from django.http import JsonResponse
from django.conf import settings

def api_key_required(view_func):
    """
    Decorator for server-to-server API Key authentication.
    Accepts token via 'X-API-KEY' header or 'api_key' query parameter.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        api_key = request.headers.get('X-API-KEY') or request.GET.get('api_key')
        
        expected_key = getattr(settings, 'WEB_APP_API_KEY', None)
        
        if not expected_key or api_key != expected_key:
            return JsonResponse(
                {
                    'success': False,
                    'message': 'Unauthorized. A valid X-API-KEY is required.'
                },
                status=401
            )
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view
