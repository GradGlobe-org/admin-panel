from django.contrib import admin
from .models import (
    university,
    location,
    stats,
    videos_links,
    ranking_agency,
    university_ranking,
    faqs,
    Uni_contact,
    commission,
    Partner_Agency,
    mou,
    Country,
    WhyStudyInSection,
    CostOfLiving,
    AdmissionStats,
    Visa,
    WorkOpportunity,
)

# === INLINES ===

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

# === MODEL ADMINS ===

@admin.register(university)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'establish_year', 'location', 'get_country', 'status')
    list_filter = ('type', 'status', 'location')
    search_fields = ('name', 'location__city', 'location__state', 'location__country')
    raw_id_fields = ('location',)
    ordering = ('name',)
    fields = (
        'cover_url', 'cover_origin', 'name', 'type', 'establish_year', 'location',
        'about', 'admission_requirements', 'location_map_link', 'avg_acceptance_rate',
        'avg_tution_fee', 'review_rating', 'status'
    )
    inlines = [
        StatsInline, VideosInline, FaqsInline, UniversityRankingInline,
        UniContactInline, CommissionInline, MouInline,
        AdmissionStatsInline, VisaInline, WorkOpportunityInline
    ]

    def get_country(self, obj):
        return obj.location.country
    get_country.short_description = 'Country'

@admin.register(location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'city', 'state', 'country')
    search_fields = ('city', 'state', 'country')

@admin.register(stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'value', 'university')
    search_fields = ('name', 'value', 'university__name')
    raw_id_fields = ('university',)

@admin.register(videos_links)
class VideosLinksAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'university')
    search_fields = ('url', 'university__name')
    raw_id_fields = ('university',)

@admin.register(ranking_agency)
class RankingAgencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'logo')
    search_fields = ('name',)

@admin.register(university_ranking)
class UniversityRankingAdmin(admin.ModelAdmin):
    list_display = ('id', 'university', 'ranking_agency', 'rank')
    list_filter = ('ranking_agency',)
    search_fields = ('university__name', 'ranking_agency__name')
    raw_id_fields = ('university', 'ranking_agency')

@admin.register(faqs)
class FaqsAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'university')
    search_fields = ('question', 'university__name')
    raw_id_fields = ('university',)

@admin.register(Uni_contact)
class UniContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'designation', 'email', 'phone', 'university')
    search_fields = ('name', 'email', 'phone', 'university__name')
    raw_id_fields = ('university',)

@admin.register(commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'inPercentage', 'inAmount', 'partner_agency', 'university')
    search_fields = ('partner_agency__name', 'university__name')
    raw_id_fields = ('partner_agency', 'university')

@admin.register(Partner_Agency)
class PartnerAgencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'partner_type')
    list_filter = ('partner_type',)
    search_fields = ('name',)

@admin.register(mou)
class MouAdmin(admin.ModelAdmin):
    list_display = ('id', 'MoU_copy_link', 'SigningDate', 'ExpiryDate', 'Duration_in_years', 'Duration_in_Months', 'university')
    search_fields = ('MoU_copy_link', 'university__name')
    list_filter = ('SigningDate', 'ExpiryDate')
    raw_id_fields = ('university',)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(WhyStudyInSection)
class WhyStudyInSectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'content')
    search_fields = ('country__name',)
    raw_id_fields = ('country',)

@admin.register(CostOfLiving)
class CostOfLivingAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'total_min', 'total_max')
    search_fields = ('country__name',)
    raw_id_fields = ('country',)

@admin.register(AdmissionStats)
class AdmissionStatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'university', 'admission_type', 'GPA_min', 'GPA_max')
    search_fields = ('university__name',)
    raw_id_fields = ('university',)

@admin.register(Visa)
class VisaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type_of_visa', 'cost', 'university')
    search_fields = ('name', 'type_of_visa', 'university__name')
    raw_id_fields = ('university',)
    list_filter = ('type_of_visa',)

@admin.register(WorkOpportunity)
class WorkOpportunityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'university')
    search_fields = ('name', 'university__name')
    raw_id_fields = ('university',)