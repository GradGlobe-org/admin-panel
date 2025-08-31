from django.contrib import admin
from .models import Course, CostOfLivingBreakdown


# === INLINE MODEL FOR COURSE ===
class CostOfLivingBreakdownInline(admin.TabularInline):
    model = CostOfLivingBreakdown
    extra = 1
    fields = ('name', 'cost')
    verbose_name = "Cost Item"
    verbose_name_plural = "Cost of Living Breakdown"


# === COURSE ADMIN ===
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'university',
        'program_name',
        'program_level',
        'tution_fees',  # Added tution_fees to list_display
        'start_date',
        'duration_in_years',
        'next_intake'
    )
    list_filter = ('program_level', 'university')
    search_fields = ('university__name', 'program_name', 'program_level', 'tution_fees')  # Added tution_fees to search_fields
    ordering = ('university', 'program_level', 'start_date')

    fieldsets = (
        ('Basic Info', {
            'fields': ('university', 'program_name', 'program_level', 'duration_in_years', 'tution_fees')  # Added tution_fees
        }),
        ('Course Timeline', {
            'fields': ('start_date', 'next_intake', 'submission_deadline', 'offshore_onshore_deadline')
        }),
        ('About and Materials', {
            'fields': ('about', 'brochure_url')
        }),
    )

    inlines = [
        CostOfLivingBreakdownInline,
    ]


# === COST OF LIVING BREAKDOWN ADMIN ===
@admin.register(CostOfLivingBreakdown)
class CostOfLivingBreakdownAdmin(admin.ModelAdmin):
    list_display = ('course', 'name', 'cost')
    list_filter = ('course__university',)
    search_fields = ('course__university__name', 'course__program_name', 'name')
    ordering = ('course', 'name')