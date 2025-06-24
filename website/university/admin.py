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
)

# Inline for Stats
class StatsInline(admin.TabularInline):
    model = stats
    extra = 1

# Inline for Videos
class VideosInline(admin.TabularInline):
    model = videos_links
    extra = 1

# Inline for FAQs
class FaqsInline(admin.TabularInline):
    model = faqs
    extra = 1

# Inline for University Rankings
class UniversityRankingInline(admin.TabularInline):
    model = university_ranking
    extra = 1

# Inline for University Contacts
class UniContactInline(admin.TabularInline):
    model = Uni_contact
    extra = 1

# Inline for Commissions
class CommissionInline(admin.TabularInline):
    model = commission
    extra = 1

# Inline for MoUs
class MouInline(admin.TabularInline):
    model = mou
    extra = 1
    fields = ('MoU_copy_link', 'SigningDate', 'ExpiryDate', 'Duration_in_years', 'Duration_in_Months')

# University Admin
@admin.register(university)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'establish_year', 'location', 'status')
    list_filter = ('type', 'status', 'location')
    search_fields = ('name', 'location__city', 'location__state')
    raw_id_fields = ('location',)
    inlines = [StatsInline, VideosInline, FaqsInline, UniversityRankingInline, UniContactInline, CommissionInline, MouInline]
    ordering = ('name',)
    fields = ('cover_url', 'cover_origin', 'name', 'type', 'establish_year', 'location', 'about', 'admission_requirements', 'location_map_link', 'status')

# Location Admin
@admin.register(location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'city', 'state')
    search_fields = ('city', 'state')

# Stats Admin
@admin.register(stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'value', 'university')
    search_fields = ('name', 'university__name')
    raw_id_fields = ('university',)

# Videos Links Admin
@admin.register(videos_links)
class VideosLinksAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'university')
    search_fields = ('url', 'university__name')
    raw_id_fields = ('university',)

# Ranking Agency Admin
@admin.register(ranking_agency)
class RankingAgencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'logo')
    search_fields = ('name',)

# University Ranking Admin
@admin.register(university_ranking)
class UniversityRankingAdmin(admin.ModelAdmin):
    list_display = ('id', 'university', 'ranking_agency', 'rank')
    list_filter = ('ranking_agency',)
    search_fields = ('university__name', 'ranking_agency__name')
    raw_id_fields = ('university', 'ranking_agency')

# FAQs Admin
@admin.register(faqs)
class FaqsAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'university')
    search_fields = ('question', 'university__name')
    raw_id_fields = ('university',)

# University Contact Admin
@admin.register(Uni_contact)
class UniContactAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'designation', 'email', 'phone', 'university')
    search_fields = ('name', 'email', 'phone', 'university__name')
    raw_id_fields = ('university',)

# Commission Admin
@admin.register(commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'inPercentage', 'inAmount', 'partner_agency', 'university')
    search_fields = ('partner_agency__name', 'university__name')
    raw_id_fields = ('partner_agency', 'university')

# Partner Agency Admin
@admin.register(Partner_Agency)
class PartnerAgencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

# MoU Admin
@admin.register(mou)
class MouAdmin(admin.ModelAdmin):
    list_display = ('id', 'MoU_copy_link', 'SigningDate', 'ExpiryDate', 'Duration_in_years', 'Duration_in_Months', 'university')
    search_fields = ('MoU_copy_link', 'university__name')
    raw_id_fields = ('university',)
    list_filter = ('SigningDate', 'ExpiryDate')