from .models import Employee, JobRole, Permission, LoginLog
from django.db import transaction
from django.db import connection
from typing import Optional, Annotated, List
import strawberry
from strawberry.exceptions import GraphQLError
import uuid
import asyncio
from typing import AsyncGenerator
from .Utils import SchemaMixin

"""
Heavily Optimized by AI 
- by the man who saw (N+1)*2 DB Calls
"""


@strawberry.type
class PermissionSchema(SchemaMixin):
    id: int
    name: str = strawberry.field(description="Permission as READ WRITE DELETE UPDATE")

    @classmethod
    def get_all_permissions(cls, authkey: str) -> list["PermissionSchema"]:
        try:
            emp = cls.get_employee(authkey)
            if not emp.is_superuser:
                raise GraphQLError("Not permitted")
            permissions = Permission.objects.only("id", "name")
            return [
                PermissionSchema(id=p.id, name=p.name)
                for p in permissions
            ]
        except:
            raise GraphQLError("Internal Server Error")


@strawberry.type
class JobRoleSchema(SchemaMixin):
    id: int
    role: str = strawberry.field(description="Name of the job role")
    permission: Optional[list[PermissionSchema]] = strawberry.field(description="List of permissions per job role")

    @classmethod
    def get_all_job_roles(cls, authkey: str) -> list["JobRoleSchema"]:
        try:
            emp = cls.get_employee(authkey)
            if not emp.is_superuser:
                raise GraphQLError("Not permitted")
            job_roles = (
                JobRole.objects
                .prefetch_related("permissions")
                .all()
            )
            result: list[JobRoleSchema] = []
            for role in job_roles:
                permissions = [
                    PermissionSchema(id=p.id, name=p.name)
                    for p in role.permissions.all()
                ]
                result.append(
                    JobRoleSchema(
                        id=role.id,
                        role=role.role,
                        permission=permissions
                    )
                )
            return result
        except:
            raise GraphQLError("Internal Server Error")

    @classmethod
    def create_job_role(
            cls,
            name: Annotated[str, strawberry.argument(description="Job role name")],
            ids: Annotated[list[int], strawberry.argument(description="List of Permission ids")],
            authkey: str
    ) -> "JobRoleSchema":
        try:

            emp = cls.get_employee(authkey)
            if not emp.is_superuser:
                raise GraphQLError("Not permitted")
            if not name.strip():
                raise GraphQLError("Job role name cannot be empty")
            permission_ids = ids or []
            permissions = list(
                Permission.objects
                .filter(id__in=permission_ids)
            )
            existing_ids = {p.id for p in permissions}
            missing_ids = set(permission_ids) - existing_ids
            if missing_ids:
                raise GraphQLError(f"Invalid permission IDs: {missing_ids}")
            with transaction.atomic():
                job_role = JobRole.objects.create(role=name)
                if permissions:
                    job_role.permissions.add(*permissions)
            permission_schemas = [
                PermissionSchema(id=p.id, name=p.name)
                for p in permissions
            ]
            return JobRoleSchema(
                id=job_role.id,
                role=job_role.role,
                permission=permission_schemas
            )
        except:
            raise GraphQLError("Internal Server Error")

    @classmethod
    def update_job_role(
            cls,
            id: int,
            authkey: str,
            updated_name: Optional[str] = None,
            remove_permission_ids: Optional[list[int]] = None,
            add_permission_ids: Optional[list[int]] = None,
    ) -> "JobRoleSchema":
        try:
            emp = cls.get_employee(authkey)
            if not emp.is_superuser:
                raise GraphQLError("Not permitted")
            try:
                job_role = JobRole.objects.prefetch_related("permissions").get(id=id)
            except JobRole.DoesNotExist:
                raise GraphQLError("Job role does not exist")
            with transaction.atomic():
                # ---- update name ----
                if updated_name is not None:
                    job_role.role = updated_name
                    job_role.save(update_fields=["role"])
                # ---- permissions logic ----
                if remove_permission_ids:
                    job_role.permissions.remove(*remove_permission_ids)
                if add_permission_ids:
                    existing_perm_ids = set(
                        Permission.objects
                        .filter(id__in=add_permission_ids)
                        .values_list("id", flat=True)
                    )
                    missing = set(add_permission_ids) - existing_perm_ids
                    if missing:
                        raise GraphQLError(f"Invalid permission IDs: {missing}")
                    job_role.permissions.add(*existing_perm_ids)
            permissions = [
                PermissionSchema(id=p.id, name=p.name)
                for p in job_role.permissions.all()
            ]
            return JobRoleSchema(
                id=job_role.id,
                role=job_role.role,
                permission=permissions
            )
        except:
            raise GraphQLError("Internal Server Error")

    @classmethod
    def delete_job_role(
            cls,
            ids: Annotated[list[int], strawberry.argument(description="Job role ids to delete")],
            authkey: str
    ) -> list[int]:

        emp = cls.get_employee(authkey)

        if not emp.is_superuser:
            raise GraphQLError("Not permitted")

        if not ids:
            return []

        with transaction.atomic():
            # Fetch only existing IDs
            existing_ids = list(
                JobRole.objects
                .filter(id__in=ids)
                .values_list("id", flat=True)
            )

            if not existing_ids:
                return []

            deleted_count, _ = (
                JobRole.objects
                .filter(id__in=existing_ids)
                .delete()
            )

        return existing_ids


