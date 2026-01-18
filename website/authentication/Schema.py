from .models import Employee, JobRole, Permission, LoginLog
from django.db import connection
from typing import Optional, Annotated, List
import strawberry
from strawberry.exceptions import GraphQLError
import uuid
import asyncio
from typing import AsyncGenerator
from strawberry.extensions import QueryDepthLimiter, MaxAliasesLimiter, MaxTokensLimiter

@strawberry.type
class PermissionSchema:
    id: int
    name: str = strawberry.field(description="Permission as READ WRITE DELETE UPDATE")

    @classmethod
    def get_all_permissions(cls) -> List["PermissionSchema"]:
        permissions = Permission.objects.all()
        lst = []
        for x in permissions:
            lst.append(cls(id=x.id, name=x.name))
        return lst


@strawberry.type
class JobRoleSchema:
    id: int
    role: str
    permission: Optional[list[PermissionSchema]] = strawberry.field(description="List of permissions per job role")

    @classmethod
    def get_all_job_roles(cls) -> List["JobRoleSchema"]:
        job_roles = JobRole.objects.all()
        lst = []
        for x in job_roles:
            lst2 = []
            for y in x.permissions.all():
                lst2.append(PermissionSchema(id=y.id, name=y.name))
            lst.append(cls(id=x.id, role=x.role, permission=lst2))
        return lst

    @classmethod
    def create_job_role(cls,
                        name: Annotated[str, strawberry.argument(description="Job role name")],
                        ids: Annotated[List[int], strawberry.argument(description="List of Permission ids")]
                        ) -> "JobRoleSchema":
        jobrole_obj = JobRole.objects.create(role=name)
        permission_objs = []
        for x in ids:
            try:
                perm_obj = Permission.objects.get(id=x)
            except Exception as e:
                perm_obj = None
                print(e)

            if perm_obj:
                permission_objs.append(PermissionSchema(id=perm_obj.id, name=perm_obj.name))
                jobrole_obj.permissions.add(perm_obj)
        try:
            jobrole_obj.save()
        except Exception as e:
            raise GraphQLError("Job role creation failed")
        return cls(id=jobrole_obj.id, role=name, permission=permission_objs)

    @classmethod
    def update_job_role(cls,
                        id: int,
                        updated_name: Optional[str] = None,
                        remove_permission_ids : Optional[list[int]] = None,
                        add_permission_ids : Optional[List[int]] = None
                        ) -> "JobRoleSchema":
        try:
            job_role = JobRole.objects.get(id=id)
        except Exception as e:
            raise GraphQLError("Job role does not exists")


        if remove_permission_ids:
            for x in remove_permission_ids:
                job_role.permissions.remove(x)
        if add_permission_ids:
            for x in add_permission_ids:
                job_role.permissions.add(x)

        if updated_name:
            job_role.role = updated_name

        try:
            job_role.save()
        except Exception as e:
            raise GraphQLError("Job role creation failed")

        lst_of_perm = []
        for x in job_role.permissions.all():
            lst_of_perm.append(PermissionSchema(id=x.id, name=x.name))

        return JobRoleSchema(id=job_role.id, role=job_role.role, permission=lst_of_perm)

    @classmethod
    def delete_job_role(cls,
        ids: Annotated[list[int], strawberry.argument(description="Job role ids to delete")],
        ) -> list[int]:
        lst = []
        for x in ids:
            try:
                JobRole.objects.get(id=x).delete()
                lst.append(x)
            except Exception as e:
                pass

        return lst

