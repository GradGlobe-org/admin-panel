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
    list_display = ('id', 'university', 'program_level', 'start_date', 'duration_in_years', 'next_intake')
    list_filter = ('program_level', 'university')
    search_fields = ('university__name', 'program_level')
    ordering = ('university', 'program_level', 'start_date')

    fieldsets = (
        ('Basic Info', {
            'fields': ('university', 'program_level', 'duration_in_years')
        }),
        ('Course Timeline', {
            'fields': ('start_date', 'next_intake', 'submission_deadline', 'offshore_onshore_deadline')
        }),
        ('Cost Details', {
            'fields': ('cost_of_living',)
        }),
        ('About and Materials', {
            'fields': ('about', 'brochure_url')
        }),
    )

    inlines = [
        CostOfLivingBreakdownInline,
    ]


# === Optional: Separate Admin View for Cost Items (not necessary) ===

@admin.register(CostOfLivingBreakdown)
class CostOfLivingBreakdownAdmin(admin.ModelAdmin):
    list_display = ('course', 'name', 'cost')
    list_filter = ('course__university',)
    search_fields = ('course__university__name', 'name')
    ordering = ('course', 'name')
