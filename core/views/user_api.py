"""
User Management API for External App Integration.
Allows managing administrative users (Staff/Admins).
"""
import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from ..services.permission_service import api_require_super_admin, PermissionService

User = get_user_model()

@csrf_exempt
@api_require_super_admin
@require_http_methods(["GET"])
def api_user_list(request):
    """List all administrative users."""
    users = User.objects.all().order_by('role', 'username')
    data = [{
        'id': u.id,
        'username': u.username,
        'email': u.email,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'role': u.role,
        'is_active': u.is_active,
        'is_staff': u.is_staff,
        'last_login': u.last_login.isoformat() if u.last_login else None,
    } for u in users]
    return JsonResponse({'success': True, 'users': data})

@csrf_exempt
@api_require_super_admin
@require_http_methods(["POST"])
def api_user_create(request):
    """Create a new administrative user."""
    try:
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'admin_staff')
        
        if not username or not email or not password:
            return JsonResponse({'success': False, 'message': 'Missing required fields'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({'success': False, 'message': 'Username already exists'}, status=400)
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=role,
        )
        return JsonResponse({'success': True, 'user_id': user.id, 'message': 'User created successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@api_require_super_admin
@require_http_methods(["POST"])
def api_user_update(request, pk):
    """Update an existing user."""
    user = get_object_or_404(User, pk=pk)
    try:
        data = json.loads(request.body)
        if 'email' in data: user.email = data['email']
        if 'first_name' in data: user.first_name = data['first_name']
        if 'last_name' in data: user.last_name = data['last_name']
        if 'role' in data: user.role = data['role']
        if 'is_active' in data: user.is_active = bool(data['is_active'])
        
        if 'password' in data and data['password']:
            user.set_password(data['password'])
            
        user.save()
        return JsonResponse({'success': True, 'message': 'User updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@api_require_super_admin
@require_http_methods(["POST"])
def api_user_delete(request, pk):
    """Deactivate or delete a user."""
    user = get_object_or_404(User, pk=pk)
    if user.is_superuser or user.role == 'pro_user':
        return JsonResponse({'success': False, 'message': 'Cannot delete super admin or pro user via API'}, status=403)
    
    user.is_active = False
    user.save()
    return JsonResponse({'success': True, 'message': 'User deactivated successfully'})

@csrf_exempt
@login_required
@require_http_methods(["GET"])
def api_get_me(request):
    """Return current session user info and permissions."""
    user = request.user
    perms = PermissionService.get_permission_context(user)
    return JsonResponse({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'full_name': user.get_full_name(),
        },
        'permissions': perms['user_permissions']
    })
