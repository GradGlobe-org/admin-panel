from uuid import uuid4

from django.db.models import F

from authentication.models import Employee
from course.models import Course
from django.core.validators import (MaxLengthValidator, MinLengthValidator,
                                    RegexValidator)
from .Constants import *
from django.db import models, connection
from django.utils import timezone
from university.models import university

class Bucket(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Bucket"
        verbose_name_plural = "Buckets"

    def __str__(self):
        return self.name


phone_regex = RegexValidator(
    regex=r"^\d{10}$", message="Phone number must be exactly 10 digits."
)
otp_regex = RegexValidator(regex=r"^\d{6}$", message="OTP must be exactly 6 digits.")



class Student(models.Model):
    phone_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[phone_regex],
        help_text="Enter a 10-digit phone number.",
    )
    is_otp_verified = models.BooleanField()
    full_name = models.CharField(max_length=200)
    authToken = models.UUIDField(default=uuid4, editable=False, unique=True)
    category = models.ForeignKey(
        Bucket,
        on_delete=models.SET_NULL,
        null=True,
        related_name="students",
    )

    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"

    def __str__(self):
        return self.full_name


class Email(models.Model):
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="email"
    )
    email = models.EmailField(max_length=150, unique=True)

    class Meta:
        verbose_name = "Email"
        verbose_name_plural = "Emails"
        ordering = ["email"]

    def __str__(self):
        return self.student.full_name


class OTPRequest(models.Model):
    phone_number = models.CharField(
        max_length=10,
        unique=True,
        validators=[phone_regex],
        help_text="Enter the phone number associated with the OTP.",
    )
    otp = models.CharField(
        max_length=6, validators=[otp_regex], help_text="6-digit OTP code."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "otp_request"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["phone_number"], name="idx_otp_phone")]

    def __str__(self):
        return f"{self.phone_number} - {self.otp}"


class StudentProfilePicture(models.Model):
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="profile_picture"
    )
    image_uuid = models.UUIDField(editable=False, unique=True, null=True, blank=True)
    google_file_id = models.CharField(max_length=255, blank=True, default="", null=True)

    def __str__(self):
        return f"{self.student.full_name}'s Profile Picture"

class StudentDetails(models.Model):
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="student_details"
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    GENDERS = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    gender = models.CharField(max_length=10, choices=GENDERS)
    dob = models.DateField()
    nationality = models.CharField(max_length=100)
    address = models.CharField(max_length=2000)
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=12)
    country = models.CharField(
        max_length=100, choices=COUNTRY_CHOICES
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class EducationDetails(models.Model):
    student = models.OneToOneField(
        "Student", on_delete=models.CASCADE, related_name="education_details"
    )
    institution_name = models.CharField(max_length=255)
    degree = models.CharField(max_length=50, choices=DEGREE_CHOICES)
    study_field = models.CharField(max_length=50, choices=FIELD_CHOICES)
    cgpa = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.institution_name} ({self.degree})"


class ExperienceDetails(models.Model):
    student = models.ForeignKey(
        "Student", on_delete=models.CASCADE, related_name="experience_details"
    )
    company_name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    country = models.CharField(
        max_length=100, choices=COUNTRY_CHOICES
    )  # Updated to use COUNTRY_CHOICES with full names
    employment_type = models.CharField(max_length=50, choices=EMPLOYMENT_TYPE_CHOICES)
    industry_type = models.CharField(max_length=50, choices=INDUSTRY_TYPE_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    currently_working = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.company_name} ({self.title})"


class TestScores(models.Model):
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="test_scores"
    )
    exam_type = models.CharField(
        max_length=50, choices=EXAM_TYPE_CHOICES, help_text="Main aptitude exam"
    )
    english_exam_type = models.CharField(
        max_length=50,
        choices=ENGLISH_EXAM_CHOICES,
        help_text="English proficiency exam",
    )
    date = models.DateField()
    listening_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    reading_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    writing_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )

    class Meta:
        verbose_name = "Test Score"
        verbose_name_plural = "Test Scores"

    def __str__(self):
        return f"{self.exam_type} ({self.date})"


class Preference(models.Model):
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="preference"
    )
    country = models.CharField(
        max_length=100, choices=COUNTRY_CHOICES
    )  # Updated to use COUNTRY_CHOICES with full names
    degree = models.CharField(max_length=100, choices=DEGREE_CHOICES)
    discipline = models.CharField(max_length=100, choices=DISCIPLINE_CHOICES)
    sub_discipline = models.CharField(max_length=100, choices=SUB_DISCIPLINE_CHOICES)
    date = models.DateField()
    budget = models.PositiveIntegerField()

    def __str__(self):
        return self.full_name


class ShortlistedUniversity(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="shortlisted_universities"
    )
    university = models.ForeignKey(
        university, on_delete=models.CASCADE, related_name="shortlisted_by_students"
    )
    added_on = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("student", "university")
        verbose_name = "Shortlisted university"
        verbose_name_plural = "Shortlisted Universities"

    def __str__(self):
        return f"{self.student.full_name} shortlisted {self.university.name}"


class ShortlistedCourse(models.Model):
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="shortlisted_courses"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="shortlisted_by_students"
    )
    added_on = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("student", "course")
        verbose_name = "Shortlisted Course"
        verbose_name_plural = "Shortlisted Courses"

    def __str__(self):
        return f"{self.student.full_name} shortlisted {self.course.program_name} at {self.course.university.name}"


class StudentLogs(models.Model):
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="StudentLogs",
    )

    logs = models.TextField()
    added_on = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "student_logs"
        ordering = ["-added_on"]
        verbose_name = "Student Log"
        verbose_name_plural = "Student Logs"

    def __str__(self):
        return (
            f"Log for {self.student} on {self.added_on.strftime('%Y-%m-%d %H:%M:%S')}"
        )


