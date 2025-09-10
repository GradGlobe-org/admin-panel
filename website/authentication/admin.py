from django.contrib import admin
from .models import JobRole, Employee, LoginLog, Permission


@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'role')
    search_fields = ('role',)
    list_display_links = ('role',)
    ordering = ('role',)
    filter_horizontal = ('permissions',)

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


@admin.register(LoginLog)
class LoginLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'login_at')
    list_filter = ('employee', 'login_at')
    search_fields = ('employee__username', 'employee__name')
    date_hierarchy = 'login_at'
    ordering = ('-login_at',)
    readonly_fields = ('employee', 'login_at')

    def has_add_permission(self, request):
        # Prevent adding logs via admin
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent editing logs
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting logs
        return False

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
