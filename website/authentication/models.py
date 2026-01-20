from django.db import models
import uuid
# Create your models here.

class JobRole(models.Model):
    role = models.CharField(max_length=100, verbose_name="Job Role", db_index=True)
    permissions = models.ManyToManyField('Permission', related_name='job_roles', verbose_name="Permissions", blank=True)

    class Meta:
        verbose_name = "Job Role"
        verbose_name_plural = "Job Roles"
        ordering = ['role']

    def __str__(self):
        return self.role


class Employee(models.Model):
    username = models.CharField(max_length=100, unique=True, verbose_name="Username", db_index=True)
    password = models.CharField(max_length=50, verbose_name="Password")
    name = models.CharField(max_length=100, verbose_name="Full Name", db_index=True)
    phone_number = models.CharField(max_length=12, verbose_name="Phone Number", db_index=True)
    email = models.EmailField(max_length=100, verbose_name="Email Address", db_index=True)
    job_roles = models.ManyToManyField(JobRole, verbose_name="Job Roles", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    modified_at = models.DateTimeField(auto_now=True, verbose_name="Last Modified At")
    authToken = models.UUIDField(default=uuid.uuid4, editable=False)
    is_superuser = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
        ordering = ['name']

    def __str__(self):
        return self.username

    
class LoginLog(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='login_logs',
        verbose_name="Employee"
    )
    login_at = models.DateTimeField(auto_now_add=True, verbose_name="Login Time")

    class Meta:
        verbose_name = "Login Log"
        verbose_name_plural = "Login Logs"
        ordering = ['-login_at']

    def __str__(self):
        return f"{self.employee.username if self.employee else 'Unknown'} logged in at {self.login_at}"
    
class Permission(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Permission Name", db_index=True)
    
    class Meta:
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
        return self.name