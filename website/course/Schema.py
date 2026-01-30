from typing import Optional, List
import strawberry
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, transaction, IntegrityError
from graphql import GraphQLError

from authentication.Utils import SchemaMixin
from course.models import Course
import datetime

from university.models import university


@strawberry.type
class CourseSchema(SchemaMixin):
    id: int
    university_id : Optional[int] = None
    university_name : Optional[str] = None
    program_name: Optional[str] = None
    program_level: Optional[str] = None
    duration_in_years: Optional[int] = None
    next_intake: Optional[datetime.date] = None
    about: Optional[str] = None
    start_date: Optional[datetime.date] = None
    submission_deadline: Optional[datetime.date] = None
    offshore_onshore_deadline: Optional[datetime.date] = None
    brochure_url: Optional[str] = None
    tution_fees: Optional[int] = None

    @classmethod
    def course(cls,
               auth_token: str,
               course_id: int,
               ) -> "CourseSchema":

        emp = cls.get_employee(auth_token)
        if not emp:
            raise GraphQLError("Unauthorized")
        has_permission = emp.job_roles.filter(
            permissions__name="course_view"
        ).exists()
        if not has_permission and not emp.is_superuser:
            raise GraphQLError("You do not have permission to view course")

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            raise GraphQLError("Course does not exist")
        except:
            raise GraphQLError("Error while fetching course data")

        try:
            return cls(
                id=course.id,
                university_id=course.university_id,
                university_name=course.university.name,
                program_name=course.program_name,
                program_level=course.program_level,
                duration_in_years=course.duration_in_years,
                next_intake=course.next_intake,
                about=course.about,
                start_date=course.start_date,
                submission_deadline=course.submission_deadline,
                offshore_onshore_deadline=course.offshore_onshore_deadline,
                brochure_url=course.brochure_url,
                tution_fees=course.tution_fees,
            )
        except:
            raise GraphQLError("Error while fetching course data")


    @classmethod
    def add_course(cls,
                   auth_token:str,
                    university_id : int,
                    program_name: str,
                    program_level: str,
                    duration_in_years: int,
                    next_intake: datetime.date,
                    about: str,
                    start_date: datetime.date,
                    submission_deadline: datetime.date,
                    offshore_onshore_deadline: datetime.date,
                    brochure_url: str,
                    tution_fees: int,
                   ) -> "CourseSchema":

        emp = cls.get_employee(auth_token)
        if not emp:
            raise GraphQLError("Unauthorized")
        has_permission = emp.job_roles.filter(
            permissions__name="course_create"
        ).exists()
        if not has_permission and not emp.is_superuser:
            raise GraphQLError("You do not have permission to add courses")

        try:
            uni = university.objects.get(id=university_id)
        except ObjectDoesNotExist:
            raise GraphQLError("University not found")
        program_exists = Course.objects.filter(
            university_id=university_id,
            program_name__iexact=program_name.strip(),
        ).exists()
        if program_exists:
            raise GraphQLError(
                "A course with this program name already exists for this university"
            )

        valid_levels = {k for k, _ in Course.PROGRAM_LEVEL_CHOICES}
        level = program_level.lower()

        if level not in valid_levels:
            raise GraphQLError(
                f"Invalid program level. Allowed values: {', '.join(valid_levels)}"
            )

        try:
            with transaction.atomic():
                course = Course.objects.create(
                    university=uni,
                    program_name=program_name.strip(),
                    program_level=program_level,
                    duration_in_years=duration_in_years,
                    next_intake=next_intake,
                    about=about,
                    start_date=start_date,
                    submission_deadline=submission_deadline,
                    offshore_onshore_deadline=offshore_onshore_deadline,
                    brochure_url=brochure_url,
                    tution_fees=tution_fees,
                )
        except Exception as e:
            raise GraphQLError(f"Failed to create course: {str(e)}")

        return CourseSchema(
            id=course.id,
            university_id=course.university_id,
            university_name=course.university.name,
            program_name=course.program_name,
            program_level=course.program_level,
            duration_in_years=course.duration_in_years,
            next_intake=course.next_intake,
            about=course.about,
            start_date=course.start_date,
            submission_deadline=course.submission_deadline,
            offshore_onshore_deadline=course.offshore_onshore_deadline,
            brochure_url=course.brochure_url,
            tution_fees=course.tution_fees,
        )

    @classmethod
    def edit_course(
            cls,
            auth_token: str,
            course_id: int,
            university_id: Optional[int] = None,
            program_name: Optional[str] = None,
            program_level: Optional[str] = None,
            duration_in_years: Optional[int] = None,
            next_intake: Optional[datetime.date] = None,
            about: Optional[str] = None,
            start_date: Optional[datetime.date] = None,
            submission_deadline: Optional[datetime.date] = None,
            offshore_onshore_deadline: Optional[datetime.date] = None,
            brochure_url: Optional[str] = None,
            tution_fees: Optional[int] = None,
    ) -> "CourseSchema":

        emp = cls.get_employee(auth_token)
        if not emp:
            raise GraphQLError("Unauthorized")

        has_permission = emp.job_roles.filter(
            permissions__name="course_update"
        ).exists()

        if not has_permission and not emp.is_superuser:
            raise GraphQLError("You do not have permission to edit course")

        with transaction.atomic():

            try:
                course = Course.objects.select_for_update().get(id=course_id)
            except ObjectDoesNotExist:
                raise GraphQLError("Course not found")

            if university_id is not None:
                try:
                    uni = university.objects.get(id=university_id)
                    course.university = uni
                except ObjectDoesNotExist:
                    raise GraphQLError("University not found")

            if program_level is not None:
                valid_levels = {key for key, _ in Course.PROGRAM_LEVEL_CHOICES}
                level = program_level.lower()

                if level not in valid_levels:
                    raise GraphQLError(
                        f"Invalid program level: {level}"
                    )

                course.program_level = level

            if program_name is not None:
                new_program_name = program_name.strip()

                uni_id_to_check = (
                    course.university_id if university_id is None else university_id
                )

                exists = Course.objects.filter(
                    university_id=uni_id_to_check,
                    program_name__iexact=new_program_name,
                ).exclude(id=course_id).exists()

                if exists:
                    raise GraphQLError(
                        "A course with this program name already exists for this university"
                    )

                course.program_name = new_program_name

            if duration_in_years is not None:
                course.duration_in_years = duration_in_years

            if next_intake is not None:
                course.next_intake = next_intake

            if about is not None:
                course.about = about

            if start_date is not None:
                course.start_date = start_date

            if submission_deadline is not None:
                course.submission_deadline = submission_deadline

            if offshore_onshore_deadline is not None:
                course.offshore_onshore_deadline = offshore_onshore_deadline

            if brochure_url is not None:
                course.brochure_url = brochure_url

            if tution_fees is not None:
                course.tution_fees = tution_fees

            try:
                course.save()
            except IntegrityError:
                raise GraphQLError(
                    "A course with this program name already exists for this university"
                )
            except Exception as e:
                raise GraphQLError(f"Failed to update course: {str(e)}")

            return CourseSchema(
                id=course.id,
                university_id=course.university_id,
                university_name=course.university.name,
                program_name=course.program_name,
                program_level=course.program_level,
                duration_in_years=course.duration_in_years,
                next_intake=course.next_intake,
                about=course.about,
                start_date=course.start_date,
                submission_deadline=course.submission_deadline,
                offshore_onshore_deadline=course.offshore_onshore_deadline,
                brochure_url=course.brochure_url,
                tution_fees=course.tution_fees,
            )

    @classmethod
    def delete_course(
            cls,
            auth_token: str,
            course_id: int,
    ) -> "CourseSchema":

        emp = cls.get_employee(auth_token)
        if not emp:
            raise GraphQLError("Unauthorized")

        has_permission = emp.job_roles.filter(
            permissions__name="course_delete"
        ).exists()

        if not has_permission and not emp.is_superuser:
            raise GraphQLError("You do not have permission to delete course")

        try:
            with transaction.atomic():
                course = Course.objects.select_for_update().get(id=course_id)

                response = CourseSchema(
                    id=course.id,
                    university_id=course.university_id,
                    university_name=course.university.name,
                    program_name=course.program_name,
                    program_level=course.program_level,
                    duration_in_years=course.duration_in_years,
                    next_intake=course.next_intake,
                    about=course.about,
                    start_date=course.start_date,
                    submission_deadline=course.submission_deadline,
                    offshore_onshore_deadline=course.offshore_onshore_deadline,
                    brochure_url=course.brochure_url,
                    tution_fees=course.tution_fees,
                )

                course.delete()

        except Course.DoesNotExist:
            raise GraphQLError("Course not found")
        except Exception as e:
            raise GraphQLError(f"Unable to delete course: {str(e)}")

        return response


