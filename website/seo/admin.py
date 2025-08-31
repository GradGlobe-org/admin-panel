from django.contrib import admin
from .models import InstaEmbed


@admin.register(InstaEmbed)
class InstaEmbedAdmin(admin.ModelAdmin):
    list_display = ("id", "short_preview", "is_active")
    list_filter = ("is_active",)
    search_fields = ("embed_text",)

    def short_preview(self, obj):
        """Show a short snippet of the embed text."""
        return obj.embed_text[:80] + ("..." if len(obj.embed_text) > 80 else "")
    short_preview.short_description = "Embed Preview"