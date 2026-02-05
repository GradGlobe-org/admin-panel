from datetime import datetime, date
import strawberry
from typing import Optional, List
import decimal

from authentication.Schema import EmployeeSchema
from university.Schema import UniversitySchema


@strawberry.input
class StudentDetailsInputSchema:
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

@strawberry.input
class EducationDetailsInputSchema:
    institution_name: str
    degree: str
    study_field: str
    cgpa: str
    start_date: date
    end_date: Optional[date] = None


@strawberry.input
class ExperienceDetailsInputSchema:
    id: Optional[int] = None
    company_name: str
    title: str
    city: str
    country: str
    employment_type: str
    industry_type:str
    start_date: date
    end_date: date
    currently_working: bool


@strawberry.input
class TestScoresInputSchema:
    exam_type: str
    english_exam_type: str
    date: date
    listening_score: decimal.Decimal | None
    reading_score: decimal.Decimal | None
    writing_score: decimal.Decimal | None


@strawberry.input
class PreferenceInputSchema:
    country: str
    degree: str
    discipline: str
    sub_discipline: str
    date: date
    budget: int


@strawberry.type
class ShortlistedUniversitySchema:
    id: int
    university_id: int
    university_name: str
    added_on: datetime


@strawberry.type
class ShortlistedCourseSchema:
    id: int
    course_id: int
    course_name: str
    added_on: datetime


@strawberry.type
class StudentLogsSchema:
    logs: str
    added_on: datetime


# @strawberry.type
# class CallRequestSchema:
#     student_id: int
#     student_name: str
#     employee_id: int
#     employee_name: str
#     requested_on: datetime


@strawberry.input
class AssignedCounsellorInputSchema:
    employee_id: int

@strawberry.input
class AppliedUniversityInputSchema:
    course_id: int
    # application_number: str


@strawberry.type
class DocumentSchema:
    name: str
    doc_type: str
    sub_type: str
    is_default: bool


@strawberry.type
class RequiredDocumentSchema:
    id: int
    document_type: str
    requested_by: Optional[EmployeeSchema]
    university: Optional[UniversitySchema]
    instructions: Optional[str]
    created_at: datetime
    uploaded_document: Optional["DocumentSchema"]

@strawberry.type
class DocumentSchema:
    file_uuid: str
    status: str
    counsellor_comments: Optional[str]
    uploaded_at: datetime


@strawberry.input
class StudentDetailsPatchInputSchema:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    nationality: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None


@strawberry.input
class EducationDetailsPatchInputSchema:
    institution_name: Optional[str] = None
    degree: Optional[str] = None
    study_field: Optional[str] = None
    cgpa: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


@strawberry.input
class TestScoresPatchInputSchema:
    exam_type: Optional[str] = None
    english_exam_type: Optional[str] = None
    listening_score: Optional[decimal.Decimal] = None
    reading_score: Optional[decimal.Decimal] = None
    writing_score: Optional[decimal.Decimal] = None
    test_date: Optional[date] = None


@strawberry.input
class PreferencePatchInputSchema:
    country: Optional[str] = None
    degree: Optional[str] = None
    discipline: Optional[str] = None
    sub_discipline: Optional[str] = None
    date: Optional[date] = None
    budget: Optional[int] = None


@strawberry.input
class ExperienceDetailsUpdateInputSchema:
    add: Optional[List[ExperienceDetailsInputSchema]] = None
    update: Optional[List[ExperienceDetailsInputSchema]] = None
    delete_ids: Optional[List[int]] = None

@strawberry.input
class AppliedUniversityUpdateItemSchema(AppliedUniversityInputSchema):
    id: int

@strawberry.input
class AppliedUniversityUpdateInputSchema:
    add: Optional[List[AppliedUniversityInputSchema]] = None
    update: Optional[List[AppliedUniversityUpdateItemSchema]] = None
    delete_ids: Optional[List[int]] = None

@strawberry.input
class CallRequestInputSchema:
    id: Optional[int] = None
    schedule_for: Optional[date] = None
    call_timing: Optional[datetime] = None
    status: Optional[str] = None
    counsellor_notes: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_on: Optional[datetime] = None


@strawberry.input
class CallRequestUpdateInputSchema:
    add: Optional[List[CallRequestInputSchema]] = None
    update: Optional[List[CallRequestInputSchema]] = None