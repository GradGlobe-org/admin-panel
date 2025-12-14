import json
from uuid import UUID

from authentication.models import Employee
from django.db import DatabaseError, connection, transaction
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from student.models import Student

from website.utils import token_required

from .models import Task, TaskAssignment


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
                "employee": (
                    {
                        "id": task.creator_employee.id,
                        "name": task.creator_employee.name,
                    }
                    if task.creator_employee
                    else None
                ),
                "student": (
                    {
                        "id": task.creator_student.id,
                        "full_name": task.creator_student.full_name,
                    }
                    if task.creator_student
                    else None
                ),
            },
            "created_at": task.created_at.isoformat(),
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "assignments": [],
        }

        if user_type == "employee":
            # Employee can see ALL assignments
            visible_assignments = task.assignments.all()

        elif user_type == "student":
            # Student can only see their own assignment
            visible_assignments = task.assignments.filter(student=user)

        # BUT if the user is the creator, override and show ALL assignments
        if task.creator_employee == user or task.creator_student == user:
            visible_assignments = task.assignments.all()

        # Build assignments list
        for assignment in visible_assignments:
            task_dict["assignments"].append(
                {
                    "id": assignment.id,
                    "status": assignment.status,
                    "assigned_on": assignment.assigned_on.isoformat(),
                    "employee": (
                        {
                            "id": assignment.employee.id,
                            "name": assignment.employee.name,
                        }
                        if assignment.employee
                        else None
                    ),
                    "student": (
                        {
                            "id": assignment.student.id,
                            "full_name": assignment.student.full_name,
                        }
                        if assignment.student
                        else None
                    ),
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
            body = json.loads(raw)  # ✔ FIXED
        except UnicodeDecodeError:
            return JsonResponse(
                {"error": "Request body must be UTF-8 encoded"}, status=400
            )
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
                    return JsonResponse(
                        {"error": "Invalid datetime format"}, status=400
                    )

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
                        "due_date": (
                            task.due_date.isoformat() if task.due_date else None
                        ),
                    },
                },
                status=201,
            )

        except Exception as e:
            return JsonResponse(
                {"error": "An error occurred while creating the task"}, status=500
            )

    def put(self, request, task_id):
        student, error = self.get_student(request)
        if error:
            return error

        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return JsonResponse({"error": "Task not found"}, status=404)

        assignment = TaskAssignment.objects.filter(task=task, student=student).first()

        if not assignment and task.creator_student != student:
            return JsonResponse(
                {"error": "You are neither the creator nor assigned to this task"},
                status=403,
            )

        if task.creator_student == student:
            allowed_fields = ["title", "description", "priority", "due_date"]
            for field in allowed_fields:
                if field in body:
                    setattr(task, field, body[field])
            task.save()

        if assignment:
            if "status" in body:
                if body["status"] not in dict(TaskAssignment.STATUS_CHOICES):
                    return JsonResponse({"error": "Invalid status value"}, status=400)
                assignment.status = body["status"]
                assignment.save(update_fields=["status"])

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
                "assignment": {
                    "status": assignment.status if assignment else None,
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


@method_decorator(csrf_exempt, name="dispatch")
class EmployeeTaskView(View):
    """Employee-only API to create tasks and assign either to employees OR their assigned students."""

    def get_employee(self, request):
        auth_token = request.headers.get("Authorization")
        if not auth_token:
            return None, JsonResponse(
                {"error": "Authorization header missing"}, status=401
            )

        try:
            token = UUID(auth_token)
        except ValueError:
            return None, JsonResponse({"error": "Invalid auth token"}, status=400)

        try:
            employee = Employee.objects.get(authToken=token)
            return employee, None
        except Employee.DoesNotExist:
            return None, JsonResponse({"error": "Invalid token"}, status=401)

    def post(self, request):
        employee, error = self.get_employee(request)
        if error:
            return error

        # Parse JSON
        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        title = body.get("title")
        if not title:
            return JsonResponse({"error": "Title is required"}, status=400)

        description = body.get("description", "")
        priority = body.get("priority", "medium")
        due_date_raw = body.get("due_date")

        assign_employees = body.get("assign_employees", [])
        assign_students = body.get("assign_students", [])

        # Validate priority
        if priority not in ["high", "medium", "low"]:
            return JsonResponse({"error": "Invalid priority"}, status=400)

        # Parse due_date
        due_date = None
        if due_date_raw:
            due_date = parse_datetime(due_date_raw)
            if due_date is None:
                return JsonResponse({"error": "Invalid datetime format"}, status=400)

        # Validate employees
        valid_employees = Employee.objects.filter(id__in=assign_employees)
        if valid_employees.count() != len(assign_employees):
            return JsonResponse(
                {"error": "One or more assigned employees not found"}, status=400
            )

        # Validate students
        valid_students = Student.objects.filter(
            id__in=assign_students, assigned_counsellors__employee=employee
        ).distinct()
        if valid_students.count() != len(assign_students):
            return JsonResponse(
                {
                    "error": "One or more assigned students are not your assigned students"
                },
                status=400,
            )

        # Create the task
        task = Task.objects.create(
            title=title,
            description=description,
            priority=priority,
            status="todo",
            creator_employee=employee,
            due_date=due_date,
        )

        # Assign to employees
        for emp in valid_employees:
            TaskAssignment.objects.create(task=task, employee=emp)

        # Assign to students
        for stu in valid_students:
            TaskAssignment.objects.create(task=task, student=stu)

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

    def put(self, request, task_id):
        employee, error = self.get_employee(request)
        if error:
            return error

        try:
            task = Task.objects.get(id=task_id, creator_employee=employee)
        except Task.DoesNotExist:
            return JsonResponse(
                {"error": "Task not found or not owned by you"}, status=404
            )

        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # Update fields
        for field in ["title", "description", "priority", "status", "due_date"]:
            if field in body:
                if field == "due_date":
                    due_date = parse_datetime(body["due_date"])
                    if due_date is None:
                        return JsonResponse(
                            {"error": "Invalid datetime format"}, status=400
                        )
                    task.due_date = due_date
                else:
                    setattr(task, field, body[field])

        # Handle reassignment
        assign_employees = body.get("assign_employees")
        assign_students = body.get("assign_students")

        if assign_employees is not None or assign_students is not None:
            # Clear previous assignments
            task.assignments.all().delete()

            # Reassign employees
            if assign_employees:
                valid_employees = Employee.objects.filter(id__in=assign_employees)
                if valid_employees.count() != len(assign_employees):
                    return JsonResponse(
                        {"error": "One or more assigned employees not found"},
                        status=400,
                    )
                for emp in valid_employees:
                    TaskAssignment.objects.create(task=task, employee=emp)

            # Reassign students
            if assign_students:
                valid_students = Student.objects.filter(
                    id__in=assign_students, assigned_counsellors__employee=employee
                ).distinct()
                if valid_students.count() != len(assign_students):
                    return JsonResponse(
                        {
                            "error": "One or more assigned students are not your assigned students"
                        },
                        status=400,
                    )
                for stu in valid_students:
                    TaskAssignment.objects.create(task=task, student=stu)

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
        employee, error = self.get_employee(request)
        if error:
            return error

        try:
            task = Task.objects.get(id=task_id, creator_employee=employee)
        except Task.DoesNotExist:
            return JsonResponse(
                {"error": "Task not found or not owned by you"}, status=404
            )

        # Delete all assignments first (optional, Django will cascade if on_delete=CASCADE)
        task.assignments.all().delete()

        # Delete the task itself
        task.delete()

        return JsonResponse({"message": "Task deleted successfully"}, status=200)


@method_decorator(csrf_exempt, name="dispatch")
class EmployeeTaskUnassignView(View):
    def post(self, request, task_id):
        employee, error = EmployeeTaskView().get_employee(request)
        if error:
            return error

        try:
            task = Task.objects.get(id=task_id, creator_employee=employee)
        except Task.DoesNotExist:
            return JsonResponse(
                {"error": "Task not found or not owned by you"}, status=404
            )

        try:
            body = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        unassign_employees = body.get("unassign_employees", [])
        unassign_students = body.get("unassign_students", [])

        if unassign_employees:
            task.assignments.filter(employee_id__in=unassign_employees).delete()

        if unassign_students:
            task.assignments.filter(student_id__in=unassign_students).delete()

        return JsonResponse({"message": "Assignments removed successfully"})


@require_http_methods(["GET"])
@token_required
def get_assigned_users(request):
    try:
        employee_id = request.user.id

        with connection.cursor() as cursor:
            cursor.execute("SELECT get_assigned_students_employee(%s);", [employee_id])
            result = cursor.fetchone()

        raw_data = result[0]

        # If Postgres returns string → convert to dict
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)

        return JsonResponse(raw_data, safe=False)

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                # "message": str(e)
            },
            status=500,
        )
