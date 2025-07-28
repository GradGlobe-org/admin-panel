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

class TestScoresInline(admin.StackedInline):
    model = TestScores
    can_delete = False
    max_num = 1
    extra = 0

# Inlines for multi-relations
class ExperienceDetailsInline(admin.TabularInline):
    model = ExperienceDetails
    extra = 1

class ShortlistedUniversityInline(admin.TabularInline):
    model = ShortlistedUniversity
    extra = 1
    readonly_fields = ['added_on']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "email_address",
        "full_name",
        "mobile_number",
        "gender",
    )
    search_fields = ("email__email", "full_name", "details__first_name", "details__last_name")  # Updated to include full_name
    list_filter = ("details__gender", "details__country")  # Optional: Added for better filtering
    fields = ("full_name", "password", "authToken")  # Fields to show in the edit form
    readonly_fields = ("authToken",)  # authToken should not be editable

    inlines = [
        StudentDetailsInline,
        EmailInline,
        PhoneNumberInline,
        EducationDetailsInline,
        PreferenceInline,
        TestScoresInline,
        ExperienceDetailsInline,
        ShortlistedUniversityInline,
    ]

    def get_inline_instances(self, request, obj=None):
        if obj is not None:
            return super().get_inline_instances(request, obj)
        return []

    # --- Display Methods ---
    def full_name(self, obj):
        # Use the full_name field from the Student model
        return obj.full_name if obj.full_name else "-"
    full_name.short_description = "Full Name"

    def email_address(self, obj):
        # Handles missing Email object gracefully
        return getattr(obj.email, "email", "-")
    email_address.short_description = "Email"

    def mobile_number(self, obj):
        # Handles missing PhoneNumber object gracefully
        return getattr(obj.phone_number, "mobile_number", "-")
    mobile_number.short_description = "Mobile"

    def gender(self, obj):
        # Handles missing StudentDetails object gracefully
        return getattr(obj.details, "gender", "-")
    gender.short_description = "Gender"