from django.contrib import admin
from .models import Scholarship, ExpenseType, ScholarshipExpenseCoverage, FAQ


# === INLINES ===

class ScholarshipExpenseCoverageInline(admin.TabularInline):
    model = ScholarshipExpenseCoverage
    extra = 1


class FAQInline(admin.TabularInline):
    model = FAQ
    extra = 1


# === MAIN ADMIN ===

@admin.register(Scholarship)
class ScholarshipAdmin(admin.ModelAdmin):
    list_display = ('name', 'awarded_by', 'course', 'deadline', 'intake_year', 'amount', 'country')
    search_fields = ('name', 'awarded_by', 'overview', 'details', 'amount_details')
    list_filter = ('country', 'intake_year', 'deadline')
    filter_horizontal = ('university', 'eligible_nationalities')

    fieldsets = (
        (None, {
            'fields': (
                'name',
                'awarded_by',
                'overview',
                'details',
                'amount_details',
                'amount',
                'course',
                'deadline',
                'intake_year',
                'type_of_scholarship',
                'no_of_students',
                'brochure',
                'country',
                'university',
                'eligible_nationalities',
            )
        }),
    )

    inlines = [
        ScholarshipExpenseCoverageInline,
        FAQInline,
    ]


# === OTHER MODELS ===

@admin.register(ExpenseType)
class ExpenseTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'scholarship')
    search_fields = ('question', 'answer', 'scholarship__name')
    raw_id_fields = ('scholarship',)