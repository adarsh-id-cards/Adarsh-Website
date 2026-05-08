from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """
    Basic health check endpoint.
    Checks database connectivity.
    """
    health = {
        'status': 'healthy',
        'database': 'unknown',
    }
    
    try:
        connection.ensure_connection()
        health['database'] = 'connected'
    except Exception as e:
        health['status'] = 'unhealthy'
        health['database'] = f'error: {str(e)}'
        
    return JsonResponse(health)
