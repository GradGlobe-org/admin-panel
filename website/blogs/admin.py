from django.contrib import admin
from .models import Post
from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from website.utils import upload_file_to_drive_public
from django.core.exceptions import ValidationError
from django.utils.html import format_html
from authentication.models import Employee
from django.shortcuts import render

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
    featured_image_upload = forms.ImageField(
        required=False,
        label="Upload Image",
        help_text="Upload an image (jpg, jpeg, png, webp, max 1MB)"
    )

    class Meta:
        model = Post
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        link = cleaned_data.get("featured_image")
        upload = cleaned_data.get("featured_image_upload")

        # Either link or upload, not both
        if link and upload:
            raise ValidationError("You can either provide a featured image link OR upload an image, not both.")
        return cleaned_data

    def clean_featured_image_upload(self):
        image = self.cleaned_data.get("featured_image_upload")
        if image and image.size > 1 * 1024 * 1024:
            raise ValidationError("Image file size must be under 1 MB.")
        return image

    def save(self, commit=True):
        obj = super().save(commit=False)
        upload_file = self.cleaned_data.get("featured_image_upload")

        if upload_file and isinstance(upload_file, InMemoryUploadedFile):
            drive_file_id, generated_uuid = upload_file_to_drive_public(upload_file)
            obj.image_uuid = generated_uuid
            obj.google_file_id = drive_file_id
            # Just save base URL without w/h
            obj.featured_image = f"/blog/images?id={drive_file_id}"

        # If user provided only a link, leave it as-is
        elif self.cleaned_data.get("featured_image") and obj.google_file_id:
            obj.featured_image = f"/blog/images?id={obj.google_file_id}"
        else:
            obj.image_uuid = None
            obj.google_file_id = None

        if commit:
            obj.save()
        return obj


class AuthorChangeForm(forms.Form):
    author = forms.ModelChoiceField(
        queryset=Employee.objects.all(),
        label="Select new author"
    )

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = ('id', 'title', 'slug', 'status', 'author_name', 'created_at', 'view_count', 'list_image_thumbnail')
    search_fields = ('title', 'content', 'author__first_name', 'author__last_name')
    list_filter = ('status', 'created_at', 'author')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'modified_at', 'image_thumbnail')

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'status', 'author')
        }),
        ('Content & Media', {
            'fields': ('content', 'featured_image', 'featured_image_upload', 'image_thumbnail'),
        }),
        ('SEO', {
            'fields': ('meta_keyword', 'meta_description'),
            'classes': ('collapse',),
        }),
        ('Meta Data', {
            'fields': ('view_count', 'created_at', 'modified_at'),
            'classes': ('collapse',),
        }),
    )

    # ✅ Bulk actions
    actions = ["make_published", "make_draft", "change_author_action"]

    def make_published(self, request, queryset):
        updated = queryset.update(status="PUBLISHED")
        self.message_user(request, f"{updated} post(s) were marked as Published.")
    make_published.short_description = "Mark selected posts as Published"

    def make_draft(self, request, queryset):
        updated = queryset.update(status="DRAFT")
        self.message_user(request, f"{updated} post(s) were marked as Draft.")
    make_draft.short_description = "Mark selected posts as Draft"

    # ✅ Custom Change Author Action
    def change_author_action(self, request, queryset):
        if "apply" in request.POST:
            form = AuthorChangeForm(request.POST)
            if form.is_valid():
                new_author = form.cleaned_data["author"]
                updated = queryset.update(author=new_author)
                self.message_user(request, f"{updated} post(s) were reassigned to {new_author}.")
                return None
        else:
            form = AuthorChangeForm()

        return render(request, "admin/change_author.html", {
            "posts": queryset,
            "form": form,
            "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
        })
    change_author_action.short_description = "Change author of selected posts"

    # Helpers
    def author_name(self, obj):
        return obj.author.name
    author_name.short_description = 'Author'

    def list_image_thumbnail(self, obj):
        url = obj.featured_image
        if url and url.startswith("/blog/images?id="):
            url = f"{url}&w=250&h=250"
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit:cover; border-radius:6px;" />', url
            )
        elif url:
            return format_html(
                '<img src="{}" width="100" height="100" style="object-fit:cover; border-radius:6px;" />', url
            )
        return "(No image)"
    list_image_thumbnail.short_description = "Preview"

    def image_thumbnail(self, obj):
        url = obj.featured_image
        if url and url.startswith("/blog/images?id="):
            url = f"{url}&w=250&h=250"
            return format_html(
                '<img src="{}" style="max-width:250px; height:auto; border-radius:6px;" />', url
            )
        elif url:
            return format_html(
                '<img src="{}" style="max-width:250px; height:auto; border-radius:6px;" />', url
            )
        return "(No image)"
    image_thumbnail.short_description = "Preview"
