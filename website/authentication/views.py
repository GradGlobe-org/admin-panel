from django.shortcuts import render
from .models import Employee, LoginLog
import json
from django.http import JsonResponse
import uuid
from django.views.decorators.csrf import csrf_exempt
from website.utils import api_key_required

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

    # save login logs
    LoginLog.objects.create(employee=employee_obj)

    # Get job roles as a list of strings
    job_roles_list = list(employee_obj.job_roles.values_list('role', flat=True))
    permissions = set()

    for role in employee_obj.job_roles.all():
        role_permissions = role.permissions.values_list("name", flat=True)
        permissions.update(role_permissions)


    return JsonResponse({
        "id" : employee_obj.id,
        "authToken": str(new_token),
        "name": employee_obj.name,
        "jobRoles": job_roles_list,
        "permissions": list(permissions)
    }, status=200)
