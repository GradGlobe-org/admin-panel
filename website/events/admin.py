from django.contrib import admin
from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "event_datetime", "created_by", "created_on")
    list_filter = ("event_datetime", "created_by")
    search_fields = ("name", "description", "created_by__username")
    readonly_fields = ("created_on",)
    ordering = ("-event_datetime",)
