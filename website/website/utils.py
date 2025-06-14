from django.http import JsonResponse
from functools import wraps
import uuid
import os

from authentication.models import Employee, Permission


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
        api_key = uuid.UUID(os.getenv("API_KEY"))
        if not api_key != api_key_value:
            return JsonResponse(
                {'error': 'Invalid API key'}, 
                status=403
            )
            
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def has_perms(employee_id: int, perms_list: list) -> bool:
    try:
        employee = Employee.objects.prefetch_related('job_roles__permissions').get(id=employee_id)
    except Employee.DoesNotExist:
        return False

    # Gather all permissions attached to the employee's job roles
    assigned_perms = set(
        perm.name for role in employee.job_roles.all() for perm in role.permissions.all()
    )

    for perm_name in perms_list:
        if perm_name not in assigned_perms:
            return False

    return True