@strawberry.type
class EmployeeSchema(SchemaMixin):
    id: int
    username: str
    name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    job_roles: Optional[List[JobRoleSchema]] = None
    created_at: Optional[str] = None
    modified_at: Optional[str] = None
    authToken: Optional[str] = None

    @classmethod
    def get_job_roles(cls, obj: Employee) -> list[JobRoleSchema]:
        try:
            roles = []
            job_roles = (
                obj.job_roles
                .prefetch_related("permissions")
                .all()
            )
            for role in job_roles:
                permissions = [
                    PermissionSchema(id=p.id, name=p.name)
                    for p in role.permissions.all()
                ]
                roles.append(
                    JobRoleSchema(
                        id=role.id,
                        role=role.role,
                        permission=permissions
                    )
                )
            return roles
        except Exception:
            raise GraphQLError("Internal Server Error")

    @classmethod
    def get_employee_login(
            cls,
            info,
            username: str,
            password: Optional[str] = None,
            authtoken: Optional[str] = None,
    ) -> "EmployeeSchema":

        try:
            if not password and not authtoken:
                raise GraphQLError("Please provide password or auth token")
            employee = Employee.objects.prefetch_related(
                "job_roles__permissions"
            ).get(username=username)
            authenticated = False
            if password and employee.password == password:
                authenticated = True
            if authtoken and str(employee.authToken) == authtoken:
                authenticated = True
            if not authenticated:
                raise GraphQLError("Authentication failed")
            with transaction.atomic():
                LoginLog.objects.create(employee=employee)
                employee.authToken = uuid.uuid4()
                employee.save(update_fields=["authToken"])
            return cls(
                id=employee.id,
                username=employee.username,
                name=employee.name,
                phone_number=employee.phone_number,
                email=employee.email,
                job_roles=cls.get_job_roles(employee),
                created_at=str(employee.created_at),
                modified_at=str(employee.modified_at),
                authToken=str(employee.authToken)
            )
        except Employee.DoesNotExist:
            raise GraphQLError("Employee not found")
        except Exception:
            raise GraphQLError("Internal Server Error")

    @classmethod
    def get_all_employees(
            cls,
            authkey: str,
            page: int = 1,
            limit: Optional[int] = 10,
    ) -> list["EmployeeSchema"]:

        offset = (page - 1) * limit
        emp = cls.get_employee(authkey)
        if not emp:
            raise GraphQLError("Employee not found")
        is_super = emp.is_superuser if authkey else False
        employees = Employee.objects.prefetch_related(
            "job_roles__permissions"
        ).order_by("name")[offset:offset + limit]
        result = []
        for e in employees:
            roles = cls.get_job_roles(e) if is_super else None
            result.append(
                cls(
                    id=e.id,
                    username=e.username,
                    name=e.name,
                    phone_number=e.phone_number if is_super else None,
                    email=e.email if is_super else None,
                    job_roles=roles,
                    created_at=str(e.created_at) if is_super else None,
                    modified_at=str(e.modified_at) if is_super else None,
                )
            )
        return result

    @classmethod
    def create_employee(
            cls,
            username: str,
            name: str,
            phone_number: str,
            email: str,
            authkey: str,
            job_roles_id: Optional[list[int]] = None,
    ) -> "EmployeeSchema":
        try:
            admin = cls.get_employee(authkey)
            if not admin.is_superuser:
                raise GraphQLError("Not permitted")
            with transaction.atomic():
                employee = Employee.objects.create(
                    username=username,
                    name=name,
                    phone_number=phone_number,
                    email=email,
                    authToken=uuid.uuid4()
                )
                if job_roles_id:
                    employee.job_roles.add(*job_roles_id)
            return cls(
                id=employee.id,
                username=employee.username,
                name=employee.name,
                phone_number=employee.phone_number,
                email=employee.email,
                job_roles=cls.get_job_roles(employee),
                created_at=str(employee.created_at),
                modified_at=str(employee.modified_at),
                authToken=str(employee.authToken)
            )
        except GraphQLError:
            raise
        except Exception:
            raise GraphQLError("Failed to create employee")

    @classmethod
    def update_employee(
            cls,
            authkey: str,
            id: int,
            updated_username: Optional[str] = None,
            updated_name: Optional[str] = None,
            updated_phone_number: Optional[str] = None,
            updated_email: Optional[str] = None,
            remove_job_role_ids: Optional[list[int]] = None,
            add_job_role_ids: Optional[list[int]] = None,
    ) -> "EmployeeSchema":
        try:
            admin = cls.get_employee(authkey)
            if not admin.is_superuser:
                raise GraphQLError("Not permitted")
            employee = Employee.objects.get(id=id)
            if updated_username:
                employee.username = updated_username
            if updated_name:
                employee.name = updated_name
            if updated_phone_number:
                employee.phone_number = updated_phone_number
            if updated_email:
                employee.email = updated_email
            with transaction.atomic():
                employee.save()
                if remove_job_role_ids:
                    employee.job_roles.remove(*remove_job_role_ids)
                if add_job_role_ids:
                    employee.job_roles.add(*add_job_role_ids)

            return cls(
                id=employee.id,
                username=employee.username,
                name=employee.name,
                phone_number=employee.phone_number,
                email=employee.email,
                job_roles=cls.get_job_roles(employee),
                created_at=str(employee.created_at),
                modified_at=str(employee.modified_at)
            )

        except GraphQLError:
            raise
        except Employee.DoesNotExist:
            raise GraphQLError("Employee not found")
        except Exception:
            raise GraphQLError("Internal Server Error")

    @classmethod
    def delete_employee(cls, authkey: str, emp_id: int) -> bool:
        try:
            admin = cls.get_employee(authkey)
            if not admin.is_superuser:
                raise GraphQLError("Not permitted")
            Employee.objects.filter(id=emp_id).delete()
            return True
        except GraphQLError:
            raise
        except Exception:
            raise GraphQLError("Failed to delete employee")


