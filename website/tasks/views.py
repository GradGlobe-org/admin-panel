from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Task, TaskAssignment
from authentication.models import Employee
from student.models import Student
from uuid import UUID
import json
from django.views import View
from django.utils.decorators import method_decorator
from django.utils.dateparse import parse_datetime


@csrf_exempt
def my_tasks(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        return JsonResponse(
            {"error": "Authorization header missing or invalid"}, status=401
        )

    token_str = auth_header

    try:
        token = UUID(token_str)
    except ValueError:
        return JsonResponse({"error": "Invalid auth token format"}, status=400)

    user = None
    user_type = None
    try:
        user = Employee.objects.get(authToken=token)
        user_type = "employee"
    except Employee.DoesNotExist:
        try:
            user = Student.objects.get(authToken=token)
            user_type = "student"
        except Student.DoesNotExist:
            return JsonResponse({"error": "Invalid token"}, status=401)

    if user_type == "employee":
        assigned_tasks = Task.objects.filter(assignments__employee=user)
        created_tasks = Task.objects.filter(creator_employee=user)
    else:
        assigned_tasks = Task.objects.filter(assignments__student=user)
        created_tasks = Task.objects.filter(creator_student=user)

    tasks = (
        (assigned_tasks | created_tasks)
        .distinct()
        .prefetch_related("assignments__employee", "assignments__student")
    )

    tasks_data = []

    for task in tasks:
        task.mark_overdue_if_needed()
        task_dict = {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "priority": task.priority,
            "status": task.status,
            "creator": {
                "employee": {
                    "id": task.creator_employee.id,
                    "name": task.creator_employee.name,
                }
                if task.creator_employee
                else None,
                "student": {
                    "id": task.creator_student.id,
                    "full_name": task.creator_student.full_name,
                }
                if task.creator_student
                else None,
            },
            "created_at": task.created_at.isoformat(),
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "assignments": [],
        }

        for assignment in task.assignments.all():
            task_dict["assignments"].append(
                {
                    "id": assignment.id,
                    "status": assignment.status,
                    "assigned_on": assignment.assigned_on.isoformat(),
                    "employee": {
                        "id": assignment.employee.id,
                        "name": assignment.employee.name,
                    }
                    if assignment.employee
                    else None,
                    "student": {
                        "id": assignment.student.id,
                        "full_name": assignment.student.full_name,
                    }
                    if assignment.student
                    else None,
                }
            )

        tasks_data.append(task_dict)

    return JsonResponse({"tasks": tasks_data}, safe=False)


@method_decorator(csrf_exempt, name="dispatch")
class StudentTaskView(View):
    def get_student(self, request):
        auth_token = request.headers.get("Authorization")
        if not auth_token:
            return None, JsonResponse(
                {"error": "Authorization header missing"}, status=401
            )

        try:
            student = Student.objects.get(authToken=auth_token)
            return student, None
        except Student.DoesNotExist:
            return None, JsonResponse({"error": "Invalid token"}, status=401)


    def post(self, request):
        student, error = self.get_student(request)
        if error:
            return error
        try:
            raw = request.body.decode("utf-8")
            body = json.loads(raw)               # ✔ FIXED
        except UnicodeDecodeError:
            return JsonResponse({"error": "Request body must be UTF-8 encoded"}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

        try:
            title = body.get("title")
            description = body.get("description", "")
            priority = body.get("priority", "medium")
            due_date_raw = body.get("due_date")

            if not title:
                return JsonResponse({"error": "Title is required"}, status=400)

            due_date = None
            if due_date_raw:
                due_date = parse_datetime(due_date_raw)
                if due_date is None:
                    return JsonResponse({"error": "Invalid datetime format"}, status=400)

            task = Task.objects.create(
                title=title,
                description=description,
                priority=priority,
                status="todo",
                creator_student=student,
                due_date=due_date,
            )

            TaskAssignment.objects.create(task=task, student=student)

            return JsonResponse(
                {
                    "message": "Task created and assigned successfully",
                    "task": {
                        "id": str(task.id),
                        "title": task.title,
                        "priority": task.priority,
                        "status": task.status,
                        "due_date": task.due_date.isoformat() if task.due_date else None,
                    },
                },
                status=201,
            )

        except Exception as e:
            return JsonResponse({"error": "An error occurred while creating the task"}, status=500)


    def put(self, request, task_id):
        student, error = self.get_student(request)
        if error:
            return error

        try:
            task = Task.objects.get(id=task_id, creator_student=student)
        except Task.DoesNotExist:
            return JsonResponse(
                {"error": "Task not found or not owned by you"}, status=404
            )

        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Update allowed fields
        for field in ["title", "description", "priority", "status", "due_date"]:
            if field in body:
                setattr(task, field, body[field])

        task.save()

        return JsonResponse(
            {
                "message": "Task updated successfully",
                "task": {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority,
                    "status": task.status,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                },
            }
        )

    def delete(self, request, task_id):
        student, error = self.get_student(request)
        if error:
            return error

        try:
            task = Task.objects.get(id=task_id, creator_student=student)
        except Task.DoesNotExist:
            return JsonResponse(
                {"error": "Task not found or not owned by you"}, status=404
            )

        task.delete()
        return JsonResponse({"message": "Task deleted successfully"}, status=200)
