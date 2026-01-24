import strawberry
from typing import Optional, Annotated, List, Any, Awaitable
from datetime import datetime
from authentication.models import Employee
from student.models import Student
from tasks.models import Task, TaskAssignment
from strawberry.exceptions import GraphQLError
import uuid
from django.db import transaction


@strawberry.type
class AssignmentSchema:
    id: int
    status: str
    assigned_on: datetime
    employee_id: int | None
    employee_name: str | None
    student_id: int | None
    student_name: str | None


@strawberry.type
class TaskSchema:
    id: uuid.UUID
    title: str
    description: str
    priority: str
    status: str
    created_by_me: bool
    assigned_to_me: bool
    created_at: datetime
    due_date: datetime | None
    assignments: list[AssignmentSchema] = strawberry.field(description="assigned users if you are the creator")

    @classmethod
    def get_tasks(cls, auth_token: uuid.UUID, created_by_me: bool = True, assigned_to_me: bool = True) -> list[
        "TaskSchema"]:
        try:
            user = Employee.objects.get(authToken=auth_token)
        except Employee.DoesNotExist:
            raise GraphQLError("Invalid auth token")

        assigned_tasks = Task.objects.none()
        created_tasks = Task.objects.none()

        if created_by_me:
            assigned_tasks = Task.objects.filter(creator_employee=user)
        if assigned_to_me:
            created_tasks = Task.objects.filter(assignments__employee=user)

        print(assigned_tasks)
        print(created_tasks)

        tasks = (
            (assigned_tasks | created_tasks)
            .distinct()
            .prefetch_related("assignments__employee")
        )

        result: list[TaskSchema] = []

        for task in tasks:
            task.mark_overdue_if_needed()

            if task.creator_employee == user:
                visible_assignments = task.assignments.all()
            else:
                visible_assignments = task.assignments.filter(employee=user)

            assignments = [
                AssignmentSchema(
                    id=a.id,
                    status=a.status,
                    assigned_on=a.assigned_on,
                    employee_id=a.employee.id if a.employee else None,
                    employee_name=a.employee.name if a.employee else None,
                    student_id=a.student.id if a.student else None,
                    student_name=a.student.full_name if a.student else None,
                )
                for a in visible_assignments
            ]

            print(assignments)

            result.append(
                cls(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    status=task.status,
                    created_by_me=task.creator_employee == user,
                    assigned_to_me=task.assignments.filter(employee=user).exists(),
                    created_at=task.created_at,
                    due_date=task.due_date,
                    assignments=assignments,
                )
            )

        return result

    @classmethod
    def create_task(cls,
                    auth_token: str,
                    title: str,
                    description: str,
                    priority: str,
                    status: str,
                    due_date: Optional[str] = None,
                    assign_student_ids: Optional[List[int]] = None,
                    assign_employee_ids: Optional[List[int]] = None,
                    ) -> "TaskSchema":

        try:
            user = Employee.objects.get(authToken=auth_token)
        except Employee.DoesNotExist:
            raise GraphQLError("Invalid auth token")

        if not auth_token or not title or not description or not priority or not status:
            raise GraphQLError("Missing data fields")

        if not assign_student_ids and not assign_employee_ids:
            raise GraphQLError("Missing data fields")

        with transaction.atomic():
            try:
                task = Task.objects.create(
                    id=uuid.uuid4(),
                    title=title,
                    description=description,
                    priority=priority,
                    status=status,
                    due_date=due_date,
                    creator_employee=user,
                )

                if assign_student_ids:
                    for stud_id in assign_student_ids:
                        TaskAssignment.objects.create(
                            task=task,
                            student=Student.objects.get(id=stud_id),
                            status=task.status,
                        )

                if assign_employee_ids:
                    for emp_id in assign_employee_ids:
                        TaskAssignment.objects.create(
                            task=task,
                            employee=Employee.objects.get(id=emp_id),
                            status=task.status,
                        )

                all_assignments = task.assignments.all()

                assignments = [
                    AssignmentSchema(
                        id=a.id,
                        status=a.status,
                        assigned_on=a.assigned_on,
                        employee_id=a.employee.id if a.employee else None,
                        employee_name=a.employee.name if a.employee else None,
                        student_id=a.student.id if a.student else None,
                        student_name=a.student.full_name if a.student else None,
                    )
                    for a in all_assignments
                ]

                return cls(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    status=status,
                    created_by_me=True,
                    assigned_to_me=task.assignments.filter(employee=user).exists(),
                    created_at=task.created_at,
                    due_date=task.due_date,
                    assignments=assignments,
                )

            except Exception as e:
                raise GraphQLError("Server error while creating or assigning Task")

    @classmethod
    def edit_task(
            cls,
            auth_token: str,
            id: str,
            title: Optional[str] = None,
            description: Optional[str] = None,
            priority: Optional[str] = None,
            status: Optional[str] = None,
            due_date: Optional[str] = None,
            remove_student_ids: Optional[List[int]] = None,
            assign_student_ids: Optional[List[int]] = None,
            remove_employee_ids: Optional[List[int]] = None,
            assign_employee_ids: Optional[List[int]] = None,
    ) -> "TaskSchema":

        try:
            user = Employee.objects.get(authToken=auth_token)
        except Employee.DoesNotExist:
            raise GraphQLError("Invalid auth token")

        try:
            task = Task.objects.get(id=id)
        except Task.DoesNotExist:
            raise GraphQLError("No task found")

        if task.creator_employee != user:
            raise GraphQLError("Task not owned by You")

        if not any([
            title,
            description,
            priority,
            status,
            due_date,
            remove_student_ids,
            assign_student_ids,
            remove_employee_ids,
            assign_employee_ids,
        ]):
            raise GraphQLError("Please provide at least one field to edit")

        with transaction.atomic():
            try:
                fields_to_update = {}

                if title is not None:
                    fields_to_update["title"] = title

                if description is not None:
                    fields_to_update["description"] = description

                if priority is not None:
                    fields_to_update["priority"] = priority

                if status is not None:
                    fields_to_update["status"] = status

                if due_date is not None:
                    fields_to_update["due_date"] = due_date

                if fields_to_update:
                    Task.objects.filter(id=task.id).update(**fields_to_update)
                    task.refresh_from_db()

                if remove_student_ids:
                    TaskAssignment.objects.filter(
                        task=task,
                        student_id__in=remove_student_ids
                    ).delete()

                if assign_student_ids:
                    students = Student.objects.filter(id__in=assign_student_ids)
                    TaskAssignment.objects.bulk_create([
                        TaskAssignment(
                            task=task,
                            student=s,
                            status=task.status
                        ) for s in students
                    ])

                if remove_employee_ids:
                    TaskAssignment.objects.filter(
                        task=task,
                        employee_id__in=remove_employee_ids
                    ).delete()

                if assign_employee_ids:
                    employees = Employee.objects.filter(id__in=assign_employee_ids)
                    TaskAssignment.objects.bulk_create([
                        TaskAssignment(
                            task=task,
                            employee=e,
                            status=task.status
                        ) for e in employees
                    ])

                assignments = [
                    AssignmentSchema(
                        id=a.id,
                        status=a.status,
                        assigned_on=a.assigned_on,
                        employee_id=a.employee.id if a.employee else None,
                        employee_name=a.employee.name if a.employee else None,
                        student_id=a.student.id if a.student else None,
                        student_name=a.student.full_name if a.student else None,
                    )
                    for a in task.assignments.all()
                ]

                return cls(
                    id=task.id,
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    status=task.status,
                    created_by_me=True,
                    assigned_to_me=task.assignments.filter(employee=user).exists(),
                    created_at=task.created_at,
                    due_date=task.due_date,
                    assignments=assignments,
                )

            except:
                raise GraphQLError("Internal server error")

    @classmethod
    def delete_task(cls,
                    auth_token: str,
                    task_ids: List[str],
                    ) -> bool:

        if not task_ids:
            raise GraphQLError("No tasks provided to delete")

        try:
            user = Employee.objects.get(authToken=auth_token)
        except Employee.DoesNotExist:
            raise GraphQLError("Invalid auth token")

        with transaction.atomic():
            owned_tasks = Task.objects.filter(
                id__in=task_ids,
                creator_employee=user,
            )

            if owned_tasks.count() != len(task_ids):
                raise GraphQLError("You can delete only tasks created by you")

            owned_tasks.delete()

        return True


@strawberry.type
class TaskQuery:
    get_tasks: list["TaskSchema"] = strawberry.field(
        resolver=TaskSchema.get_tasks,
    )


@strawberry.type
class TaskMutation:
    create_task: TaskSchema = strawberry.field(
        resolver=TaskSchema.create_task
    )

    edit_task: TaskSchema = strawberry.field(
        resolver=TaskSchema.edit_task
    )

    delete_task: TaskSchema = strawberry.field(
        resolver=TaskSchema.delete_task
    )