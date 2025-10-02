from django.contrib import admin
from .models import (
    Student,
    Bucket,
    Email,
    # PhoneNumber,
    StudentDetails,
    EducationDetails,
    ExperienceDetails,
    TestScores,
    Preference,
    ShortlistedUniversity,
    ShortlistedCourse,
    StudentLogs,
    CallRequest,
    AssignedCounsellor,
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


# class PhoneNumberInline(admin.StackedInline):
#     model = PhoneNumber
#     can_delete = False
#     max_num = 1
#     extra = 0


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
    list_display = (
        "full_name",
        "email_address",
        "mobile_number",
        "category",
    )
    search_fields = (
        "full_name",
        "phone_number__mobile_number",
        "email__email",
    )
    list_filter = ("category",)
    readonly_fields = ("authToken",)
    autocomplete_fields = ["category"]

    fields = ("full_name", "password", "category")

    def email_address(self, obj):
        return getattr(obj.email, "email", "-")

    email_address.short_description = "Email"

    def mobile_number(self, obj):
        return getattr(obj.phone_number, "mobile_number", "-")

    mobile_number.short_description = "Mobile"


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
    list_display = (
        "student",
        "short_log",
        "added_on",
    )
    search_fields = (
        "student__full_name",
        "logs",
    )
    list_filter = ("added_on",)

    readonly_fields = ("added_on",)

    def short_log(self, obj):
        return (obj.logs[:50] + "...") if len(obj.logs) > 50 else obj.logs

    short_log.short_description = "Log"


@admin.register(CallRequest)
class CallRequestAdmin(admin.ModelAdmin):
    list_display = ("student", "employee", "requested_on")  # shows these columns
    list_filter = ("employee", "requested_on")  # sidebar filters
    search_fields = ("student__full_name", "employee__name")  # search by related fields
    ordering = ("-requested_on",)  # newest first
    date_hierarchy = "requested_on"
    autocomplete_fields = ("student", "employee")
    readonly_fields = ("requested_on",)


@admin.register(AssignedCounsellor)
class AssignedCounsellorAdmin(admin.ModelAdmin):
    list_display = ("student", "employee", "assigned_on")  # columns in list view
    list_filter = ("employee", "assigned_on")  # sidebar filters
    search_fields = ("student__full_name", "employee__name")  # search by related fields
    ordering = ("-assigned_on",)  # newest first
    date_hierarchy = "assigned_on"  # date drilldown
    autocomplete_fields = ("student", "employee")  # improves dropdown UX
    readonly_fields = ("assigned_on",)  # prevent manual edits
