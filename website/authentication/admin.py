from django.contrib import admin
from .models import JobRole, Employee

# Register your models here.

@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'role')
    search_fields = ('role',)
    ordering = ('role',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'name', 'email', 'phone_number', 'created_at', 'modified_at')
    search_fields = ('username', 'name', 'email', 'phone_number')
    list_filter = ('job_roles', 'created_at', 'modified_at')
    date_hierarchy = 'created_at'
    ordering = ('name',)
    filter_horizontal = ('job_roles',)
    readonly_fields = ('created_at', 'modified_at')

    fieldsets = (
        ('Account Information', {
            'fields': ('username', 'password')
        }),
        ('Personal Details', {
            'fields': ('name', 'phone_number', 'email')
        }),
        ('Job Details', {
            'fields': ('job_roles',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',),  # Optional: collapsible section
        }),
    )


