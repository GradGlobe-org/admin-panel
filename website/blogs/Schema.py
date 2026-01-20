import strawberry
from typing import Optional, Annotated, List, Any, Awaitable

from django.core.exceptions import ObjectDoesNotExist

from authentication.models import Employee
from .models import Post
from datetime import datetime
from django.db import connection
from strawberry.scalars import JSON
from strawberry.exceptions import GraphQLError

import uuid
from website.utils import EmployeeAuthorization
from django.shortcuts import get_object_or_404


@strawberry.type
class PostSchema(EmployeeAuthorization):
    id: int
    title: str
    content: str
    featured_image: Optional[str] = None
    author: JSON
    created_at: datetime
    modified_at: datetime
    status: str
    meta_keyword: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    view_count: int

    @classmethod
    # @strawberry.field(permission_classes=[EmployeeAuthentication])
    def get_all_blogs(cls, auth_token: str, page: int, limit: Optional[int] = 20) -> List["PostSchema"]:
        try:
            auth_token = uuid.UUID(auth_token)
            employee = EmployeeAuthorization.check_employee_token(auth_token)
        except Exception as e:
            raise GraphQLError("Failed to authenticate")

        has_permission = EmployeeAuthorization.check_employee_permission(
            employee.id, ["Blog_view"]
        )

        if not employee.is_superuser and not has_permission:
            raise GraphQLError("You do not have permission to do this")

        offset = (page - 1) * limit

        blog_table = Post._meta.db_table
        employee_table = Employee._meta.db_table
        blog_lst = []
        with connection.cursor() as cursor:
            blog_sql = f"""
            SELECT b.id, b.title, SUBSTR(b.content, 1, 1000) AS content, b.featured_image, b.created_at, b.modified_at,
            b.status, b.meta_keyword, b.meta_description, b.slug, b.view_count,
            e.id as author_id, e.name as author_name
            FROM {blog_table} b
            JOIN {employee_table} e on b.author_id = e.id 
            ORDER BY b.created_at DESC
            LIMIT %s OFFSET %s
            """

            cursor.execute(blog_sql, [limit, offset])

            # print(rows)
            # print(cursor.description)

            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            for blog in rows:
                blog_lst.append(cls(
                    id=blog["id"],
                    title=blog["title"],
                    content=blog["content"],
                    featured_image=blog["featured_image"],
                    author={
                        "id": blog["author_id"],
                        "name": blog["author_name"],
                    },
                    created_at=blog["created_at"],
                    modified_at=blog["modified_at"],
                    status=blog["status"],
                    meta_keyword=None,
                    meta_description=None,
                    slug=blog["slug"],
                    view_count=blog["view_count"],
                ))

        return blog_lst

    @classmethod
    def get_detailed_blog(cls, auth_token:str, blog_id: int) -> "PostSchema":
        try:
            auth_token=uuid.UUID(auth_token)
            employee = EmployeeAuthorization.check_employee_token(auth_token)
        except Exception as e:
            raise GraphQLError("Failed to authenticate")

        has_permission = EmployeeAuthorization.check_employee_permission(
            employee.id, ["Blog_view"]
        )

        if not employee.is_superuser and not has_permission:
            raise GraphQLError("You do not have permission to do this")

        try:
            blog = Post.objects.get(id=blog_id)
        except ObjectDoesNotExist:
            raise GraphQLError("This blog does not exist")
        except Exception:
            raise GraphQLError("Error getting blog")

        return(cls(
            id=blog.id,
            title=blog.title,
            content=blog.content,
            featured_image=blog.featured_image,
            author={
                "id":blog.author.id,
                "name":blog.author.name
            },
            created_at=blog.created_at,
            modified_at=blog.modified_at,
            status=blog.status,
            meta_keyword=blog.meta_keyword,
            meta_description=blog.meta_description,
            slug=blog.slug,
            view_count=blog.view_count
        ))

    @classmethod
    def get_personal_blogs(cls, auth_token:str, page:int, limit: Optional[int] = 20) -> List["PostSchema"]:
        try:
            auth_token=uuid.UUID(auth_token)
            employee = EmployeeAuthorization.check_employee_token(auth_token)
        except Exception as e:
            raise GraphQLError("Failed to authenticate")

        has_permission = EmployeeAuthorization.check_employee_permission(
            employee.id, ["Blog_view"]
        )

        if not employee.is_superuser and not has_permission:
            raise GraphQLError("You do not have permission to do this")

        offset = (page - 1) * limit

        blog_table = Post._meta.db_table
        employee_table = Employee._meta.db_table
        blog_lst = []
        with connection.cursor() as cursor:
            blog_sql = f"""
               SELECT 
                b.id,
                b.title,
                SUBSTR(b.content, 1, 1000) AS content,
                b.featured_image,
                b.created_at,
                b.modified_at,
                b.status,
                b.meta_keyword,
                b.meta_description,
                b.slug,
                b.view_count,
                e.id AS author_id,
                e.name AS author_name
            FROM {blog_table} b
            JOIN {employee_table} e 
                ON b.author_id = e.id
            WHERE e.id = %s
            ORDER BY b.created_at DESC
            LIMIT %s OFFSET %s;
               """

            cursor.execute(blog_sql, [employee.id, limit, offset])

            # print(rows)
            # print(cursor.description)

            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

            for blog in rows:
                blog_lst.append(cls(
                    id=blog["id"],
                    title=blog["title"],
                    content=blog["content"],
                    featured_image=blog["featured_image"],
                    author={
                        "id": blog["author_id"],
                        "name": blog["author_name"],
                    },
                    created_at=blog["created_at"],
                    modified_at=blog["modified_at"],
                    status=blog["status"],
                    meta_keyword=None,
                    meta_description=None,
                    slug=blog["slug"],
                    view_count=blog["view_count"],
                ))

        return blog_lst

    @classmethod
    def search_blog(cls,
                    query:Annotated[str, strawberry.argument(description="Enter search query")],
                    auth_token:str
                    ) -> List["PostSchema"]:
        try:
            auth_token=uuid.UUID(auth_token)
            employee = EmployeeAuthorization.check_employee_token(auth_token)
        except Exception as e:
            raise GraphQLError("Failed to authenticate")

        has_permission = EmployeeAuthorization.check_employee_permission(
            employee.id, ["Blog_view"]
        )

        if not employee.is_superuser and not has_permission:
            raise GraphQLError("You do not have permission to do this")

        blog_table = Post._meta.db_table
        employee_table = Employee._meta.db_table

        with connection.cursor() as cursor:
            search_sql=f"""
                SELECT 
                    b.id,
                    b.title,
                    SUBSTR(b.content, 1, 1000) AS content,
                    b.featured_image,
                    b.created_at,
                    b.modified_at,
                    b.status,
                    b.meta_keyword,
                    b.meta_description,
                    b.slug,
                    b.view_count,
                    e.id AS author_id,
                    e.name AS author_name
                FROM {blog_table} b
                JOIN {employee_table} e
                    ON b.author_id = e.id
                WHERE
                    CONCAT_WS(
                        ' ',
                        b.title,
                        b.meta_keyword,
                        b.meta_description,
                        e.name
                    ) ILIKE %s
                ORDER BY b.created_at DESC;
                """

            search_term = f"%{query}%"
            cursor.execute(search_sql, [search_term])

            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
            blog_lst = []
            for blog in rows:
                blog_lst.append(cls(
                    id=blog["id"],
                    title=blog["title"],
                    content=blog["content"],
                    featured_image=blog["featured_image"],
                    author={
                        "id": blog["author_id"],
                        "name": blog["author_name"],
                    },
                    created_at=blog["created_at"],
                    modified_at=blog["modified_at"],
                    status=blog["status"],
                    meta_keyword=None,
                    meta_description=None,
                    slug=blog["slug"],
                    view_count=blog["view_count"],
                ))

        return blog_lst

    @classmethod
    def create_blog(cls,
                    auth_token: str,
                    title: str,
                    content: str,
                    featured_image: str,
                    status: str,
                    meta_keyword: Optional[str] = None,
                    meta_description: Optional[str] = None,
                    slug: Optional[str] = None,
                    ) -> "PostSchema":
        try:
            auth_token = uuid.UUID(auth_token)
            employee = EmployeeAuthorization.check_employee_token(auth_token)
        except Exception as e:
            raise GraphQLError("Failed to authenticate")

        has_permission = EmployeeAuthorization.check_employee_permission(
            employee.id, ["Blog_create"]
        )

        if not employee.is_superuser and not has_permission:
            raise GraphQLError("You do not have permission to do this")

        if title == Post.objects.get(title=title).title:
            raise GraphQLError("Blog with this title already exists")

        blog = Post.objects.create(
            title=title,
            content=content,
            featured_image=featured_image,
            author_id=employee.id,
            status=status,
            meta_keyword=meta_keyword,
            meta_description=meta_description,
            slug=slug,
        )

        return cls(
            id=blog.id,
            title=blog.title,
            content=blog.content,
            featured_image=blog.featured_image,
            author={
                "id": blog.author.id,
                "name": blog.author.name,
            },
            created_at=blog.created_at,
            modified_at=blog.modified_at,
            status=blog.status,
            meta_keyword=blog.meta_keyword,
            meta_description=blog.meta_description,
            slug=blog.slug,
            view_count=blog.view_count,
        )

    @classmethod
    def update_blog(cls,
                    auth_token: str,
                    id: int,
                    updated_title: Optional[str] = None,
                    updated_content: Optional[str] = None,
                    updated_image: Optional[str] = None,
                    updated_status: Optional[str] = None,
                    updated_meta_keyword: Optional[str] = None,
                    updated_meta_description: Optional[str] = None,
                    updated_slug: Optional[str] = None,
                    ) -> "PostSchema":

        try:
            auth_token = uuid.UUID(auth_token)
            employee = EmployeeAuthorization.check_employee_token(auth_token)
        except Exception as e:
            raise GraphQLError("Failed to authenticate")

        has_permission = EmployeeAuthorization.check_employee_permission(
            employee.id, ["Blog_update"]
        )

        if not employee.is_superuser and not has_permission:
            raise GraphQLError("You do not have permission to do this")

        blog = Post.objects.get(id=id)

        if not (employee.is_superuser or blog.author_id == employee.id):
            raise GraphQLError("You did not created the blog")

        try:
            blog = Post.objects.get(id=id)
        except Post.DoesNotExist:
            raise GraphQLError("Blog does not exist")
        except Exception as e:
            raise GraphQLError("Failed to get Blog")

        if updated_title:
            blog.title = updated_title
        if updated_content:
            blog.content = updated_content
        if updated_image:
            blog.featured_image = updated_image
        if updated_status:
            blog.status = updated_status
        if updated_meta_keyword:
            blog.meta_keyword = updated_meta_keyword
        if updated_meta_description:
            blog.meta_description = updated_meta_description
        if updated_slug:
            blog.slug = updated_slug

        try:
            blog.save()
        except Exception as e:
            raise GraphQLError("Failed to Update Blog")

        return cls(
            id=blog.id,
            title=blog.title,
            content=blog.content,
            featured_image=blog.featured_image,
            author={
                "id": blog.author.id,
                "name": blog.author.name,
            },
            created_at=blog.created_at,
            modified_at=blog.modified_at,
            status=blog.status,
            meta_keyword=blog.meta_keyword,
            meta_description=blog.meta_description,
            slug=blog.slug,
            view_count=blog.view_count,
        )

    @classmethod
    def delete_blog(cls, auth_token: str, id: int) -> bool:
        try:
            auth_token = uuid.UUID(auth_token)
            employee = EmployeeAuthorization.check_employee_token(auth_token)
        except Exception as e:
            raise GraphQLError("Failed to authenticate")

        has_permission = EmployeeAuthorization.check_employee_permission(
            employee.id, ["Blog_delete"]
        )

        if not employee.is_superuser and not has_permission:
            raise GraphQLError("You do not have permission to do this")

        try:
            blog = Post.objects.get(id=id)
        except Post.DoesNotExist:
            raise GraphQLError("Blog does not exist")
        except Exception as e:
            raise GraphQLError("Error fetching blog")

        if not (employee.is_superuser or blog.author_id == employee.id):
            raise GraphQLError("You did not created this blog")

        try:
            blog.delete()
            return True
        except Exception as e:
            raise GraphQLError("Failed to Delete Blog")


@strawberry.type
class BlogQuery:
    get_all_blog: list[PostSchema] = strawberry.field(
        resolver=PostSchema.get_all_blogs
    )
    get_detailed_blog: PostSchema = strawberry.field(
        resolver=PostSchema.get_detailed_blog
    )
    get_personal_blogs: list[PostSchema] = strawberry.field(
        resolver=PostSchema.get_personal_blogs
    )
    search_blogs: list[PostSchema] = strawberry.field(
        resolver=PostSchema.search_blog
    )


@strawberry.type
class BlogMutation:
    create_blog: PostSchema = strawberry.field(
        resolver=PostSchema.create_blog
    )
    update_blog: PostSchema = strawberry.field(
        resolver=PostSchema.update_blog
    )
    delete_blog: bool = strawberry.field(
        resolver=PostSchema.delete_blog
    )