class CallRequest(models.Model):
    student = models.ForeignKey(
        "Student",
        on_delete=models.CASCADE,
        related_name="call_requests",
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="call_requests"
    )
    requested_on = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["employee"]),
            models.Index(fields=["requested_on"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "employee"],
                name="unique_student_employee_request",
            )
        ]
        verbose_name = "Call Request"
        verbose_name_plural = "Call Requests"

    def __str__(self):
        return f"Call request: {self.student} → {self.employee} on {self.requested_on:%Y-%m-%d %H:%M}"


class AssignedCounsellor(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="assigned_counsellors",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="counselling_students",
    )
    assigned_on = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = (
            "student",
            "employee",
        )
        verbose_name = "Assigned Counsellor"
        verbose_name_plural = "Assigned Counsellors"
        ordering = ["-assigned_on"]

    def __str__(self):
        return f"{self.employee.name} assigned to {self.student.full_name} on {self.assigned_on:%Y-%m-%d %H:%M}"


class AppliedUniversity(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="applied_universities")
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    applied_at = models.DateTimeField(auto_now_add=True)

    STATUS = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(max_length=55, choices=STATUS, default="pending")

    application_number = models.CharField(max_length=20, unique=True, null=True)

    class Meta:
        unique_together = ("student", "course")
        ordering = ["-applied_at"]
        verbose_name = "Applied University"
        verbose_name_plural = "Applied Universities"
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["course"]),
            models.Index(fields=["application_number"]),
        ]

    def __str__(self):
        return f"{self.student} → {self.course} ({self.application_number})"

    def save(self, *args, **kwargs):
        if self.application_number is None:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT nextval('applied_university_app_no_seq')"
                )
                self.application_number = cursor.fetchone()[0]

        super().save(*args, **kwargs)


class DocumentType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    doc_type = models.CharField(
        max_length=100,
        choices=[
            ("Passport", "Passport"),
            ("Transcript", "Transcript"),
            ("Degree Certificate", "Degree Certificate"),
            ("Recommendation Letter", "Recommendation Letter"),
            ("Statement of Purpose", "Statement of Purpose"),
            ("Resume", "Resume"),
            ("Test Score Report", "Test Score Report"),
            ("ID Proof", "ID Proof"),
            ("Marksheet", "Marksheet"),
            ("Other", "Other"),
        ]
    )
    sub_type = models.CharField(max_length=100, blank=True, null=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        verbose_name = "Document Type"
        verbose_name_plural = "Document Types"
        indexes = [
            models.Index(fields=["doc_type"]),
            models.Index(fields=["is_default"]),
        ]

    def __str__(self):
        return self.name


class StudentDocumentRequirement(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="requirements"
    )

    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.CASCADE
    )

    requested_by = models.ForeignKey(
        Employee,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requested_documents",
        help_text="Null means this is a default required document."
    )

    requested_for_university = models.ForeignKey(
        AppliedUniversity,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="required_documents",
        help_text="Only set if this document is required for a specific university."
    )

    instructions = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "document_type", "requested_for_university")
        ordering = ["-created_at"]
        verbose_name = "Student Document Requirement"
        verbose_name_plural = "Student Document Requirements"
        indexes = [
            models.Index(fields=["student"]),
            models.Index(fields=["document_type"]),
            models.Index(fields=["requested_for_university"]),
        ]

    def __str__(self):
        if self.requested_for_university:
            return (
                f"{self.student.full_name} requires {self.document_type.name} for "
                f"{self.requested_for_university.course.program_name}"
            )
        return f"{self.student.full_name} requires {self.document_type.name}"


class Document(models.Model):
    required_document = models.OneToOneField(
        StudentDocumentRequirement,
        on_delete=models.PROTECT,
        related_name="file",
    )
    submitted_document = models.CharField(max_length=255, blank=True, default="")

    STATUS_CHOICES = [
        ("uploaded", "Uploaded"),
        ("verified", "Verified"),
        ("rejected", "Rejected"),
        ("in_review", "In Review"),
        ("processing", "Processing"),
        ("re-do", "Upload Again")
    ]

    counsellor_status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default="uploaded",
        null=True,
        blank=True
    )
    counsellor_comments = models.CharField(max_length=2000, null=True, blank=True)

    file_id = models.CharField(max_length=255)
    file_uuid = models.UUIDField(default=uuid4, editable=False, unique=True)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        indexes = [
            models.Index(fields=["required_document"]),
            models.Index(fields=["counsellor_status"]),
            models.Index(fields=["file_uuid"]),
        ]

    def __str__(self):
        return f"Document for {self.required_document.document_type.name}"


# Milestones trigger has been added via postgres. is_default=true are assigned directly to new applications
class Milestone(models.Model):
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    is_default = models.BooleanField(default=True)   # optional

    def __str__(self):
        return self.name

class SubMilestoneTemplate(models.Model):
    milestone = models.ForeignKey(
        Milestone,
        on_delete=models.CASCADE,
        related_name="steps"
    )

    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.milestone.name} → {self.name}"

class StudentMilestone(models.Model):
    application = models.ForeignKey(
        AppliedUniversity,
        on_delete=models.CASCADE,
        related_name="student_milestones"
    )

    template = models.ForeignKey(
        Milestone,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.name

class StudentSubMilestone(models.Model):
    milestone = models.ForeignKey(
        StudentMilestone,
        on_delete=models.CASCADE,
        related_name="steps"
    )

    template = models.ForeignKey(
        SubMilestoneTemplate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    name = models.CharField(max_length=255)

    STATUS = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("under_review", "Under Review"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(max_length=20, choices=STATUS, default="pending")

    order = models.PositiveIntegerField(default=1)

    counsellor_comment = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.status})"
