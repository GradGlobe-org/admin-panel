from django.contrib import admin
from .models import *

# Inlines for one-to-one relationships: use StackedInline with can_delete=False and max_num=1
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

# Inlines for multi-relations
class ExperienceDetailsInline(admin.TabularInline):
    model = ExperienceDetails
    extra = 1

# class DocumentInline(admin.TabularInline):
#     model = Document
#     extra = 1

class ShortlistedUniversityInline(admin.TabularInline):
    model = ShortlistedUniversity
    extra = 1
    readonly_fields = ['added_on']
# Inline for TestScores (OneToOne)
class TestScoresInline(admin.StackedInline):
    model = TestScores
    can_delete = False
    max_num = 1
    extra = 0

# Add TestScoresInline to the StudentAdmin's inlines:
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "full_name",
        "email_address",
        "mobile_number",
        "gender"
    )
    search_fields = ("username", )

    inlines = [
        StudentDetailsInline,
        EmailInline,
        PhoneNumberInline,
        EducationDetailsInline,
        PreferenceInline,
        TestScoresInline,         # <--- Add this here
        ExperienceDetailsInline,
        # DocumentInline,
        ShortlistedUniversityInline,
    ]

    def get_inline_instances(self, request, obj=None):
        if obj is not None:
            return super().get_inline_instances(request, obj)
        return []

    # --- Display Methods ---
    def full_name(self, obj):
        # Handles missing related StudentDetails gracefully
        if hasattr(obj, "details"):
            return f"{obj.details.first_name} {obj.details.last_name}"
        return "-"
    full_name.short_description = "Name"

    def email_address(self, obj):
        # Handles missing Email object gracefully
        return getattr(obj.email, "email", "-")
    email_address.short_description = "Email"

    def mobile_number(self, obj):
        # Handles missing PhoneNumber object gracefully
        return getattr(obj.phone_number, "mobile_number", "-")
    mobile_number.short_description = "Mobile"

    def gender(self, obj):
        if hasattr(obj, "details"):
            return obj.details.gender
        return "-"
    gender.short_description = "Gender"