@strawberry.type
class CourseListSchema(SchemaMixin):
    course: List[CourseSchema]
    page: int
    limit: int
    total: int

    @classmethod
    def course_list(
            cls,
            auth_token: str,
            page: int,
            uni_id: Optional[int] = None,
            programme_name: Optional[str] = None,
            programme_level: Optional[str] = None,
            limit: Optional[int] = 100,
    ) -> "CourseListSchema":

        emp = cls.get_employee(auth_token)
        if not emp:
            raise GraphQLError("Unauthorized")

        has_permission = emp.job_roles.filter(
            permissions__name="course_view"
        ).exists()

        if not has_permission and not emp.is_superuser:
            raise GraphQLError("You do not have permission to view course")

        page = max(page, 1)
        limit = min(limit or 100, 100)
        offset = (page - 1) * limit

        course_table = Course._meta.db_table
        university_table = university._meta.db_table

        where_clauses = []
        params = []

        if uni_id:
            where_clauses.append("c.university_id = %s")
            params.append(uni_id)

        if programme_name:
            where_clauses.append("LOWER(c.program_name) LIKE %s")
            params.append(f"%{programme_name.lower()}%")

        if programme_level:
            valid_levels = {key for key, _ in Course.PROGRAM_LEVEL_CHOICES}

            level = programme_level.lower()
            if level not in valid_levels:
                raise GraphQLError(
                    f"Invalid programme level. Allowed values: {', '.join(valid_levels)}"
                )

            where_clauses.append("LOWER(c.program_level) = %s")
            params.append(level)

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        count_sql = f"""
            SELECT COUNT(*)
            FROM {course_table} c
            {where_sql}
        """

        data_sql = f"""
            SELECT
                c.id,
                c.university_id,
                u.name AS university_name,
                c.program_name,
                c.program_level,
                c.duration_in_years,
                c.next_intake,
                c.about,
                c.start_date,
                c.submission_deadline,
                c.offshore_onshore_deadline,
                c.brochure_url,
                c.tution_fees
            FROM {course_table} c
            JOIN {university_table} u ON u.id = c.university_id
            {where_sql}
            ORDER BY c.start_date DESC
            LIMIT %s OFFSET %s
        """

        with connection.cursor() as cursor:
            cursor.execute(count_sql, params)
            total = cursor.fetchone()[0]

            cursor.execute(data_sql, params + [limit, offset])
            rows = cursor.fetchall()

        courses = [
            CourseSchema(
                id=row[0],
                university_id=row[1],
                university_name=row[2],
                program_name=row[3],
                program_level=row[4],
                duration_in_years=row[5],
                next_intake=row[6],
                about=row[7],
                start_date=row[8],
                submission_deadline=row[9],
                offshore_onshore_deadline=row[10],
                brochure_url=row[11],
                tution_fees=row[12],
            )
            for row in rows
        ]

        return cls(
            course=courses,
            page=page,
            limit=limit,
            total=total,
        )

@strawberry.type
class CourseQuery:
    course: CourseSchema = strawberry.field(
        resolver=CourseSchema.course
    )

    course_list: CourseListSchema = strawberry.field(
        resolver=CourseListSchema.course_list
    )

@strawberry.type
class CourseMutation:
    add_course : CourseSchema = strawberry.field(
        resolver=CourseSchema.add_course
    )

    edit_course : CourseSchema = strawberry.field(
        resolver=CourseSchema.edit_course
    )

    delete_course : CourseSchema = strawberry.field(
        resolver=CourseSchema.delete_course
    )