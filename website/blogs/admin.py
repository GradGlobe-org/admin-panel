from django.contrib import admin
from .models import Post

class StatusListFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('DRAFT', 'Draft'),
            ('PUBLISHED', 'Published'),
            ('PRIVATE', 'Private'),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())
        return queryset

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'slug', 'status', 'author_name', 'created_at', 'view_count')
    search_fields = ('title', 'content', 'author__first_name', 'author__last_name')
    list_filter = (StatusListFilter, 'created_at', 'author')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def author_name(self, obj):
        return f"{obj.author.name}"
    author_name.short_description = 'Author'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'status', 'author')
        }),
        ('Content & Media', {
            'fields': ('content', 'featured_image'),
        }),
        ('SEO', {
            'fields': ('meta_keyword', 'meta_description'),
            'classes': ('collapse',),  # Optional: makes this section collapsible
        }),
        ('Meta Data', {
            'fields': ('view_count', 'created_at', 'modified_at'),
        }),
    )
    readonly_fields = ('created_at', 'modified_at')
