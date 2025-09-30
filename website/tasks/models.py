from django.db import models
from authentication.models import Employee
from student.models import Student
from django.utils import timezone
from uuid import uuid4


class Task(models.Model):
    PRIORITY_CHOICES = [
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]

    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("inprogress", "In Progress"),
        ("overdue", "Overdue"),
        ("completed", "Completed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    # This is the **overall status** of the task
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")

    creator_employee = models.ForeignKey(
        Employee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_tasks",
        help_text="Employee who created this task, if applicable",
    )
    creator_student = models.ForeignKey(
        Student,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_tasks",
        help_text="Student who created this task, if applicable",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return f"{self.title} ({self.priority} - {self.status})"

    def mark_overdue_if_needed(self):
        """Automatically mark task as overdue if past due_date and not completed"""
        if (
            self.due_date
            and self.due_date < timezone.now()
            and self.status not in ["completed", "overdue"]
        ):
            self.status = "overdue"
            self.save(update_fields=["status"])


class TaskAssignment(models.Model):
    STATUS_CHOICES = [
        ("todo", "To Do"),
        ("inprogress", "In Progress"),
        ("completed", "Completed"),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="assignments")
    employee = models.ForeignKey(
        Employee, null=True, blank=True, on_delete=models.CASCADE, related_name="tasks"
    )
    student = models.ForeignKey(
        Student, null=True, blank=True, on_delete=models.CASCADE, related_name="tasks"
    )
    assigned_on = models.DateTimeField(default=timezone.now)
    # Per-assignee status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="todo")

    class Meta:
        verbose_name = "Task Assignment"
        verbose_name_plural = "Task Assignments"
        constraints = [
            models.UniqueConstraint(
                fields=["task", "employee", "student"], name="unique_task_assignment"
            )
        ]

    def __str__(self):
        target = self.employee.name if self.employee else self.student.full_name
        return f"Task '{self.task.title}' → {target} [{self.status}]"
