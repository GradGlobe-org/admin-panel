from django.urls import path
from .views import CreateEventView, get_all_events, delete_event

urlpatterns = [
    path("create/", CreateEventView.as_view()),
    path("get/", get_all_events),
    path("delete/<int:event_id>/", delete_event),
]
