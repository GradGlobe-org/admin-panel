from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Employee
from website.event_bus import event_bus


@receiver(post_save, sender=Employee)
def employee_saved(sender, instance, created, **kwargs):
    action = "created" if created else "updated"
    # Capture ID now because instance might change
    emp_id = instance.id
    # Wait for DB to finish saving before notifying subscription
    transaction.on_commit(lambda: event_bus.emit("employee.events", {"action": action, "id": emp_id}))


@receiver(post_delete, sender=Employee)
def employee_deleted(sender, instance, **kwargs):
    # For delete, we send it immediately
    event_bus.emit("employee.events", {"action": "deleted", "id": instance.id})
