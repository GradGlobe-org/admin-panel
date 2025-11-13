from django.contrib import admin
from .models import (
    AppliedUniversity,
    CallRequest,
    AssignedCounsellor,
    Bucket,
    Document,
    EducationDetails,
    Email,
    ExperienceDetails,
    Preference,
    ShortlistedCourse,
    ShortlistedUniversity,
    Student,
    StudentDetails,
    StudentLogs,
    TestScores,
    DocumentTemplate,
    TemplateDocument,
    StudentDocumentRequirement,
)


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


@admin.register(AppliedUniversity)
class AppliedUniversityAdmin(admin.ModelAdmin):
    list_display = ("student", "formatted_course", "application_number", "status", "applied_at")
    list_filter = ("status", "applied_at")
    search_fields = ("student__full_name", "course__program_name", "course__university__name", "application_number")
    readonly_fields = ("applied_at",)
    ordering = ("-applied_at",)
    autocomplete_fields = ("student", "course")

    def formatted_course(self, obj):
        course = obj.course
        return f"{course.program_name} — {course.university.name} ({course.program_level})"

    formatted_course.short_description = "Course Details"


# ---------------- Document-related admin ----------------

class TemplateDocumentInline(admin.TabularInline):
    model = TemplateDocument
    extra = 1
    fields = ("name", "doc_type", "sub_type")
    show_change_link = True


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "description")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    inlines = [TemplateDocumentInline]


@admin.register(TemplateDocument)
class TemplateDocumentAdmin(admin.ModelAdmin):
    list_display = ("name", "doc_type", "sub_type", "template")
    list_filter = ("doc_type", "template")
    search_fields = ("name", "doc_type", "sub_type", "template__name")
    ordering = ("template", "name")


@admin.register(StudentDocumentRequirement)
class StudentDocumentRequirementAdmin(admin.ModelAdmin):
    list_display = ("student", "template_document")
    list_filter = ("template_document__doc_type",)
    search_fields = ("student__full_name", "template_document__name", "template_document__doc_type")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("student", "name", "doc_type", "status", "uploaded_at", "template_document")
    list_filter = ("status", "doc_type", "uploaded_at")
    search_fields = ("student__full_name", "name", "doc_type", "file_id", "file_uuid")
    readonly_fields = ("uploaded_at", "updated_at", "file_uuid")
    ordering = ("-uploaded_at",)
    fieldsets = (
        ("Document Information", {
            "fields": ("student", "template_document", "name", "doc_type", "sub_type", "status")
        }),
        ("File Details", {
            "fields": ("file_id", "file_uuid", "uploaded_at", "updated_at")
        }),
    )