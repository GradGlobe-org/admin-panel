import decimal

import strawberry
from typing import List, Optional

from django.core.exceptions import ObjectDoesNotExist
from graphql import GraphQLError
from django.core.paginator import Paginator
from django.db.models import Q

from authentication.models import Employee
from student.models import Student, AssignedCounsellor
from authentication.Utils import SchemaMixin


@strawberry.type
class StudentDetailsSchema:
    first_name: str
    last_name: str
    gender: str
    dob: str
    nationality: str
    address: str
    state: str
    city: str
    zip_code: str
    country: str

@strawberry.type
class EducationDetailsSchema:
    institution_name: str
    degree: str
    study_field: str
    cgpa: str
    start_date: str
    end_date: str
@strawberry.type
@strawberry.type
class ExperienceDetailsSchema:
    company_name: str
    title: str
    city: str
    country: str
    employment_type: str
    industry_type:str
    start_date: str
    end_date: str
    currently_working: str
@strawberry.type
@strawberry.type
class TestScoresSchema:
    exam_type: str
    english_exam_type: str
    date: str
    listening_score:decimal.Decimal
    reading_score:decimal.Decimal
    writing_score:decimal.Decimal
@strawberry.type
class PreferenceSchema:
    country: str
    degree: str
    discipline: str
    sub_discipline: str
    date: str
    budget: int
@strawberry.type
class ShortlistedUniversitySchema:
    university_id: int
    university_name: str
    added_on: str
@strawberry.type
class ShortlistedCourseSchema:
    course_id: int
    course_name: str
    added_on: str
@strawberry.type
class StudentLogsSchema:
    logs: str
    added_on: str
@strawberry.type
class CallRequestSchema:
    student_id: int
    student_name: str
    employee_id: int
    employee_name: str
    requested_on: str


@strawberry.type
class AssignedCounsellorSchema(SchemaMixin):
    student_id: int
    student_name: str
    employee_id: int
    employee_name: str
    assigned_on: str

    @classmethod
    def assign_counsellor(
        cls,
        auth_token: str,
        student_ids: list[int],
        employee_id: int
    ) -> list["AssignedCounsellorSchema"]:

        emp = cls.get_employee(auth_token)
        if not emp or not emp.is_superuser:
            raise GraphQLError("You do not have permission to perform this task")

        if not student_ids:
            raise GraphQLError("No student to assign")
        if not employee_id:
            raise GraphQLError("No employee id provided")

        try:
            counsellor = Employee.objects.get(id=employee_id)
        except Employee.DoesNotExist:
            raise GraphQLError("No such employee exists")
        except Exception:
            raise GraphQLError("Error fetching employee")

        students = Student.objects.filter(id__in=student_ids)
        if not students.exists():
            raise GraphQLError("No valid students found")

        existing_assignments = AssignedCounsellor.objects.filter(
            student__in=students,
            employee=counsellor
        ).values_list("student_id", flat=True)

        new_assignments = []
        for student in students:
            if student.id in existing_assignments:
                continue

            new_assignments.append(
                AssignedCounsellor(
                    student=student,
                    employee=counsellor
                )
            )

        AssignedCounsellor.objects.bulk_create(new_assignments)

        return [
            AssignedCounsellorSchema(
                student_id=ac.student.id,
                student_name=ac.student.full_name,
                employee_id=ac.employee.id,
                employee_name=ac.employee.name,
                assigned_on=str(ac.assigned_on)
            )
            for ac in AssignedCounsellor.objects.filter(
                student__in=students,
                employee=counsellor
            )
        ]


@strawberry.type
class AppliedUniversitySchema:
    course_id: int
    course_name: str
    applied_at: str
    application_number: str


@strawberry.type
class StudentSchema:
    id: int
    full_name: str
    phone_number: str
    category: Optional[str]
    email: Optional[str]
    google_file_uuid: Optional[str] = None
    student_details: Optional[StudentDetailsSchema] = None
    education_details: Optional[EducationDetailsSchema] = None
    experience_details: Optional[ExperienceDetailsSchema] = None
    test_scores: Optional[TestScoresSchema] = None
    preference: Optional[PreferenceSchema] = None
    shortlisted_university: Optional[ShortlistedUniversitySchema] = None
    shortlisted_course: Optional[ShortlistedCourseSchema] = None
    student_logs: Optional[StudentLogsSchema] = None
    call_request: Optional[CallRequestSchema] = None
    assigned_counsellor: Optional[AssignedCounsellorSchema] = None
    applied_university: Optional[AppliedUniversitySchema] = None

    # @classmethod
    # def student_list


@strawberry.type
class StudentListSchema(SchemaMixin):
    student_list: List[StudentSchema]
    limit: int
    current_page: int
    total: int

    @classmethod
    def student_list(
            cls,
            auth_token: str,
            page: int,
            assigned_to_me_only: Optional[bool] = False,
            limit: Optional[int] = 50,
            query: Optional[str] = None,
    ) -> "StudentListSchema":

        emp = cls.get_employee(auth_token)

        if not emp:
            raise GraphQLError("Unauthorized")

        if page < 1:
            raise GraphQLError("Page must be greater than 0")

        limit = min(limit or 50, 100)

        student_qs = (
            Student.objects
            .select_related("details", "email", "category")
            .prefetch_related("assigned_counsellors__employee")
        )

        if not emp.is_superuser or assigned_to_me_only:
            student_qs = student_qs.filter(
                assigned_counsellors__employee=emp
            )

        if query:
            student_qs = student_qs.filter(
                Q(full_name__icontains=query) |
                Q(phone_number__icontains=query) |
                Q(email__email__icontains=query)
            )

        student_qs = student_qs.distinct()

        paginator = Paginator(student_qs, limit)
        page_obj = paginator.get_page(page)

        students_qs = page_obj.object_list
        total = paginator.count

        students = []

        for s in students_qs:
            details = None
            d = getattr(s, "details", None)

            if d:
                details = StudentDetailsSchema(
                    first_name=d.first_name,
                    last_name=d.last_name,
                    gender=d.gender,
                    dob=str(d.dob),
                    nationality=d.nationality,
                    address=d.address,
                    state=d.state,
                    city=d.city,
                    zip_code=d.zip_code,
                    country=d.country,
                )

            assigned_counsellor = None

            if emp.is_superuser:

                assignments = list(s.assigned_counsellors.all())
                assignment = assignments[0] if assignments else None

                if assignment and assignment.employee:
                    employee = assignment.employee

                    assigned_counsellor = AssignedCounsellorSchema(
                        student_id=s.id,
                        student_name=s.full_name,
                        employee_id=employee.id,
                        employee_name=getattr(employee, "name", str(employee)),
                        assigned_on=str(assignment.assigned_on),
                    )

            students.append(
                StudentSchema(
                    id=s.id,
                    full_name=s.full_name,
                    phone_number=s.phone_number,
                    category=s.category.name if s.category else None,
                    email=s.email.email if hasattr(s, "email") else None,
                    student_details=details,
                    assigned_counsellor=assigned_counsellor,
                )
            )

        return cls(
            student_list=students,
            limit=limit,
            current_page=page,
            total=total,
        )


@strawberry.type
class StudentsQuery:
    students_list: StudentListSchema = strawberry.field(
        resolver=StudentListSchema.student_list
    )

    assign_counsellor: list[AssignedCounsellorSchema] = strawberry.field(
        resolver=AssignedCounsellorSchema.assign_counsellor
    )