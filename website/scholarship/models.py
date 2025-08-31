from django.db import models
from university.models import Country, university  # Ensure 'University' is the correct model name


class ExpenseType(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text="Type of expense (e.g. tuition, travel, accommodation)")

    class Meta:
        verbose_name = "Expense Type"
        verbose_name_plural = "Expense Types"
        ordering = ['name']

    def __str__(self):
        return self.name


class Scholarship(models.Model):
    name = models.CharField(max_length=1000, unique=True, help_text="Name of the scholarship")
    awarded_by = models.CharField(max_length=1000, help_text="Organization or institution awarding the scholarship")
    overview = models.TextField(help_text="Short overview of the scholarship")
    details = models.TextField(help_text="Detailed description of the scholarship")
    amount_details = models.TextField(help_text="Information about amount distribution or breakdown")
    course = models.CharField(max_length=100, help_text="Course or program eligible for the scholarship")
    deadline = models.DateField(help_text="Application deadline for the scholarship")
    intake_year = models.DateField(help_text="Year of intake the scholarship applies to")
    amount = models.PositiveIntegerField(help_text="Total amount awarded (in local currency)")
    country = models.ForeignKey(Country, on_delete=models.PROTECT, help_text="Country where the scholarship applies")
    no_of_students = models.CharField(max_length=100, help_text="Number of students who will receive this scholarship")
    type_of_scholarship = models.CharField(max_length=255, help_text="Type/category of the scholarship")
    brochure = models.URLField(max_length=1000, null=True, blank=True, help_text="Link to a PDF brochure or webpage")

    university = models.ManyToManyField(university, related_name='scholarships', help_text="Universities offering or associated with this scholarship")
    eligible_nationalities = models.ManyToManyField(
        Country,
        related_name='eligible_scholarships',
        help_text="Countries whose citizens are eligible for this scholarship"
    )

    class Meta:
        verbose_name = "Scholarship"
        verbose_name_plural = "Scholarships"
        ordering = ['name']

    def __str__(self):
        return self.name


class ScholarshipExpenseCoverage(models.Model):
    scholarship = models.ForeignKey(Scholarship, on_delete=models.CASCADE, related_name='expense_coverages')
    expense_type = models.ForeignKey(ExpenseType, on_delete=models.CASCADE)
    is_covered = models.BooleanField(default=False, help_text="Check if this expense is covered by the scholarship")

    class Meta:
        unique_together = ('scholarship', 'expense_type')
        verbose_name = "Scholarship Expense Coverage"
        verbose_name_plural = "Scholarship Expense Coverages"
        ordering = ['scholarship', 'expense_type']

    def __str__(self):
        return f"{self.scholarship.name} - {self.expense_type.name} - {'Covered' if self.is_covered else 'Not Covered'}"


class FAQ(models.Model):
    question = models.TextField(db_index=True, help_text="Frequently asked question")
    answer = models.TextField(help_text="Answer to the question")
    scholarship = models.ForeignKey(
        Scholarship,
        on_delete=models.CASCADE,
        related_name='faqs',
        db_index=True,
        help_text="Scholarship this FAQ belongs to"
    )

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ['scholarship', 'id']

    def __str__(self):
        return self.question
