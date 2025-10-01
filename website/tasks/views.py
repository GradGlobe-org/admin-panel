# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .models import Task
# from authentication.models import Employee
# from student.models import Student
# from uuid import UUID
#
#
# @csrf_exempt
# def my_tasks(request):
#     if request.method != "GET":
#         return JsonResponse({"error": "Only GET allowed"}, status=405)
#
#     auth_header = request.headers.get("Authorization")
#     if not auth_header:
#         return JsonResponse(
#             {"error": "Authorization header missing or invalid"}, status=401
#         )
#
#     token_str = auth_header
#
#     try:
#         token = UUID(token_str)
#     except ValueError:
#         return JsonResponse({"error": "Invalid auth token format"}, status=400)
#
#     user = None
#     user_type = None
#     try:
#         user = Employee.objects.get(authToken=token)
#         user_type = "employee"
#     except Employee.DoesNotExist:
#         try:
#             user = Student.objects.get(authToken=token)
#             user_type = "student"
#         except Student.DoesNotExist:
#             return JsonResponse({"error": "Invalid token"}, status=401)
#
#     if user_type == "employee":
#         assigned_tasks = Task.objects.filter(assignments__employee=user)
#         created_tasks = Task.objects.filter(creator_employee=user)
#     else:
#         assigned_tasks = Task.objects.filter(assignments__student=user)
#         created_tasks = Task.objects.filter(creator_student=user)
#
#     tasks = (
#         (assigned_tasks | created_tasks)
#         .distinct()
#         .prefetch_related("assignments__employee", "assignments__student")
#     )
#
#     tasks_data = []
#
#     for task in tasks:
#         task.mark_overdue_if_needed()
#         task_dict = {
#             "id": str(task.id),
#             "title": task.title,
#             "description": task.description,
#             "priority": task.priority,
#             "status": task.status,
#             "creator": {
#                 "employee": {
#                     "id": task.creator_employee.id,
#                     "name": task.creator_employee.name,
#                 }
#                 if task.creator_employee
#                 else None,
#                 "student": {
#                     "id": task.creator_student.id,
#                     "full_name": task.creator_student.full_name,
#                 }
#                 if task.creator_student
#                 else None,
#             },
#             "created_at": task.created_at.isoformat(),
#             "due_date": task.due_date.isoformat() if task.due_date else None,
#             "assignments": [],
#         }
#
#         for assignment in task.assignments.all():
#             task_dict["assignments"].append(
#                 {
#                     "id": assignment.id,
#                     "status": assignment.status,
#                     "assigned_on": assignment.assigned_on.isoformat(),
#                     "employee": {
#                         "id": assignment.employee.id,
#                         "name": assignment.employee.name,
#                     }
#                     if assignment.employee
#                     else None,
#                     "student": {
#                         "id": assignment.student.id,
#                         "full_name": assignment.student.full_name,
#                     }
#                     if assignment.student
#                     else None,
#                 }
#             )
#
#         tasks_data.append(task_dict)
#
#     return JsonResponse({"tasks": tasks_data}, safe=False)