@strawberry.type
class EmployeeSchema:
    id: int
    username: str
    name: str
    phone_number: str
    email: str
    job_roles: Optional[List[JobRoleSchema]] = None
    created_at: str
    modified_at: str
    authToken: Optional[str] = None

    @classmethod
    def get_job_roles(cls, obj: Employee) -> Optional[List[JobRoleSchema]]:
        roles: list[JobRoleSchema] = []

        for role in obj.job_roles.all():
            permissions: list[PermissionSchema] = [
                PermissionSchema(id=p.id,name=p.name)
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

    @classmethod
    def get_employee(
        cls,
        info,
            username: Annotated[str, strawberry.argument(description="Employee username")],
            password: Annotated[Optional[str], strawberry.argument(description="Employee password")] = None,
            authtoken: Annotated[Optional[str], strawberry.argument(description="Employee auth token")] = None,
    ) -> "EmployeeSchema":

        if not password and not authtoken:
            raise GraphQLError("Please provide a password or auth token")

        try:
            employee = Employee.objects.get(username=username)
        except Employee.DoesNotExist:
            raise GraphQLError("Employee not found")

        is_authenticated = False

        if password:
            if employee.password == password:
                is_authenticated = True

        if not is_authenticated and authtoken:
            if str(employee.authToken) == authtoken:
                is_authenticated = True

        if not is_authenticated:
            raise GraphQLError("Employee authentication failed")


        LoginLog.objects.create(employee=employee)
        new_auth_token = uuid.uuid4()
        employee.authToken = new_auth_token
        employee.save()

        return cls(
            id=employee.id,
            username=employee.username,
            name=employee.name,
            phone_number=employee.phone_number,
            email=employee.email,
            job_roles=cls.get_job_roles(employee),
            created_at=str(employee.created_at),
            modified_at=str(employee.modified_at),
            authToken=str(new_auth_token)
        )

    @classmethod
    def get_all_employees(cls, page: int = 1, limit: Optional[int] = 10) -> List["EmployeeSchema"]:
        offset = (page - 1) * limit

        emp_table = Employee._meta.db_table
        role_table = JobRole._meta.db_table
        perm_table = Permission._meta.db_table

        emp_role_m2m = Employee.job_roles.through._meta.db_table
        role_perm_m2m = JobRole.permissions.through._meta.db_table

        list_employees = []

        with connection.cursor() as cursor:
            sql_emp = f"""
                        SELECT id, username, name, phone_number, email, created_at, modified_at 
                        FROM {emp_table}
                        ORDER BY name
                        LIMIT %s OFFSET %s
                    """
            cursor.execute(sql_emp, [limit, offset])

            columns = [col[0] for col in cursor.description]
            employees_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

            for emp in employees_data:
                sql_roles = f"""
                            SELECT r.id, r.role 
                            FROM {role_table} r
                            INNER JOIN {emp_role_m2m} map ON r.id = map.jobrole_id
                            WHERE map.employee_id = %s
                            ORDER BY r.role
                        """
                cursor.execute(sql_roles, [emp['id']])

                role_columns = [col[0] for col in cursor.description]
                roles_data = [dict(zip(role_columns, row)) for row in cursor.fetchall()]

                job_role_schemas = []

                for role in roles_data:
                    sql_perms = f"""
                            SELECT p.id, p.name
                            FROM {perm_table} p
                            INNER JOIN {role_perm_m2m} map ON p.id = map.permission_id
                            WHERE map.jobrole_id = %s
                        """
                    cursor.execute(sql_perms, [role['id']])

                    perm_columns = [col[0] for col in cursor.description]
                    perms_data = [dict(zip(perm_columns, row)) for row in cursor.fetchall()]

                    permission_schemas = [
                        PermissionSchema(id=p['id'], name=p['name'])
                        for p in perms_data
                    ]

                    job_role_schemas.append(
                        JobRoleSchema(
                            id=role['id'],
                            role=role['role'],
                            permission=permission_schemas
                        )
                    )

                list_employees.append(cls(
                    id=emp["id"],
                    username=emp['username'],
                    name=emp['name'],
                    phone_number=emp['phone_number'],
                    email=emp['email'],
                    job_roles=job_role_schemas,
                    created_at=str(emp['created_at']),
                    modified_at=str(emp['modified_at'])
                ))

        return list_employees

    @classmethod
    def create_employee(cls,
        username: str,
        name: str,
        phone_number: str,
        email: str,
        job_roles_id : Optional[list[int]] = None,
        ) -> "EmployeeSchema":

        emp = Employee(username=username, name=name, phone_number=phone_number, email=email, authToken=uuid.uuid4())
        if job_roles_id:
            for x in job_roles_id:
                emp.job_roles.add(x)

        try:
            emp.save()
        except Exception as e:
            raise GraphQLError("Failed to create employee")

        return cls(id=emp.id,
                   username=username,
                   name=name,
                   phone_number=phone_number,
                   email=email,
                   authToken=emp.authToken,
                   job_roles=cls.get_job_roles(emp),
                   created_at=str(emp.created_at),
                   modified_at=str(emp.modified_at))

    @classmethod
    def update_employee(cls,
                        updated_username: Optional[str] = None,
                        updated_name: Optional[str] = None,
                        updated_phone_number: Optional[str] = None,
                        updated_email: Optional[str] = None,
                        remove_job_role_ids: Optional[list[int]] = None,
                        add_job_role_ids: Optional[list[int]] = None,
                        id: int = strawberry.field(description="Employee id to update"),
                        ) -> "EmployeeSchema":
        try:
            emp = Employee.objects.get(id=id)
        except Exception as e:
            raise GraphQLError("Employee not found")

        if updated_username:
            emp.username = updated_username
        if updated_name:
            emp.name = updated_name
        if updated_phone_number:
            emp.phone_number = updated_phone_number
        if updated_email:
            emp.email = updated_email

        if remove_job_role_ids:
            for x in remove_job_role_ids:
                emp.job_roles.remove(x)

        if add_job_role_ids:
            for x in add_job_role_ids:
                emp.job_roles.add(x)
        try:
            emp.save()
        except Exception as e:
            raise GraphQLError("Failed to Update employee")
        return cls(id=emp.id,
                   username=emp.username,
                   name=emp.name,
                   phone_number=emp.phone_number,
                   email=emp.email,
                   authToken=None,
                   job_roles=cls.get_job_roles(emp),
                   created_at=str(emp.created_at),
                   modified_at=str(emp.modified_at)
                   )

    @classmethod
    def delete_employee(cls, emp_id: int) -> bool:
        try:
            emp = Employee.objects.get(id=emp_id)
        except Exception as e:
            raise GraphQLError("Employee not found")
        try:
            emp.delete()
            return True
        except Exception as e:
            raise GraphQLError("Failed to delete employee")






@strawberry.type
class EmployeeQuery:
    employee: EmployeeSchema = strawberry.field(
        resolver=EmployeeSchema.get_employee
    )
    all_employee: list[EmployeeSchema] = strawberry.field(
        resolver=EmployeeSchema.get_all_employees
    )
    all_employee_permissions: list[PermissionSchema] = strawberry.field(
        resolver=PermissionSchema.get_all_permissions
    )
    all_employee_job_roles : list[JobRoleSchema] = strawberry.field(
        resolver=JobRoleSchema.get_all_job_roles
    )
    get_job_role: list[JobRoleSchema]= strawberry.field(
        resolver=JobRoleSchema.get_all_job_roles
    )

@strawberry.type
class EmployeeMutation:
    # Job Role
    create_job_role: JobRoleSchema = strawberry.field(resolver=JobRoleSchema.create_job_role)
    update_job_role: JobRoleSchema = strawberry.field(resolver=JobRoleSchema.update_job_role)
    delete_job_role: Annotated[list[int], "Ids That were successfully deleted"] = strawberry.field(resolver=JobRoleSchema.delete_job_role)

    # Employee
    create_employee: EmployeeSchema = strawberry.field(resolver=EmployeeSchema.create_employee)
    update_employee: EmployeeSchema = strawberry.field(resolver=EmployeeSchema.update_employee)
    delete_employee: bool = strawberry.field(resolver=EmployeeSchema.delete_employee)

@strawberry.type
class EmployeeSubscription:
    @strawberry.subscription
    async def hello(self) -> AsyncGenerator[str, None]:
        while True:
            yield "Hello"
            await asyncio.sleep(1)


employee_schema = strawberry.Schema(query=EmployeeQuery, mutation=EmployeeMutation, subscription=EmployeeSubscription,
                                    extensions=[QueryDepthLimiter(max_depth=3), MaxAliasesLimiter(max_alias_count=10),
                                                MaxTokensLimiter(max_token_count=1000)]

                                    )