from django.shortcuts import render

def error_400(request, exception=None):
    return render(request, 'errors/error.html', {
        'status_code': 400, 
        'title': 'Bad Request',
        'heading': 'We Couldn\'t Understand That',
        'message': 'The request was malformed or missing required parameters. Please try again from the starting page.'
    }, status=400)

def error_403(request, exception=None):
    return render(request, 'errors/error.html', {
        'status_code': 403, 
        'title': 'Forbidden',
        'heading': 'Access Restricted',
        'message': 'You do not have the required permissions to view this resource. If you believe this is an error, contact your administrator.'
    }, status=403)

def error_404(request, exception=None):
    return render(request, 'errors/error.html', {
        'status_code': 404, 
        'title': 'Page Not Found',
        'heading': 'Lost in the Ether?',
        'message': 'The page you are looking for has been moved, deleted, or never existed in the first place.'
    }, status=404)

def error_500(request):
    return render(request, 'errors/error.html', {
        'status_code': 500, 
        'title': 'Server Error',
        'heading': 'An Unexpected Glitch',
        'message': 'Our servers encountered a problem while processing your request. We have been notified and are looking into it.'
    }, status=500)

def csrf_failure(request, reason=""):
    return render(request, 'errors/error.html', {
        'status_code': 403, 
        'title': 'CSRF Verification Failed',
        'heading': 'Security Session Expired',
        'message': f'Your security token is missing or invalid. This usually happens if you leave a page open for too long. Please refresh and try again. ({reason})'
    }, status=403)
