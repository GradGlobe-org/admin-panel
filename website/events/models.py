from django.db import models
from authentication.models import Employee


class Event(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    event_datetime = models.DateTimeField()
    link = models.URLField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    created_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, related_name="events_created"
    )
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return str(self.name)
