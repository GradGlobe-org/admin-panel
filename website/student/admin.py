from django.contrib import admin, messages
from django.db import transaction

from .models import (AppliedUniversity, AssignedCounsellor, Bucket,
                     CallRequest, Document, DocumentType, EducationDetails,
                     Email, ExperienceDetails, Milestone, Preference,
                     ShortlistedCourse, ShortlistedUniversity, Student,
                     StudentDetails, StudentDocumentRequirement, StudentLogs,
                     StudentMilestone, StudentSubMilestone,
                     SubMilestoneTemplate, TestScores)

# ---------------- Inlines ----------------


class StudentDetailsInline(admin.StackedInline):
    model = StudentDetails
    can_delete = False
    max_num = 1
    extra = 0


class EmailInline(admin.StackedInline):
    model = Email
    can_delete = False
    max_num = 1
    extra = 0


class EducationDetailsInline(admin.StackedInline):
    model = EducationDetails
    can_delete = False
    max_num = 1
    extra = 0


class PreferenceInline(admin.StackedInline):
    model = Preference
    can_delete = False
    max_num = 1
    extra = 0


class TestScoresInline(admin.StackedInline):
    model = TestScores
    can_delete = False
    max_num = 1
    extra = 0


class ExperienceDetailsInline(admin.TabularInline):
    model = ExperienceDetails
    extra = 1


class ShortlistedUniversityInline(admin.TabularInline):
    model = ShortlistedUniversity
    extra = 1
    readonly_fields = ["added_on"]


class ShortlistedCourseInline(admin.TabularInline):
    model = ShortlistedCourse
    extra = 1
    readonly_fields = ["added_on"]


# ---------------- ModelAdmins ----------------


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone_number", "is_otp_verified", "category")
    search_fields = ("full_name", "phone_number")
    list_filter = ("category", "is_otp_verified")
    readonly_fields = ("authToken",)
    autocomplete_fields = ["category"]
    fields = ("full_name", "phone_number", "is_otp_verified", "category", "authToken")


@admin.register(ExperienceDetails)
class ExperienceDetailsAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "company_name",
        "title",
        "employment_type",
        "start_date",
        "currently_working",
    )
    search_fields = ("company_name", "title", "industry_type")
    list_filter = ("employment_type", "industry_type", "country")


@admin.register(Bucket)
class BucketAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(ShortlistedUniversity)
class ShortlistedUniversityAdmin(admin.ModelAdmin):
    list_display = ("student", "university", "added_on")
    search_fields = ("student__full_name", "university__name")
    list_filter = ("added_on",)


@admin.register(ShortlistedCourse)
class ShortlistedCourseAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "added_on")
    search_fields = (
        "student__full_name",
        "course__program_name",
        "course__university__name",
    )
    list_filter = ("added_on",)


@admin.register(StudentLogs)
class StudentLogsAdmin(admin.ModelAdmin):
    list_display = ("student", "short_log", "added_on")
    search_fields = ("student__full_name", "logs")
    list_filter = ("added_on",)
    readonly_fields = ("added_on",)

    def short_log(self, obj):
        return (obj.logs[:50] + "...") if len(obj.logs) > 50 else obj.logs

    short_log.short_description = "Log"


@admin.register(CallRequest)
class CallRequestAdmin(admin.ModelAdmin):
    list_display = ("student", "employee", "requested_on")
    list_filter = ("employee", "requested_on")
    search_fields = ("student__full_name", "employee__name")
    ordering = ("-requested_on",)
    date_hierarchy = "requested_on"
    autocomplete_fields = ("student", "employee")
    readonly_fields = ("requested_on",)


@admin.register(AssignedCounsellor)
class AssignedCounsellorAdmin(admin.ModelAdmin):
    list_display = ("student", "employee", "assigned_on")
    list_filter = ("employee", "assigned_on")
    search_fields = ("student__full_name", "employee__name")
    ordering = ("-assigned_on",)
    date_hierarchy = "assigned_on"
    autocomplete_fields = ("student", "employee")
    readonly_fields = ("assigned_on",)


# ---------------- DOCUMENT SYSTEM ADMINS ----------------


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "doc_type", "sub_type", "is_default")
    list_filter = ("doc_type", "is_default")
    search_fields = ("name", "doc_type", "sub_type")


@admin.register(StudentDocumentRequirement)
class StudentDocumentRequirementAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "document_type",
        "requested_by",
        "requested_for_university",
        "created_at",
    )
    search_fields = ("student__full_name", "document_type__name")
    list_filter = ("document_type__doc_type", "requested_for_university")
    autocomplete_fields = (
        "student",
        "document_type",
        "requested_by",
        "requested_for_university",
    )
    ordering = ("-created_at",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "required_document",
        "submitted_document",
        "counsellor_status",
        "uploaded_at",
        "file_uuid",
    )
    list_filter = ("counsellor_status", "uploaded_at")
    search_fields = (
        "required_document__student__full_name",
        "required_document__document_type__name",
        "file_id",
        "file_uuid",
    )
    readonly_fields = ("uploaded_at", "updated_at", "file_uuid")
    ordering = ("-uploaded_at",)
    autocomplete_fields = ("required_document",)


# ---------------- MILESTONE SYSTEM ----------------


class StudentSubMilestoneInline(admin.TabularInline):
    model = StudentSubMilestone
    fields = ("name", "status", "order", "counsellor_comment", "updated_at")
    readonly_fields = ("updated_at",)
    extra = 0
    ordering = ("order",)


@admin.register(StudentMilestone)
class StudentMilestoneAdmin(admin.ModelAdmin):
    list_display = ("application", "name", "order")
    ordering = ("application", "order")
    inlines = [StudentSubMilestoneInline]


@admin.register(StudentSubMilestone)
class StudentSubMilestoneAdmin(admin.ModelAdmin):
    list_display = ("milestone", "name", "status", "order", "updated_at")
    list_filter = ("status",)
    ordering = ("milestone", "order")
    search_fields = ("name", "milestone__name")


class StudentMilestoneInline(admin.TabularInline):
    model = StudentMilestone
    fields = ("name", "order")
    readonly_fields = ("name", "order")
    extra = 0
    show_change_link = True  # ⭐ lets you open sub-milestones


# ---------------- MILESTONE TEMPLATES ----------------


class SubMilestoneTemplateInline(admin.TabularInline):
    model = SubMilestoneTemplate
    extra = 2
    fields = ("name", "order")
    ordering = ("order",)


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_default")
    ordering = ("order",)
    inlines = [SubMilestoneTemplateInline]


@admin.register(SubMilestoneTemplate)
class SubMilestoneTemplateAdmin(admin.ModelAdmin):
    list_display = ("milestone", "name", "order")
    ordering = ("milestone", "order")
    search_fields = ("name", "milestone__name")


# ---------------- AppliedUniversity Admin ----------------


@admin.register(AppliedUniversity)
class AppliedUniversityAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "formatted_course",
        "application_number",
        "status",
        "applied_at",
    )
    list_filter = ("status", "applied_at")
    search_fields = (
        "student__full_name",
        "course__program_name",
        "course__university__name",
        "application_number",
    )
    readonly_fields = ("applied_at",)
    ordering = ("-applied_at",)
    autocomplete_fields = ("student", "course")

    inlines = [StudentMilestoneInline]

    actions = ["assign_milestone_template"]

    def formatted_course(self, obj):
        course = obj.course
        return (
            f"{course.program_name} — {course.university.name} ({course.program_level})"
        )

    formatted_course.short_description = "Course Details"