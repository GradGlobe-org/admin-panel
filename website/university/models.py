from django.db import models
from django.core.validators import MinValueValidator


class location(models.Model):
    city = models.CharField(max_length=1000, db_index=True, help_text="Name of the city")
    state = models.CharField(max_length=1000, db_index=True, help_text="Name of the state or country")

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        return f"{self.city}, {self.state}"


class university(models.Model):
    cover_url = models.URLField(max_length=1000, unique=True, help_text="Primary cover image URL for the university")
    cover_origin = models.URLField(max_length=1000, help_text="Original source of the cover image")
    name = models.CharField(max_length=1000, unique=True, db_index=True, help_text="Full name of the university")
    
    TYPE = (
        ("PUBLIC", "PUBLIC"),
        ("PRIVATE", "PRIVATE"),
    )
    type = models.CharField(max_length=50, choices=TYPE, db_index=True, help_text="Type of university: Public or Private")

    establish_year = models.PositiveIntegerField(db_index=True, help_text="Year the university was established")

    location = models.ForeignKey(
        location, on_delete=models.PROTECT, related_name='universities', db_index=True,
        help_text="Location where the university is situated"
    )

    about = models.TextField(help_text="Brief description or history of the university")
    admission_requirements = models.TextField(help_text="Eligibility and admission criteria")

    location_map_link = models.URLField(
        max_length=1000, unique=True, db_index=True,
        help_text="Google Maps URL or any map link for the location"
    )

    STATUS = (("DRAFT", "DRAFT"), ("PUBLISH", "PUBLISH"))
    status = models.CharField(max_length=50, choices=STATUS, default="DRAFT", db_index=True, help_text="Publishing status of the university data")

    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name




class Partner_Agency(models.Model):
    name = models.CharField(max_length=200, db_index=True, help_text="Name of the partner agency")

    class Meta:
        verbose_name = "Partner Agency"
        verbose_name_plural = "Partner Agencies"

    def __str__(self):
        return self.name


class commission(models.Model):
    inPercentage = models.PositiveIntegerField(help_text="Commission value in Percentage", blank=True, null=True)
    inAmount = models.PositiveIntegerField(help_text="Commission value in Rupees" , blank=True, null=True)

    partner_agency = models.ForeignKey(Partner_Agency, on_delete=models.PROTECT, help_text="Partner agency for this commission")
    university = models.ForeignKey(university, on_delete=models.CASCADE, help_text="University this commission is assigned to")

    class Meta:
        verbose_name = "Commission"
        verbose_name_plural = "Commissions"

    def __str__(self):
        return f"{self.university.name} - {self.partner_agency.name}"

class mou(models.Model):
    MoU_copy_link=models.URLField(max_length=2000)
    SigningDate = models.DateField()
    ExpiryDate = models.DateField()
    Duration_in_years  = models.PositiveIntegerField(help_text="Duration in Years")
    Duration_in_Months = models.PositiveIntegerField(help_text="Duration in Years")
    university = models.ForeignKey(university, on_delete=models.CASCADE, help_text="University this commission is assigned to")

    class Meta:
        verbose_name = "MoU"
        verbose_name_plural = "MoU"

    def __str__(self):
        return f"{self.university.name} - {self.partner_agency.name}"


class Uni_contact(models.Model):
    name = models.CharField(max_length=200, db_index=True, help_text="Name of the university's contact person")
    designation = models.CharField(max_length=2000)
    email = models.EmailField(max_length=1000, db_index=True, help_text="Official email address")
    phone = models.CharField(max_length=20, db_index=True, help_text="Contact number (include country code)")
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='contacts', db_index=True, help_text="Associated university")

    class Meta:
        verbose_name = "University Contact"
        verbose_name_plural = "University Contacts"

    def __str__(self):
        return f"{self.name} ({self.university.name})"


class stats(models.Model):
    name = models.CharField(max_length=100, db_index=True, help_text="Statistic name (e.g., No. of Students)")
    value = models.CharField(max_length=1000, help_text="Value of the statistic (e.g., 20,000)")
    
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='statistics', db_index=True, help_text="University this statistic is linked to")

    class Meta:
        verbose_name = "Statistic"
        verbose_name_plural = "Statistics"

    def __str__(self):
        return f"{self.name} ({self.university.name})"


class videos_links(models.Model):
    url = models.URLField(max_length=2000, db_index=True, help_text="Video link (e.g., YouTube) related to the university")
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='video_links', db_index=True, help_text="University this video is associated with")

    class Meta:
        verbose_name = "Video Link"
        verbose_name_plural = "Video Links"

    def __str__(self):
        return self.url


class ranking_agency(models.Model):
    name = models.CharField(max_length=1000, unique=True, db_index=True, help_text="Name of the ranking agency (e.g., QS, NIRF)")
    description = models.TextField(help_text="Description of the agency and its methodology")
    logo = models.URLField(max_length=2000, unique=True, db_index=True, help_text="Logo URL of the ranking agency")

    class Meta:
        verbose_name = "Ranking Agency"
        verbose_name_plural = "Ranking Agencies"

    def __str__(self):
        return self.name


class university_ranking(models.Model):
    rank = models.CharField(max_length=50, db_index=True, help_text="Rank assigned to the university")
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='rankings', db_index=True, help_text="University being ranked")
    ranking_agency = models.ForeignKey(ranking_agency, on_delete=models.CASCADE, related_name='university_rankings', db_index=True, help_text="Agency that provided the ranking")

    class Meta:
        verbose_name = "University Ranking"
        verbose_name_plural = "University Rankings"
        unique_together = ('university', 'ranking_agency')

    def __str__(self):
        return f"{self.university.name} - {self.ranking_agency.name}: {self.rank}"


class faqs(models.Model):
    question = models.TextField(unique=True, db_index=True, help_text="Frequently asked question")
    answer = models.TextField(unique=True, help_text="Answer to the question")
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='faqs', db_index=True, help_text="University this FAQ belongs to")

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
