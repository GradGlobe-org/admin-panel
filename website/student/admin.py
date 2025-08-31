from django.contrib import admin
from .models import (
    Student,
    Email,
    PhoneNumber,
    StudentDetails,
    EducationDetails,
    ExperienceDetails,
    TestScores,
    Preference,
    ShortlistedUniversity,
    ShortlistedCourse,
    StudentLogs
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


class PhoneNumberInline(admin.StackedInline):
    model = PhoneNumber
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
    list_display = (
        "email_address",
        "full_name_display",
        "mobile_number",
        "gender",
    )
    search_fields = (
        "email__email",
        "full_name",
        "details__first_name",
        "details__last_name",
    )
    list_filter = ("details__gender", "details__country")
    fields = ("full_name", "password", "authToken")
    readonly_fields = ("authToken",)

    inlines = [
        StudentDetailsInline,
        EmailInline,
        PhoneNumberInline,
        EducationDetailsInline,
        PreferenceInline,
        TestScoresInline,
        ExperienceDetailsInline,
        ShortlistedUniversityInline,
        ShortlistedCourseInline,
    ]

    def get_inline_instances(self, request, obj=None):
        if obj:
            return super().get_inline_instances(request, obj)
        return []

    # ---- Display Methods ----
    def full_name_display(self, obj):
        return obj.full_name if obj.full_name else "-"
    full_name_display.short_description = "Full Name"

    def email_address(self, obj):
        return getattr(obj.email, "email", "-")
    email_address.short_description = "Email"

    def mobile_number(self, obj):
        return getattr(obj.phone_number, "mobile_number", "-")
    mobile_number.short_description = "Mobile"

    def gender(self, obj):
        return getattr(obj.details, "gender", "-")
    gender.short_description = "Gender"


@admin.register(ExperienceDetails)
class ExperienceDetailsAdmin(admin.ModelAdmin):
    list_display = ("student", "company_name", "title", "employment_type", "start_date", "currently_working")
    search_fields = ("company_name", "title", "industry_type")
    list_filter = ("employment_type", "industry_type", "country")


@admin.register(ShortlistedUniversity)
class ShortlistedUniversityAdmin(admin.ModelAdmin):
    list_display = ("student", "university", "added_on")
    search_fields = ("student__full_name", "university__name")
    list_filter = ("added_on",)


@admin.register(ShortlistedCourse)
class ShortlistedCourseAdmin(admin.ModelAdmin):
    list_display = ("student", "course", "added_on")
    search_fields = ("student__full_name", "course__program_name", "course__university__name")
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
