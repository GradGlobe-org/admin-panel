import decimal
import json
from dataclasses import dataclass

import strawberry
from typing import List, Optional
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, transaction
from graphql import GraphQLError
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from strawberry import Info
from authentication.models import Employee
from student.models import Student, AssignedCounsellor, Bucket, Email, StudentDetails, EducationDetails, TestScores, \
    Preference, ExperienceDetails, AppliedUniversity, StudentLogs, CallRequest, StudentSubMilestone, StudentMilestone, \
    StudentDocumentRequirement, DocumentType
from authentication.Utils import SchemaMixin
from university.AllSchemas import DocumentRequirementUpdateInput, MilestoneUpdateInput
from .AllSchema import *
import re

PHONE_REGEX = re.compile(r"^[6-9]\d{9}$")
EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)


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
    end_date: str | None


@strawberry.type
class ExperienceDetailsSchema:
    id: Optional[int] = None
    company_name: str
    title: str
    city: str
    country: str
    employment_type: str
    industry_type:str
    start_date: str
    end_date: str
    currently_working: bool


import decimal

@strawberry.type
class TestScoresSchema:
    exam_type: str
    english_exam_type: str
    date: str
    listening_score: decimal.Decimal | None
    reading_score: decimal.Decimal | None
    writing_score: decimal.Decimal | None


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
    id: int
    university_id: int
    university_name: str
    added_on: str


@strawberry.type
class ShortlistedCourseSchema:
    id: int
    course_id: int
    course_name: str
    added_on: str


@strawberry.type
class StudentLogsSchema:
    logs: str
    added_on: str


@strawberry.type
class CallRequestSchema:
    id: Optional[int] = None
    student_id: Optional[int] = None
    student_name: Optional[str] = None
    employee_id: Optional[int] = None
    employee_name: Optional[str] = None
    requested_on: Optional[str] = None
    schedule_for: Optional[str] = None
    call_timing: Optional[str] = None
    status: Optional[str] = None
    outcome: Optional[str] = None
    counsellor_notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_on: Optional[str] = None
    updated_at: Optional[str] = None


@strawberry.type
class AssignedCounsellorSchema(SchemaMixin):
    student_id: int
    student_name: str
    employee_id: int
    employee_name: str
    assigned_on: str

    @classmethod
    def from_model(cls, obj):
        return cls(
            student_id=obj.student.id,
            student_name=obj.student.full_name,
            employee_id=obj.employee.id,
            employee_name=obj.employee.name,
            assigned_on=str(obj.assigned_on),
        )

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
    id: int
    course_id: int
    course_name: str
    applied_at: str
    application_number: Optional[str] = None


