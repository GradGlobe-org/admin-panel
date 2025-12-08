from django.urls import path
from . import views
from .views import get_assigned_users

urlpatterns = [
    path("my-tasks/", views.my_tasks, name="my_tasks"),
    path("create-task/", views.StudentTaskView.as_view()),  # POST only
    path("task/<uuid:task_id>/",  views.StudentTaskView.as_view()),  # PUT, DELETE
    path("employee_create_task/", views.EmployeeTaskView.as_view(), name="employee_task_create"),
    path("employee_task/<uuid:task_id>/", views.EmployeeTaskView.as_view(), name="employee_task_update"),
    path("employee_task/unassign/<uuid:task_id>/", views.EmployeeTaskUnassignView.as_view(), name="employee_task_unassign"),
    path("get_assigned_users/", get_assigned_users)
]
