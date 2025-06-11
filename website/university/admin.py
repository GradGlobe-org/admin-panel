from django.contrib import admin
from .models import (
    location,
    university,
    stats,
    videos_links,
    ranking_agency,
    university_ranking,
    faqs
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

# Inline for Rankings
class UniversityRankingInline(admin.TabularInline):
    model = university_ranking
    extra = 1

@admin.register(university)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'establish_year', 'location')
    list_filter = ('type', 'location')
    search_fields = ('name',)
    inlines = [StatsInline, VideosInline, FaqsInline, UniversityRankingInline]

# Register other models normally

@admin.register(location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(stats)
class StatsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'value', 'university')
    search_fields = ('name',)

@admin.register(videos_links)
class VideosLinksAdmin(admin.ModelAdmin):
    list_display = ('id', 'url', 'university')

@admin.register(ranking_agency)
class RankingAgencyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'logo')
    search_fields = ('name',)

@admin.register(university_ranking)
class UniversityRankingAdmin(admin.ModelAdmin):
    list_display = ('id', 'university', 'ranking_agency', 'rank')

@admin.register(faqs)
class FaqsAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'university')
