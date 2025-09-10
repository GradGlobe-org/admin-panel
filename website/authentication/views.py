from django.shortcuts import render
from .models import Employee, LoginLog
import json
from django.http import JsonResponse
import uuid
import json
from django.views.decorators.csrf import csrf_exempt
from website.utils import api_key_required



@api_key_required
@csrf_exempt
def login(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON request"}, status=400)

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return JsonResponse({"error": "Missing required fields"}, status=400)

    try:
        with connection.cursor() as cursor:
            # Call the existing login_employee function
            cursor.execute(
                "SELECT public.login_employee(%s, %s) AS result",
                [username, password]
            )
            # Fetch the JSON result
            result = json.loads(cursor.fetchone()[0])

            if result:
                return JsonResponse(result, status=200)
            else:
                return JsonResponse({"error": "No such Employee exists"}, status=409)

    except Exception as e:
        error_message = str(e)
        if "No such Employee exists" in error_message:
            return JsonResponse({"error": "No such Employee exists"}, status=409)
        return JsonResponse({"error": "Internal server error"}, status=500)
