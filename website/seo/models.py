from django.db import models


class InstaEmbed(models.Model):
    embed_text = models.TextField(
        verbose_name="Embed HTML",
        help_text = "Paste the Instagram embed HTML blockquote here (without the <code>&lt;script&gt;</code> tag)."
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Only active embeds will be exposed via the API.",
    )

    class Meta:
        verbose_name = "Instagram Embed"
        verbose_name_plural = "Instagram Embeds"

    def __str__(self):
        # Show a short preview in Django Admin
        return self.embed_text[:60] + "..."
