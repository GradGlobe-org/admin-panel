from django.shortcuts import render
from .models import Employee, LoginLog
import json
from django.http import JsonResponse
import uuid
from django.views.decorators.csrf import csrf_exempt
from website.utils import api_key_required, token_required
from django.views.decorators.http import require_http_methods

@api_key_required
@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "Method not allowed"
        }, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON request"
        }, status=400)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({
            "error": "Missing required fields"
        }, status=400)

    employee_obj = Employee.objects.filter(username=username, password=password).first()
    if not employee_obj:
        return JsonResponse({
            "error": "No such Employee exists"
        }, status=409)

    new_token = uuid.uuid4()
    employee_obj.authToken = new_token
    employee_obj.save()

    # Save login logs
    LoginLog.objects.create(employee=employee_obj)

    # Prepare role-permission structure
    job_roles_list = []
    for role in employee_obj.job_roles.all():
        role_permissions = list(role.permissions.values_list("name", flat=True))
        job_roles_list.append({
            "role": role.role,
            "permissions": role_permissions
        })

    return JsonResponse({
        "id": employee_obj.id,
        "authToken": str(new_token),
        "name": employee_obj.name,
        "jobRoles": job_roles_list
    }, status=200)
