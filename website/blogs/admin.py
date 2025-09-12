from django.contrib import admin
from .models import Post
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from website.utils import upload_file_to_drive_public  # your website.utils with upload_file_to_drive_public
from django.core.exceptions import ValidationError
from django.utils.html import format_html

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

class PostAdminForm(forms.ModelForm):
    # Only allow images (max 1MB)
    featured_image = forms.ImageField(
        required=False,
        help_text="Upload an image (jpg, jpeg, png, webp, max 1MB)"
    )

    class Meta:
        model = Post
        fields = '__all__'

    def clean_featured_image(self):
        image = self.cleaned_data.get("featured_image")

        if image:
            if image.size > 1 * 1024 * 1024:  # 1 MB
                raise ValidationError("Image file size must be under 1 MB.")
        return image

    def save(self, commit=True):
        obj = super().save(commit=False)

        upload_file = self.cleaned_data.get("featured_image")
        if upload_file and isinstance(upload_file, InMemoryUploadedFile):
            drive_file_id, generated_uuid = upload_file_to_drive_public(upload_file)

            obj.image_uuid = generated_uuid
            obj.google_file_id = drive_file_id

        if commit:
            obj.save()
        return obj


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = (
        'id', 'title', 'slug', 'status', 'author_name',
        'created_at', 'view_count', 'image_thumbnail'
    )
    search_fields = ('title', 'content', 'author__first_name', 'author__last_name')
    list_filter = ('status', 'created_at', 'author')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def author_name(self, obj):
        return f"{obj.author.name}"
    author_name.short_description = 'Author'

    def image_thumbnail(self, obj):
        if obj.google_file_id:
            url = f"https://drive.google.com/thumbnail?id={obj.google_file_id}"
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit:cover; border-radius:6px;" />',
                url
            )
        return "(No image)"
    image_thumbnail.allow_tags = True
    image_thumbnail.short_description = "Preview"

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'status', 'author')
        }),
        ('Content & Media', {
            'fields': ('content', 'featured_image', 'image_thumbnail'),
        }),
        ('SEO', {
            'fields': ('meta_keyword', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('Meta Data', {
            'fields': ('view_count', 'created_at', 'modified_at'),
        }),
    )
    readonly_fields = ('created_at', 'modified_at', 'image_thumbnail')