@strawberry.type
class EmployeeQuery:
    employee: EmployeeSchema = strawberry.field(
        resolver=EmployeeSchema.get_employee_login
    )
    all_employee: list[EmployeeSchema] = strawberry.field(
        resolver=EmployeeSchema.get_all_employees
    )
    all_employee_permissions: list[PermissionSchema] = strawberry.field(
        resolver=PermissionSchema.get_all_permissions
    )
    all_employee_job_roles: list[JobRoleSchema] = strawberry.field(
        resolver=JobRoleSchema.get_all_job_roles
    )


@strawberry.type
class EmployeeMutation:
    # Job Role
    create_job_role: JobRoleSchema = strawberry.field(resolver=JobRoleSchema.create_job_role)
    update_job_role: JobRoleSchema = strawberry.field(resolver=JobRoleSchema.update_job_role)
    delete_job_role: list[int] = strawberry.field(
        resolver=JobRoleSchema.delete_job_role, description="Returns The IDs that were successfully deleted")

    # Employee
    create_employee: EmployeeSchema = strawberry.field(resolver=EmployeeSchema.create_employee)
    update_employee: EmployeeSchema = strawberry.field(resolver=EmployeeSchema.update_employee)
    delete_employee: bool = strawberry.field(resolver=EmployeeSchema.delete_employee)


@strawberry.type
class EmployeeSubscription:
    @strawberry.subscription
    async def hello_world_stream(self, iterations: int = 5) -> AsyncGenerator[str, None]:
        for i in range(iterations):
            yield f"Update {i + 1}"
            await asyncio.sleep(1)
