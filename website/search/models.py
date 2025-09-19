from django.db import models


class UnsanitizedSearch(models.Model):
    query = models.TextField(db_index=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "unsanitized_searches"
        verbose_name = "Unsanitized Search"
        verbose_name_plural = "Unsanitized Searches"
        ordering = ["-count"]

    def __str__(self):
        return f"{self.query} ({self.count})"


class SanitizedSearch(models.Model):
    query = models.TextField(unique=True, db_index=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "sanitized_searches"
        verbose_name = "Sanitized Search"
        verbose_name_plural = "Sanitized Searches"
        ordering = ["-count"]

    def __str__(self):
        return f"{self.query} ({self.count})"
