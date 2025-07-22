from django.contrib import admin
from .models import (
    location, Country, university, WhyStudyInSection, CostOfLiving,
    AdmissionStats, Visa, WorkOpportunity, Partner_Agency, commission,
    mou, Uni_contact, stats, videos_links, ranking_agency,
    university_ranking, faqs
)

# === INLINE MODELS FOR UNIVERSITY ===

class StatsInline(admin.TabularInline):
    model = stats
    extra = 1


class VideosInline(admin.TabularInline):
    model = videos_links
    extra = 1


class FaqsInline(admin.TabularInline):
    model = faqs
    extra = 1


class UniversityRankingInline(admin.TabularInline):
    model = university_ranking
    extra = 1


class UniContactInline(admin.TabularInline):
    model = Uni_contact
    extra = 1


class CommissionInline(admin.TabularInline):
    model = commission
    extra = 1


class MouInline(admin.TabularInline):
    model = mou
    extra = 1


class AdmissionStatsInline(admin.TabularInline):
    model = AdmissionStats
    extra = 1


class VisaInline(admin.TabularInline):
    model = Visa
    extra = 1


class WorkOpportunityInline(admin.TabularInline):
    model = WorkOpportunity
    extra = 1

# === UNIVERSITY ADMIN ===

@admin.register(university)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'establish_year', 'location', 'get_country', 'status')
    list_filter = ('type', 'status', 'location')
    search_fields = ('name', 'location__city', 'location__state', 'location__country')
    raw_id_fields = ('location',)
    ordering = ('name',)
    actions = ['make_published', 'make_draft']

    fieldsets = (
        ('Basic Info', {
            'fields': ('cover_url', 'cover_origin', 'name', 'type', 'establish_year', 'location', 'status')
        }),
        ('Academic & Admission Info', {
            'fields': ('about', 'admission_requirements')
        }),
        ('Other Details', {
            'fields': ('location_map_link', 'avg_acceptance_rate', 'avg_tution_fee', 'review_rating')
        }),
    )

    inlines = [
        StatsInline,
        VideosInline,
        FaqsInline,
        UniversityRankingInline,
        UniContactInline,
        CommissionInline,
        MouInline,
        AdmissionStatsInline,
        VisaInline,
        WorkOpportunityInline,
    ]

    def get_country(self, obj):
        return obj.location.country
    get_country.short_description = 'Country'

    @admin.action(description="Mark selected universities as Published")
    def make_published(self, request, queryset):
        queryset.update(status='PUBLISH')

    @admin.action(description="Mark selected universities as Draft")
    def make_draft(self, request, queryset):
        queryset.update(status='DRAFT')


# === OTHER MODELS ===

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('city', 'state', 'country')
    search_fields = ('city', 'state', 'country')


@admin.register(WhyStudyInSection)
class WhyStudyInSectionAdmin(admin.ModelAdmin):
    list_display = ('country',)
    search_fields = ('country__name', 'content')


@admin.register(CostOfLiving)
class CostOfLivingAdmin(admin.ModelAdmin):
    list_display = ('country', 'total_min', 'total_max')
    search_fields = ('country__name',)


@admin.register(Partner_Agency)
class PartnerAgencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'partner_type')
    search_fields = ('name',)


@admin.register(ranking_agency)
class RankingAgencyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name', 'description')


# Do not register: stats, videos_links, university_ranking, faqs, etc. separately
# because they are already inlined into the university admin

