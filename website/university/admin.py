from django.contrib import admin
from .models import (
    location,
    university,
    stats,
    videos_links,
    ranking_agency,
    university_ranking,
    faqs,
    Uni_contact,
)

# Inlines
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

@admin.register(university)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'establish_year', 'location', 'status')
    list_filter = ('type', 'status', 'location')
    search_fields = ('name', 'location__city', 'location__state')  # Updated to use city and state
    raw_id_fields = ('location',)
    inlines = [StatsInline, VideosInline, FaqsInline, UniversityRankingInline, UniContactInline]
    ordering = ('name',)

@admin.register(location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'city', 'state')  # Updated to include state
    search_fields = ('city', 'state')  # Updated to search by city and state

@admin.register(stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'value', 'university')
    search_fields = ('name', 'university__name')
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
    list_display = ('id', 'name', 'email', 'phone', 'university')
    search_fields = ('name', 'email', 'phone', 'university__name')
    raw_id_fields = ('university',)