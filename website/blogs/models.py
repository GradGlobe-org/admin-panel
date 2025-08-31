from django.db import models
from authentication.models import Employee as EMPLOYEE_MODEL
from slugify import slugify  # using `python-slugify`

class Post(models.Model):
    STATUS = (
        ("DRAFT", "DRAFT"),
        ("PUBLISHED", "PUBLISHED"),
        ("PRIVATE", "PRIVATE"),
    )

    title = models.CharField(max_length=1000)
    content = models.TextField()
    featured_image = models.TextField(default="no image")
    author = models.ForeignKey(EMPLOYEE_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    modified_at = models.DateTimeField(auto_now=True, verbose_name="Last Modified At")
    status = models.CharField(max_length=50, choices=STATUS)
    meta_keyword = models.TextField(blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=1000, unique=True, blank=True, null=True)
    view_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
