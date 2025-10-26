from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json

from authentication.models import Employee
from .models import CallRequest, Student, AssignedCounsellor


@method_decorator(csrf_exempt, name="dispatch")
class EmployeeCallRequestsView(View):
    def get(self, request):
        auth_token = request.headers.get("Authorization")

        if not auth_token:
            return JsonResponse(
                {"error": "Authorization header is required"}, status=400
            )

        try:
            employee = Employee.objects.get(authToken=auth_token)
        except Employee.DoesNotExist:
            return JsonResponse({"error": "Invalid authToken"}, status=404)

        calls = CallRequest.objects.filter(employee=employee).select_related("student")

        data = [
            {
                "id": c.id,
                "student_id": c.student.id,
                "student_name": c.student.full_name,
                "employee_name": c.employee.name,
                "requested_at": c.requested_on,
            }
            for c in calls
        ]
        return JsonResponse(data, safe=False, status=200)


@method_decorator(csrf_exempt, name="dispatch")
class StudentCallRequestsView(View):
    def get(self, request):
        auth_token = request.headers.get("Authorization")

        if not auth_token:
            return JsonResponse(
                {"error": "Authorization header is required"}, status=400
            )

        try:
            student = Student.objects.get(authToken=auth_token)
        except Student.DoesNotExist:
            return JsonResponse({"error": "Invalid authToken"}, status=404)

        calls = CallRequest.objects.filter(student=student).select_related("employee")

        data = [
            {
                "id": c.id,
                "employee_id": c.employee.id,
                "student_name": c.student.full_name,
                "employee_name": c.employee.name,
                "requested_at": c.requested_on,
            }
            for c in calls
        ]
        return JsonResponse(data, safe=False, status=200)


@method_decorator(csrf_exempt, name="dispatch")
class RequestCallWithCounsellorView(View):
    def get(self, request):
        auth_token = request.headers.get("Authorization")
        if not auth_token:
            return JsonResponse(
                {"error": "Authorization header is required"}, status=400
            )

        try:
            student = Student.objects.get(authToken=auth_token)
        except Student.DoesNotExist:
            return JsonResponse({"error": "Invalid authToken"}, status=404)

        assigned = AssignedCounsellor.objects.filter(student=student).select_related(
            "employee"
        )
        if not assigned.exists():
            return JsonResponse(
                {"error": "No counsellor assigned to this student"}, status=404
            )

        created_calls = []
        for assign in assigned:
            employee = assign.employee
            if not CallRequest.objects.filter(
                student=student, employee=employee
            ).exists():
                call = CallRequest.objects.create(student=student, employee=employee)
                created_calls.append(
                    {
                        "id": call.id,
                        "student_id": student.id,
                        "student_name": student.full_name,
                        "employee_id": employee.id,
                        "employee_name": employee.name,
                        "requested_at": call.requested_on,
                    }
                )

        if not created_calls:
            return JsonResponse(
                {"error": "Call request already exists with assigned counsellor(s)"},
                status=400,
            )

        return JsonResponse(created_calls, safe=False, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class CompleteCallRequestView(View):
    def post(self, request):
        auth_token = request.headers.get("Authorization")
        if not auth_token:
            return JsonResponse(
                {"error": "Authorization header is required"}, status=400
            )

        try:
            employee = Employee.objects.get(authToken=auth_token)
        except Employee.DoesNotExist:
            return JsonResponse({"error": "Invalid authToken"}, status=404)

        try:
            data = json.loads(request.body.decode("utf-8"))
            student_id = data.get("student_id")
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        if not student_id:
            return JsonResponse({"error": "student_id is required"}, status=400)

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            return JsonResponse({"error": "Student not found"}, status=404)

        try:
            call = CallRequest.objects.get(student=student, employee=employee)
        except CallRequest.DoesNotExist:
            return JsonResponse({"error": "Call request not found"}, status=404)

        call.delete()

        return JsonResponse(
            {
                "status": "success",
                "message": f"Call request for student {student.full_name} marked as completed",
            },
            status=200,
        )