@strawberry.type
class StudentSchema(SchemaMixin):
    id: int
    full_name: str
    phone_number: str
    category: Optional[str]
    email: Optional[str]
    image_id: Optional[str] = None

    student_details: Optional[StudentDetailsSchema] = None
    education_details: Optional[EducationDetailsSchema] = None
    test_scores: Optional[TestScoresSchema] = None
    preference: Optional[PreferenceSchema] = None

    experience_details: Optional[list[ExperienceDetailsSchema]] = None
    student_logs: Optional[list[StudentLogsSchema]] = None
    shortlisted_university: Optional[list[ShortlistedUniversitySchema]] = None
    shortlisted_course: Optional[list[ShortlistedCourseSchema]] = None
    call_request: Optional[list[CallRequestSchema]] = None
    assigned_counsellor: Optional[list[AssignedCounsellorSchema]] = None
    applied_university: Optional[list[AppliedUniversitySchema]] = None

    @classmethod
    def student_schema_builder(cls, data: dict, logs: Optional[dict] = None) -> "StudentSchema":
        try:
            student = data["student"]

            student_logs = (
                [
                    StudentLogsSchema(
                        logs=l["logs"],
                        added_on=l["added_on"],
                    )
                    for l in logs
                ]
                if logs
                else []
            )

            return StudentSchema(
                id=student["id"],
                full_name=student["full_name"],
                phone_number=student["phone_number"],
                category=student.get("category"),
                email=student.get("email"),
                image_id=student.get("google_file_uuid"),

                student_details=(
                    StudentDetailsSchema(
                        first_name=data["student_details"]["first_name"],
                        last_name=data["student_details"]["last_name"],
                        gender=data["student_details"]["gender"],
                        dob=data["student_details"]["dob"],
                        nationality=data["student_details"]["nationality"],
                        address=data["student_details"]["address"],
                        state=data["student_details"]["state"],
                        city=data["student_details"]["city"],
                        zip_code=data["student_details"]["zip_code"],
                        country=data["student_details"]["country"],
                    )
                    if data.get("student_details") else None
                ),

                education_details=(
                    EducationDetailsSchema(
                        institution_name=data["education_details"]["institution_name"],
                        degree=data["education_details"]["degree"],
                        study_field=data["education_details"]["study_field"],
                        cgpa=data["education_details"]["cgpa"],
                        start_date=data["education_details"]["start_date"],
                        end_date=data["education_details"]["end_date"],
                    )
                    if data.get("education_details") else None
                ),

                test_scores=(
                    TestScoresSchema(
                        exam_type=data["test_scores"]["exam_type"],
                        english_exam_type=data["test_scores"]["english_exam_type"],
                        date=data["test_scores"]["date"],
                        listening_score=data["test_scores"]["listening_score"],
                        reading_score=data["test_scores"]["reading_score"],
                        writing_score=data["test_scores"]["writing_score"],
                    )
                    if data.get("test_scores") else None
                ),

                preference=(
                    PreferenceSchema(
                        country=data["preference"]["country"],
                        degree=data["preference"]["degree"],
                        discipline=data["preference"]["discipline"],
                        sub_discipline=data["preference"]["sub_discipline"],
                        date=data["preference"]["date"],
                        budget=data["preference"]["budget"],
                    )
                    if data.get("preference") else None
                ),

                experience_details=[
                    ExperienceDetailsSchema(
                        id=e["id"],
                        company_name=e["company_name"],
                        title=e["title"],
                        city=e["city"],
                        country=e["country"],
                        employment_type=e["employment_type"],
                        industry_type=e["industry_type"],
                        start_date=e["start_date"],
                        end_date=e["end_date"],
                        currently_working=e["currently_working"],
                    )
                    for e in (data.get("experience_details") or [])
                ],

                shortlisted_university=[
                    ShortlistedUniversitySchema(
                        id=u["id"],
                        university_id=u["university_id"],
                        university_name=u["university_name"],
                        added_on=u["added_on"],
                    )
                    for u in (data.get("shortlisted_universities") or [])
                ],

                shortlisted_course=[
                    ShortlistedCourseSchema(
                        id=c["id"],
                        course_id=c["course_id"],
                        course_name=c["course_name"],
                        added_on=c["added_on"],
                    )
                    for c in (data.get("shortlisted_courses") or [])
                ],

                assigned_counsellor=[
                    AssignedCounsellorSchema(
                        student_id=a["student_id"],
                        student_name=a["student_name"],
                        employee_id=a["employee_id"],
                        employee_name=a["employee_name"],
                        assigned_on=a["assigned_on"],
                    )
                    for a in (data.get("assigned_counsellors") or [])
                ],

                applied_university=[
                    AppliedUniversitySchema(
                        id=a["id"],
                        course_id=a["course_id"],
                        course_name=a["course_name"],
                        applied_at=a["applied_at"],
                        application_number=a["application_number"],
                    )
                    for a in (data.get("applied_universities") or [])
                ],

                call_request=[
                    CallRequestSchema(
                        id=cr["id"],
                        student_id=cr["student_id"],
                        student_name=cr["student_name"],
                        employee_id=cr["employee_id"],
                        employee_name=cr["employee_name"],
                        requested_on=cr["requested_on"],
                        schedule_for=cr["schedule_for"],
                        call_timing=cr["call_timing"],
                        status=cr["status"],
                        outcome=cr["outcome"],
                        counsellor_notes=cr["counsellor_notes"],
                        follow_up_required=cr["follow_up_required"],
                        follow_up_on=cr["follow_up_on"],
                        updated_at=cr["updated_at"],
                    )
                    for cr in (data.get("call_requests") or [])
                ],

                student_logs=student_logs,
            )

        except Exception as e:
            raise GraphQLError("Internal Server Error")

    @classmethod
    def validate_phone(cls, phone: str) -> bool:
        if not PHONE_REGEX.match(phone):
            return False
        return True

    @classmethod
    def validate_email(cls, email: str) -> bool:
        if not EMAIL_REGEX.match(email):
            return False
        return True

    @classmethod
    def student(cls, info: Info, auth_token: str, student_id: int):
        emp = cls.get_employee(auth_token)
        if not emp:
            raise GraphQLError("Unauthorized")

        requested_fields = [
            f.name for f in info.selected_fields[0].selections
        ]

        logs_requested = "studentLogs" in requested_fields

        if not emp.is_superuser:
            is_assigned = AssignedCounsellor.objects.filter(
                student_id=student_id,
                employee_id=emp.id
            ).exists()

            if not is_assigned:
                raise GraphQLError(
                    "You do not have permission to view this student"
                )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT get_student_full_profile(%s);",
                [student_id],
            )
            row = cursor.fetchone()

        if not row or not row[0]:
            raise GraphQLError("Student not found")

        data = json.loads(row[0]) if isinstance(row[0], str) else row[0]

        logs = None
        if logs_requested:
            logs = list(
                StudentLogs.objects
                .filter(student_id=student_id)
                .values("logs", "added_on")
                .order_by("-added_on")
            )

        return cls.student_schema_builder(data, logs)

    @classmethod
    def add_student(cls,
                    auth_token:str,
                    full_name: str,
                    phone_number: str,
                    category: Optional[str] = None,
                    email: Optional[str] = None,

                    student_details: Optional[StudentDetailsInputSchema] = None,
                    education_details: Optional[EducationDetailsInputSchema] = None,
                    test_scores: Optional[TestScoresInputSchema] = None,
                    preference: Optional[PreferenceInputSchema] = None,

                    experience_details: Optional[list[ExperienceDetailsInputSchema]] = None,
                    assigned_counsellor: Optional[AssignedCounsellorInputSchema] = None,
                    applied_university: Optional[list[AppliedUniversityInputSchema]] = None,
                    ) -> "StudentSchema":

        emp = cls.get_employee(auth_token)
        if not emp:
            raise GraphQLError("Unauthorized")

        has_permission = emp.job_roles.filter(
            permissions__name="student_add"
        ).exists()

        if not (emp.is_superuser or has_permission):
            raise GraphQLError("You do not have permission to add a student")

        if not cls.validate_phone(phone_number):
            raise GraphQLError("Invalid phone number")

        if Student.objects.filter(phone_number=phone_number).exists():
            raise GraphQLError("Student with this phone number already exists")

        if email:
            if not cls.validate_email(email):
                raise GraphQLError("Invalid email")

        if Email.objects.filter(email=email).exists():
            raise GraphQLError("Student with this email already exists")

        try:
            with transaction.atomic():
                bucket = None
                if category:
                    try:
                        bucket = Bucket.objects.get(name=category)
                    except Bucket.DoesNotExist:
                        raise GraphQLError("Invalid category")

                student = Student.objects.create(
                    full_name=full_name,
                    phone_number=phone_number,
                    category=bucket,
                    is_otp_verified=False
                )

                if email:
                    Email.objects.create(
                        student=student,
                        email=email,
                    )

                if student_details:
                    StudentDetails.objects.create(
                        student=student,
                        first_name=student_details.first_name,
                        last_name=student_details.last_name,
                        gender=student_details.gender,
                        dob=student_details.dob,
                        nationality=student_details.nationality,
                        address=student_details.address,
                        state=student_details.state,
                        city=student_details.city,
                        zip_code=student_details.zip_code,
                        country=student_details.country,
                    )

                if education_details:
                    EducationDetails.objects.create(
                        student=student,
                        institution_name=education_details.institution_name,
                        degree=education_details.degree,
                        study_field=education_details.study_field,
                        cgpa=education_details.cgpa,
                        start_date=education_details.start_date,
                        end_date=education_details.end_date,
                    )

                if test_scores:
                    TestScores.objects.create(
                        student=student,
                        exam_type=test_scores.exam_type,
                        english_exam_type=test_scores.english_exam_type,
                        date=test_scores.date,
                        listening_score=test_scores.listening_score,
                        reading_score=test_scores.reading_score,
                        writing_score=test_scores.writing_score,
                    )

                if preference:
                    Preference.objects.create(
                        student=student,
                        country=preference.country,
                        degree=preference.degree,
                        discipline=preference.discipline,
                        sub_discipline=preference.sub_discipline,
                        date=preference.date,
                        budget=preference.budget,
                    )

                if experience_details:
                    ExperienceDetails.objects.bulk_create([
                        ExperienceDetails(
                            student=student,
                            company_name=e.company_name,
                            title=e.title,
                            city=e.city,
                            country=e.country,
                            employment_type=e.employment_type,
                            industry_type=e.industry_type,
                            start_date=e.start_date,
                            end_date=e.end_date,
                            currently_working=e.currently_working,
                        )
                        for e in experience_details
                    ])

                if applied_university:
                    AppliedUniversity.objects.bulk_create([
                        AppliedUniversity(
                            student=student,
                            course_id=a.course_id,
                        )
                        for a in applied_university
                    ])

                if assigned_counsellor:
                    AssignedCounsellor.objects.create(
                        student=student,
                        employee_id=assigned_counsellor.employee_id,
                    )
                else:
                    AssignedCounsellor.objects.create(
                        student=student,
                        employee=emp,
                    )

        except:
            raise GraphQLError("Server error while trying to add university")

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT get_student_full_profile(%s);",
                    [student.id],
                )
                row = cursor.fetchone()

            if not row or not row[0]:
                raise GraphQLError("Student not found")

            raw = row[0]

            if isinstance(raw, str):
                data = json.loads(raw)
            else:
                data = raw

            return cls.student_schema_builder(data)

        except:
            raise GraphQLError("Internal Server Error")

    @classmethod
    def edit_student(
            cls,
            auth_token: str,
            student_id: int,

            full_name: Optional[str] = None,
            phone_number: Optional[str] = None,
            category: Optional[str] = None,
            email: Optional[str] = None,

            student_details: Optional[StudentDetailsPatchInputSchema] = None,
            education_details: Optional[EducationDetailsPatchInputSchema] = None,
            test_scores: Optional[TestScoresPatchInputSchema] = None,
            preference: Optional[PreferencePatchInputSchema] = None,

            experience_details: Optional[ExperienceDetailsUpdateInputSchema] = None,
            applied_university: Optional[AppliedUniversityUpdateInputSchema] = None,
            assigned_counsellor: Optional[AssignedCounsellorInputSchema] = None,
            call_request: Optional[CallRequestUpdateInputSchema] = None
    ) -> "StudentSchema":

        emp = cls.get_employee(auth_token)
        if not emp:
            raise GraphQLError("Unauthorized")

        student = Student.objects.filter(id=student_id).first()
        if not student:
            raise GraphQLError("Student does not exist")

        if not emp.is_superuser:
            is_assigned = AssignedCounsellor.objects.filter(
                student_id=student_id,
                employee_id=emp.id
            ).exists()

            if not is_assigned:
                raise GraphQLError("You do not have permission to perform this task")

        if phone_number:
            if not cls.validate_phone(phone_number):
                raise GraphQLError("Invalid phone number")

        if Student.objects.filter(phone_number=phone_number).exists():
            raise GraphQLError("Student with this phone number already exists")

        if email:
            if not cls.validate_email(email):
                raise GraphQLError("Invalid email")

        if Email.objects.filter(email=email).exists():
            raise GraphQLError("Student with this email already exists")

        try:
            with transaction.atomic():

                student = (
                    Student.objects
                    .select_for_update()
                    .filter(id=student_id)
                    .first()
                )

                if not student:
                    raise GraphQLError("Student does not exist")

                if full_name is not None:
                    student.full_name = full_name

                if phone_number is not None:
                    exists = Student.objects.exclude(id=student_id).filter(
                        phone_number=phone_number
                    ).exists()
                    if exists:
                        raise GraphQLError("Phone number already in use")
                    student.phone_number = phone_number

                if category is not None:
                    try:
                        student.category = Bucket.objects.get(name=category)
                    except Bucket.DoesNotExist:
                        raise GraphQLError("Invalid category")

                student.save()

                if email is not None:
                    Email.objects.update_or_create(
                        student=student,
                        defaults={"email": email}
                    )

                def patch_one_to_one(model, patch_obj):
                    data = {
                        field: value
                        for field, value in vars(patch_obj).items()
                        if value is not None
                    }

                    if not data:
                        return

                    model.objects.update_or_create(
                        student=student,
                        defaults=data
                    )

                if student_details:
                    patch_one_to_one(StudentDetails, student_details)

                if education_details:
                    patch_one_to_one(EducationDetails, education_details)

                if test_scores:
                    patch_one_to_one(TestScores, test_scores)

                if preference:
                    patch_one_to_one(Preference, preference)

                def handle_list(model, payload, field_map):
                    if not payload:
                        return

                    if payload.delete_ids:
                        deleted, _ = model.objects.filter(
                            id__in=payload.delete_ids,
                            student=student
                        ).delete()

                        if deleted != len(payload.delete_ids):
                            raise GraphQLError("Delete failed")

                    if payload.update:
                        for obj in payload.update:
                            data = {
                                model_field: getattr(obj, input_field)
                                for model_field, input_field in field_map.items()
                                if getattr(obj, input_field) is not None
                            }

                            rows = model.objects.filter(
                                id=obj.id,
                                student=student
                            ).update(**data)

                            if rows != 1:
                                raise GraphQLError("Update failed")

                    if payload.add:
                        model.objects.bulk_create([
                            model(
                                student=student,
                                **{
                                    model_field: getattr(obj, input_field)
                                    for model_field, input_field in field_map.items()
                                }
                            )
                            for obj in payload.add
                        ])

                handle_list(
                    ExperienceDetails,
                    experience_details,
                    {
                        "company_name": "company_name",
                        "title": "title",
                        "city": "city",
                        "country": "country",
                        "employment_type": "employment_type",
                        "industry_type": "industry_type",
                        "start_date": "start_date",
                        "end_date": "end_date",
                        "currently_working": "currently_working",
                    },
                )

                if applied_university:
                    if applied_university.delete_ids:
                        if not emp.is_superuser:
                            raise GraphQLError(
                                "You are not allowed to delete applications"
                            )

                        deleted, _ = AppliedUniversity.objects.filter(
                            id__in=applied_university.delete_ids,
                            student=student
                        ).delete()

                        if deleted != len(applied_university.delete_ids):
                            raise GraphQLError(
                                "Delete failed: invalid application ID or ownership mismatch"
                            )

                    if applied_university.add:
                        AppliedUniversity.objects.bulk_create([
                            AppliedUniversity(
                                student=student,
                                course_id=obj.course_id
                            )
                            for obj in applied_university.add
                        ])

                if assigned_counsellor:
                    if not emp.is_superuser:
                        raise GraphQLError("You are not allowed to perform this task")

                    existing = AssignedCounsellor.objects.filter(
                        student=student
                    ).select_for_update().first()

                    if existing:
                        existing.employee_id = assigned_counsellor.employee_id
                        existing.save(update_fields=["employee"])
                    else:
                        AssignedCounsellor.objects.create(
                            student=student,
                            employee_id=assigned_counsellor.employee_id
                        )

                if call_request:
                    allowed_statuses = {
                        c[0] for c in
                        CallRequest._meta.get_field("status").choices
                    }

                    if call_request.add:
                        for obj in call_request.add:
                            if not emp.is_superuser and not AssignedCounsellor.objects.filter(
                                    student=student,
                                    employee=emp
                            ).exists():
                                raise GraphQLError(
                                    "You do not have permission to create call requests for this student"
                                )

                            if CallRequest.objects.filter(
                                    student=student,
                                    employee=emp
                            ).exists():
                                raise GraphQLError(
                                    "Call request already exists for this student"
                                )

                            if obj.status and obj.status not in allowed_statuses:
                                raise GraphQLError("Invalid call status")

                            CallRequest.objects.create(
                                student=student,
                                employee=emp,
                                schedule_for=obj.schedule_for,
                                call_timing=obj.call_timing,
                                status=obj.status or "requested",
                                counsellor_notes=obj.counsellor_notes,
                                follow_up_required=obj.follow_up_required or False,
                                follow_up_on=obj.follow_up_on,
                            )

                    if call_request.update:
                        for obj in call_request.update:
                            call_obj = CallRequest.objects.select_for_update().filter(
                                id=obj.id,
                                student=student
                            ).first()

                            if not call_obj:
                                raise GraphQLError("Call request not found")

                            if not emp.is_superuser and call_obj.employee_id != emp.id:
                                raise GraphQLError(
                                    "You do not have permission to update this call request"
                                )

                            if obj.status:
                                if obj.status not in allowed_statuses:
                                    raise GraphQLError("Invalid call status")
                                call_obj.status = obj.status

                            for field in [
                                "schedule_for",
                                "call_timing",
                                "counsellor_notes",
                                "follow_up_required",
                                "follow_up_on",
                            ]:
                                val = getattr(obj, field)
                                if val is not None:
                                    setattr(call_obj, field, val)

                            call_obj.save()

            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT get_student_full_profile(%s);",
                    [student.id],
                )
                row = cursor.fetchone()

            if not row or not row[0]:
                raise GraphQLError("Student not found")

            data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            return cls.student_schema_builder(data)

        except Exception as e:
            raise GraphQLError(f"Update failed")

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

        try:
            # Main optimized queryset
            student_qs = (
                Student.objects
                .select_related(
                    "student_details",
                    "email",
                    "category",
                    "profile_picture",
                )
                .prefetch_related(
                    "assigned_counsellors__employee",
                    "applied_universities__course",
                    Prefetch(
                        "call_requests",
                        queryset=CallRequest.objects.select_related("student", "employee")
                    )
                )
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
                d = getattr(s, "student_details", None)

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

                applied_university = []

                ap = s.applied_universities.all()

                for application in ap:
                    applied_university.append(
                        AppliedUniversitySchema(
                            id=application.id,
                            course_id=application.course_id,
                            course_name=application.course.program_name if application.course else None,
                            applied_at=application.applied_at,
                            application_number=application.application_number,
                        )
                    )

                call_request = []
                cr = s.call_requests.all()
                for call in cr:
                    call_request.append(
                        CallRequestSchema(
                            student_id=call.student_id,
                            student_name=call.student.full_name,
                            employee_id=call.employee.id,
                            employee_name=call.employee.name,
                            requested_on=call.requested_on,
                        )
                    )

                assigned_counsellor = None

                if emp.is_superuser:
                    assignment = s.assigned_counsellors.first()

                    if assignment and assignment.employee:
                        employee = assignment.employee

                        assigned_counsellor = [
                            AssignedCounsellorSchema(
                                student_id=s.id,
                                student_name=s.full_name,
                                employee_id=employee.id,
                                employee_name=getattr(employee, "name", str(employee)),
                                assigned_on=str(assignment.assigned_on),
                            )
                        ]

                profile = getattr(s, "profile_picture", None)

                students.append(
                    StudentSchema(
                        id=s.id,
                        full_name=s.full_name,
                        phone_number=s.phone_number,
                        category=s.category.name if s.category else None,
                        email=getattr(getattr(s, "email", None), "email", None),
                        image_id=profile.google_file_id if profile else None,
                        student_details=details,
                        assigned_counsellor=assigned_counsellor,
                        applied_university=applied_university,
                        call_request=call_request,
                    )
                )

            return cls(
                student_list=students,
                limit=limit,
                current_page=page,
                total=total,
            )

        except Exception as e:
            raise GraphQLError("Internal Server Error")

import datetime

@strawberry.type
class DocumentSchema:
    document_type: str
    submitted_document: str
    counsellor_status: str | None
    counsellor_comments: str | None
    uploaded_at: datetime.datetime

@strawberry.type
class RequiredDocumentSchema:
    required_doc_id: int
    document_type: str
    instructions: str | None
    is_submitted: bool
    document_id: int | None
    submitted_document: str | None
    counsellor_status: str | None
    counsellor_comments: str | None
    uploaded_at: datetime.datetime | None

@strawberry.type
class SubMilestoneSchema:
    id: int
    name: str
    status: str
    order: int
    counsellor_comment: str | None

@strawberry.type
class MilestoneSchema:
    name: str
    order: int
    steps: List[SubMilestoneSchema]

@strawberry.type
class ApplicationDocumentsSchema:
    basic: List[RequiredDocumentSchema]
    university_specific: List[RequiredDocumentSchema]

@strawberry.type
class ApplicationSchema(SchemaMixin):
    application_id: int
    course_id: int
    applied_at: datetime.datetime
    status: str
    application_number: str
    documents: ApplicationDocumentsSchema
    milestones: List[MilestoneSchema]

    @classmethod
    def applications(
            cls,
            auth_token: str,
            student_id: int,
            application_id: int,
    ) -> "ApplicationSchema":

        emp = cls.get_employee(auth_token)
        if not emp:
            raise GraphQLError("Unauthorized")

        app = (
            AppliedUniversity.objects
            .select_related("student")
            .filter(id=application_id)
            .first()
        )

        if not app:
            raise GraphQLError("Application does not exist")

        student = app.student

        if not emp.is_superuser:
            is_assigned = AssignedCounsellor.objects.filter(
                student=student,
                employee=emp,
            ).exists()

            if not is_assigned:
                raise GraphQLError(
                    "You do not have permission to access this student's applications"
                )

        try:

            app = (
                AppliedUniversity.objects
                .filter(id=application_id, student_id=student_id)
                .prefetch_related(
                    Prefetch(
                        "student_milestones",
                        queryset=StudentMilestone.objects
                        .order_by("order")
                        .prefetch_related(
                            Prefetch(
                                "steps",
                                queryset=StudentSubMilestone.objects.order_by("order")
                            )
                        ),
                    )
                )
                .first()
            )

            if not app:
                raise GraphQLError("Invalid application id")

            basic_requirements = (
                StudentDocumentRequirement.objects
                .select_related("document_type", "file")
                .filter(
                    student_id=student_id,
                    requested_for_university__isnull=True,
                )
                .order_by("document_type__name")
            )

            basic_docs: List[RequiredDocumentSchema] = []
            for req in basic_requirements:
                doc = getattr(req, "file", None)
                basic_docs.append(
                    RequiredDocumentSchema(
                        required_doc_id=req.id,
                        document_type=req.document_type.name,
                        instructions=req.instructions,
                        is_submitted=doc is not None,
                        document_id=doc.id if doc else None,
                        submitted_document=doc.submitted_document if doc else None,
                        counsellor_status=doc.counsellor_status if doc else None,
                        counsellor_comments=doc.counsellor_comments if doc else None,
                        uploaded_at=doc.uploaded_at if doc else None,
                    )
                )

            university_requirements = (
                StudentDocumentRequirement.objects
                .select_related("document_type", "file")
                .filter(requested_for_university=app)
                .order_by("document_type__name")
            )

            university_docs: List[RequiredDocumentSchema] = []
            for req in university_requirements:
                doc = getattr(req, "file", None)
                university_docs.append(
                    RequiredDocumentSchema(
                        required_doc_id=req.id,
                        document_type=req.document_type.name,
                        instructions=req.instructions,
                        is_submitted=doc is not None,
                        document_id=doc.id if doc else None,
                        submitted_document=doc.submitted_document if doc else None,
                        counsellor_status=doc.counsellor_status if doc else None,
                        counsellor_comments=doc.counsellor_comments if doc else None,
                        uploaded_at=doc.uploaded_at if doc else None,
                    )
                )

            milestones: List[MilestoneSchema] = []
            for m in app.student_milestones.all():
                milestones.append(
                    MilestoneSchema(
                        name=m.name,
                        order=m.order,
                        steps=[
                            SubMilestoneSchema(
                                id=s.id,
                                name=s.name,
                                status=s.status,
                                order=s.order,
                                counsellor_comment=s.counsellor_comment,
                            )
                            for s in m.steps.all()
                        ],
                    )
                )

            return cls(
                application_id=app.id,
                course_id=app.course_id,
                applied_at=app.applied_at,
                status=app.status,
                application_number=str(app.application_number),
                documents=ApplicationDocumentsSchema(
                    basic=basic_docs,
                    university_specific=university_docs,
                ),
                milestones=milestones,
            )

        except GraphQLError:
            raise
        except Exception:
            raise GraphQLError(
                "Something went wrong while fetching student application"
            )

    @classmethod
    def edit_student_application(
            cls,
            info,
            auth_token: str,
            application_id: int,
            documents: Optional[DocumentRequirementUpdateInput] = None,
            milestones: Optional[MilestoneUpdateInput] = None,
    ) -> "ApplicationSchema":

        emp = cls.get_employee(auth_token)
        if not emp:
            raise GraphQLError("Unauthorized")

        try:
            application = (
                AppliedUniversity.objects
                .select_related("student")
                .get(id=application_id)
            )
        except AppliedUniversity.DoesNotExist:
            raise GraphQLError("Application does not exist")

        student_id = application.student_id

        if not emp.is_superuser:
            is_assigned = AssignedCounsellor.objects.filter(
                student_id=student_id,
                employee_id=emp.id
            ).exists()
            if not is_assigned:
                raise GraphQLError(
                    "You do not have permission to update this application"
                )

        allowed_submilestone_statuses = {
            choice[0] for choice in StudentSubMilestone.STATUS
        }

        try:
            with transaction.atomic():

                if documents:
                    if documents.delete_ids:
                        reqs = StudentDocumentRequirement.objects.filter(
                            id__in=documents.delete_ids
                        )
                        if reqs.count() != len(documents.delete_ids):
                            raise GraphQLError(
                                "One or more document requirements not found"
                            )

                        for req in reqs:
                            if req.student_id != student_id:
                                raise GraphQLError("Invalid document reference")

                            if req.requested_for_university_id != application_id:
                                raise GraphQLError(
                                    "Document does not belong to this application"
                                )

                            if req.requested_by_id != emp.id:
                                raise GraphQLError(
                                    "You can delete only documents requested by you"
                                )

                        reqs.delete()

                    if documents.update:
                        for obj in documents.update:
                            req = StudentDocumentRequirement.objects.filter(
                                id=obj.id
                            ).first()

                            if not req:
                                raise GraphQLError(
                                    "Document requirement not found"
                                )

                            if req.student_id != student_id:
                                raise GraphQLError("Invalid document reference")

                            if req.requested_for_university_id != application_id:
                                raise GraphQLError(
                                    "Document does not belong to this application"
                                )

                            req.instructions = obj.instructions
                            req.save(update_fields=["instructions"])

                    if documents.add:
                        for obj in documents.add:
                            doc_type = DocumentType.objects.filter(
                                id=obj.document_type_id
                            ).first()

                            if not doc_type:
                                raise GraphQLError(
                                    f"Invalid document type {obj.document_type_id}"
                                )

                            if doc_type.is_default:
                                raise GraphQLError(
                                    "It is a basic document and cannot be requested per application"
                                )

                            exists = StudentDocumentRequirement.objects.filter(
                                student_id=student_id,
                                document_type=doc_type,
                                requested_for_university=application
                            ).exists()

                            if exists:
                                raise GraphQLError(
                                    "This document is already requested"
                                )

                            StudentDocumentRequirement.objects.create(
                                student_id=student_id,
                                document_type=doc_type,
                                requested_for_university=application,
                                requested_by=emp,
                                instructions=obj.instructions
                            )

                if milestones and milestones.update:
                    for obj in milestones.update:
                        sub = StudentSubMilestone.objects.select_related(
                            "milestone__application"
                        ).filter(id=obj.id).first()

                        if not sub:
                            raise GraphQLError(
                                f"Sub-milestone {obj.id} not found"
                            )
                        if sub.milestone.application_id != application_id:
                            raise GraphQLError(
                                "Sub-milestone does not belong to this application"
                            )

                        if obj.status:
                            if obj.status not in allowed_submilestone_statuses:
                                raise GraphQLError(
                                    f"Invalid status '{obj.status}'. "
                                )
                            sub.status = obj.status
                        if obj.counsellor_comment is not None:
                            sub.counsellor_comment = obj.counsellor_comment
                        sub.save(update_fields=[
                            "status",
                            "counsellor_comment",
                            "updated_at"
                        ])

            app = cls.applications(
                auth_token=auth_token,
                student_id=student_id,
                application_id=application_id
            )
            if not app:
                raise GraphQLError("Failed to fetch updated application")
            return app

        except GraphQLError:
            raise
        except Exception:
            raise GraphQLError(
                "Update failed due to an internal error"
            )

@strawberry.type
class DocumentTypeSchema(SchemaMixin):
    id: int
    name: str
    doc_type: str
    sub_type: Optional[str]
    is_default: bool

    @classmethod
    def documents(cls, auth_token:str) -> List["DocumentTypeSchema"]:
        try:
            emp = cls.get_employee(auth_token)
            if not emp:
                raise GraphQLError("Unauthorized")

            docs = list(DocumentType.objects.all())

            return [
                cls(
                    id=doc.id,
                    name=doc.name,
                    doc_type=doc.doc_type,
                    sub_type=doc.sub_type,
                    is_default=doc.is_default,
                )
                for doc in docs
            ]

        except:
            raise GraphQLError("Internal server error")







@strawberry.type
class StudentsQuery:
    students_list: StudentListSchema = strawberry.field(
        resolver=StudentListSchema.student_list
    )

    student: StudentSchema = strawberry.field(
        resolver=StudentSchema.student
    )

    application: ApplicationSchema = strawberry.field(
        resolver=ApplicationSchema.applications
    )

    docs: List[DocumentTypeSchema] = strawberry.field(
        resolver=DocumentTypeSchema.documents
    )

@strawberry.type()
class StudentMutation:
    assign_students: list[AssignedCounsellorSchema] = strawberry.field(
        resolver=AssignedCounsellorSchema.assign_counsellor
    )

    add_student: StudentSchema = strawberry.field(
        resolver=StudentSchema.add_student
    )

    update_student: StudentSchema = strawberry.field(
        resolver=StudentSchema.edit_student
    )

    edit_application: ApplicationSchema = strawberry.field(
        resolver=ApplicationSchema.edit_student_application
    )