from django.db import models
from university.models import university

class Course(models.Model):
    PROGRAM_LEVEL_CHOICES = (
        ('bachelors', 'Bachelors'),
        ('masters', 'Masters'),
        ('diploma', 'Diploma'),
        ('certificate', 'Certificate'),
        ('phd', 'PhD'),
        ('associate', 'Associate'),
        ('postgraduate_diploma', 'Postgraduate Diploma'),
    )

    university = models.ForeignKey(
        university,
        on_delete=models.PROTECT,
        help_text="The university offering this course."
    )
    program_name = models.CharField(max_length=1000)
    program_level = models.CharField(
        max_length=50,
        choices=PROGRAM_LEVEL_CHOICES,
        default='bachelors',
        help_text="The academic level of the program."
    )
    duration_in_years = models.PositiveIntegerField(
        help_text="Duration of the course in years."
    )
    next_intake = models.DateField(
        help_text="The next intake date for the course."
    )
    about = models.TextField(
        max_length=10000,
        help_text="Detailed information about the course."
    )
    start_date = models.DateField(
        help_text="The official start date of the course."
    )
    submission_deadline = models.DateField(
        help_text="Final date for submitting the application."
    )
    offshore_onshore_deadline = models.DateField(
        help_text="Deadline for offshore/onshore applications."
    )
    brochure_url = models.URLField(
        help_text="Link to the course brochure."
    )

    # New Added Field

    tution_fees = models.PositiveIntegerField(help_text="Cost of the course in USD")

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"
        ordering = ['university', 'program_level', 'start_date']

    def __str__(self):
        return f"{self.university.name} - {self.program_level.title()} Program"


class CostOfLivingBreakdown(models.Model):
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="cost_breakdown",
        help_text="The course to which this cost is associated."
    )
    name = models.CharField(
        max_length=1000,
        help_text="Category name (e.g., Housing, Transport, Food)."
    )
    cost = models.PositiveIntegerField(
        help_text="Cost in USD."
    )

    class Meta:
        verbose_name = "Cost of Living Item"
        verbose_name_plural = "Cost of Living Breakdown"

    def __str__(self):
        return f"{self.name} - ${self.cost} (USD)"
