from django.contrib import admin
from .models import Task, TaskAssignment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "priority", "status", "created_at", "due_date")
    list_filter = ("priority", "status", "created_at", "due_date")
    search_fields = ("title", "description")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    autocomplete_fields = ("creator_employee", "creator_student")


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ("task", "get_assignee", "status", "assigned_on")
    list_filter = ("status", "assigned_on")
    search_fields = (
        "task__title",
        "employee__name",
        "student__full_name",
    )
    ordering = ("-assigned_on",)
    autocomplete_fields = ("task", "employee", "student")

    def get_assignee(self, obj):
        return obj.employee.name if obj.employee else obj.student.full_name
