import uuid
import strawberry
from typing import Optional, Annotated, List, Any, Awaitable
from datetime import datetime
from strawberry.scalars import JSON

from authentication.models import Employee
from student.models import Student
from tasks.models import Task, TaskAssignment
from strawberry.exceptions import GraphQLError

# get_my_created_tasks/owned_task
# get_all_my_tasks
# edit_task
# edit_task_assignment/unassign/assign
# delete_task


@strawberry.type
class TaskSchema:
    id: int
    title: str
    description: str
    priority: int
    status: str
    created_at: datetime
    due_date: datetime
    assigned_students: JSON
    assigned_employees: JSON

    @classmethod
    def get_owned_tasks(cls, auth_token:uuid.UUID):
        user = None
        user_type = None
        try:
            user = Employee.objects.get(authToken=auth_token)
            user_type = "employee"
        except Employee.DoesNotExist:
            try:
                user = Student.objects.get(authToken=auth_token)
                user_type = "student"
            except Student.DoesNotExist:
                raise GraphQLError("Invalid auth token")

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

            return task_dict

@strawberry.type
class TaskQuery:
    get_owned_tasks : JSON = strawberry.field(
        resolver=TaskSchema.get_owned_tasks,
    )