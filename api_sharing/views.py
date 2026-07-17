from django.http import JsonResponse
from website.models import PortfolioCategory, PortfolioItem, WebsiteClientLogo
from .auth import api_key_required

def _make_absolute(url, request):
    """Helper to convert relative media/static URLs into absolute URLs."""
    if not url:
        return ''
    if url.startswith(('http://', 'https://')):
        return url
    return request.build_absolute_uri(url)

@api_key_required
def shared_portfolio_list(request):
    """
    Expose active categories and their nested active products (images and videos)
    with absolute URLs for external consumption by the panel.
    """
    categories_qs = PortfolioCategory.objects.filter(is_active=True).order_by('order', 'name')
    categories_data = []
    
    for category in categories_qs:
        products_qs = category.items.filter(is_active=True).order_by('order', '-created_at')
        products_data = []
        
        for item in products_qs:
            products_data.append({
                'id': item.id,
                'title': item.title,
                'slug': item.slug,
                'description': item.description,
                'item_type': item.item_type,
                'orientation': item.orientation,
                'media_url': _make_absolute(item.media_url, request),
                'video_url': item.video_url or '',
                'video_fallback_url': _make_absolute(item.video_fallback_url, request) if item.video_file else '',
                'video_stream_url': _make_absolute(item.video_stream_url, request) if item.video_file else '',
                'video_thumbnail_url': _make_absolute(item.video_thumbnail_url, request) if (item.image or item.video_file) else '',
                'is_featured': item.is_featured,
                'order': item.order,
                'created_at': item.created_at.isoformat(),
            })
            
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'icon': category.icon,
            'description': category.description,
            'is_bento': category.is_bento,
            'bento_size': category.bento_size,
            'order': category.order,
            'products': products_data,
        })
        
    return JsonResponse({
        'success': True,
        'categories': categories_data
    })

@api_key_required
def shared_client_list(request):
    """
    Expose the complete list of website client logos, visibility settings,
    and aggregate record counts to the panel.
    """
    clients_qs = WebsiteClientLogo.objects.all().order_by('website_display_order', '-created_at')
    clients_data = []
    
    for client in clients_qs:
        clients_data.append({
            'id': client.id,
            'name': client.name,
            'email': client.email or '',
            'logo_url': _make_absolute(client.logo.url, request) if client.logo else '',
            'website_is_visible': client.website_is_visible,
            'website_display_order': client.website_display_order,
            'total_records': client.total_records,
            'created_at': client.created_at.isoformat(),
            'updated_at': client.updated_at.isoformat(),
        })
        
    return JsonResponse({
        'success': True,
        'clients': clients_data
    })


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@api_key_required
@require_http_methods(['POST'])
def shared_contact_submit(request):
    """
    Accept contact/enquiry form submissions from the mobile app or panel application.
    Protected by server-to-server API key.
    """
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        name = str(data.get('name', '')).strip()
        email = str(data.get('email', '')).strip()
        phone = str(data.get('phone', '')).strip()
        subject = str(data.get('subject', 'Mobile App Contact Submission')).strip()
        message = str(data.get('message', '')).strip()

        if not all([name, email, message]):
            return JsonResponse({'success': False, 'message': 'Name, email, and message are required.'}, status=400)

        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({'success': False, 'message': 'Invalid email address.'}, status=400)

        from website.services import ContactSubmissionService
        ContactSubmissionService.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message
        )
        return JsonResponse({'success': True, 'message': 'Message sent successfully!'})
    except Exception as e:
        logger.error("API contact submission failed: %s", e)
        return JsonResponse({'success': False, 'message': 'Internal server error.'}, status=500)
