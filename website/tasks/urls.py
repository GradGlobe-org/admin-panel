from django.urls import path
from . import views

urlpatterns = [
    path("my-tasks/", views.my_tasks, name="my_tasks"),
    path("create-task/", views.StudentTaskView.as_view()),  # POST only
    path("task/<uuid:task_id>/", views.StudentTaskView.as_view()),  # PUT, DELETE
]
