from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

class location(models.Model):
    city = models.CharField(max_length=1000, db_index=True, help_text="Name of the city")
    state = models.CharField(max_length=1000, db_index=True, help_text="Name of the state")
    country = models.CharField(max_length=1000, db_index=True, help_text="Name of the country")
    
    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        return f"{self.city}, {self.state}"


class Country(models.Model):
    name = models.CharField(max_length=1000, unique=True, db_index=True, help_text="Name of the country")

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    def __str__(self):
        return self.name
    
class CountryFAQ(models.Model):
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name="faqs")
    question = models.TextField()
    answer = models.TextField(blank=True)

    def __str__(self):
        return f"{self.country.name}: {self.question[:50]}..."

class WhyStudyInSection(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="study_sections",
        help_text="The country this section is related to"
    )
    content = models.TextField(
        help_text="Detailed content about why to study in this country, comma seperated"
    )

    class Meta:
        verbose_name = "WhyStudyIn"
        verbose_name_plural = "WhyStudyIn Sections"

    def __str__(self):
        return f"{self.country.name}"

# show country specific
class CostOfLiving(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.CASCADE,
        related_name="cost_of_living",
        help_text="The country this cost of living data is related to"
    )
    rent_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum rent cost in USD"
    )
    rent_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum rent cost in USD"
    )
    food_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum food cost in USD"
    )
    food_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum food cost in USD"
    )
    transport_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum transport cost in USD"
    )
    transport_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum transport cost in USD"
    )
    miscellaneous_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum miscellaneous cost in USD"
    )
    miscellaneous_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum miscellaneous cost in USD"
    )
    total_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Minimum total cost of living in USD"
    )
    total_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum total cost of living in USD"
    )

    class Meta:
        verbose_name = "Cost of Living"
        verbose_name_plural = "Costs of Living"

    def __str__(self):
        return f"Cost of Living - {self.country.name}"


class university(models.Model):
    cover_url = models.URLField(max_length=1000, unique=True, help_text="Primary cover image URL for the university")
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
    review_rating = models.DecimalField(
        max_digits=3,  # Total digits (including decimal)
        decimal_places=1,  # One decimal place
        validators=[
            MaxValueValidator(5.0),  # Maximum value of 5.0
            MinValueValidator(0.0)   # Minimum value of 0.0
        ]
    )
    avg_acceptance_rate = models.PositiveIntegerField(help_text="in percentage")
    avg_tution_fee = models.PositiveIntegerField(help_text="in USD")

    STATUS = (("DRAFT", "DRAFT"), ("PUBLISH", "PUBLISH"))
    status = models.CharField(max_length=50, choices=STATUS, default="DRAFT", db_index=True, help_text="Publishing status of the university data")

    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name

class AdmissionStats(models.Model):
    university = models.ForeignKey(university, on_delete=models.CASCADE, help_text="University this Admission stats is assigned to")
    TYPE = (("UNDERGRADUATE","UNDERGRADUATE"), ("GRADUATE","GRADUATE"), ("PHD","Doctorate(PhD)"))
    application_fee = models.PositiveIntegerField(help_text="Application fee for this university")
    admission_type = models.CharField(max_length=50, choices=TYPE)
    GPA_min = models.DecimalField(
        max_digits=9,  # Total digits (including decimal)
        decimal_places=1,  # One decimal place
        validators=[
            
            MinValueValidator(0.0)   # Minimum value of 0.0
        ]
    )
    GPA_max = models.DecimalField(
        max_digits=9,  # Total digits (including decimal)
        decimal_places=1,  # One decimal place
        validators=[
            
            MinValueValidator(0.0)   # Minimum value of 0.0
        ]
    )
    SAT_min = models.DecimalField(
        max_digits=9,  # Total digits (including decimal)
        decimal_places=1,  # One decimal place
        validators=[
            
            MinValueValidator(0.0)   # Minimum value of 0.0
        ]
    )
    SAT_max = models.DecimalField(
        max_digits=9,  # Total digits (including decimal)
        decimal_places=1,  # One decimal place
        validators=[
            
            MinValueValidator(0.0)   # Minimum value of 0.0
        ]
    )
    ACT_min = models.DecimalField(
        max_digits=9,  # Total digits (including decimal)
        decimal_places=1,  # One decimal place
        validators=[
            
            MinValueValidator(0.0)   # Minimum value of 0.0
        ]
    )
    ACT_max = models.DecimalField(
        max_digits=9,  # Total digits (including decimal)
        decimal_places=1,  # One decimal place
        validators=[
            
            MinValueValidator(0.0)   # Minimum value of 0.0
        ]
    )
    IELTS_min = models.DecimalField(
        max_digits=9,  # Total digits (including decimal)
        decimal_places=1,  # One decimal place
        validators=[
            
            MinValueValidator(0.0)   # Minimum value of 0.0
        ]
    )
    IELTS_max = models.DecimalField(
        max_digits=9,  # Total digits (including decimal)
        decimal_places=1,  # One decimal place
        validators=[
            
            MinValueValidator(0.0)   # Minimum value of 0.0
        ]
    )

    class Meta:
        verbose_name = "Admission Stats"
        verbose_name_plural = "Admission Stats"

class CountryVisa(models.Model):
    # Define choices for type_of_visa
    VISA_TYPES = (
        ('TOURIST', 'Tourist Visa'),
        ('BUSINESS', 'Business Visa'),
        ('WORK', 'Work Visa'),
        ('STUDENT', 'Student Visa'),
        ('TRANSIT', 'Transit Visa'),
        ('IMMIGRANT', 'Immigrant Visa'),
        ('FAMILY', 'Family Reunion Visa'),
        ('DIPLOMATIC', 'Diplomatic/Official Visa'),
        ('MEDICAL', 'Medical Visa'),
        ('REFUGEE', 'Refugee/Asylum Visa'),
        ('SPECIAL', 'Special Purpose Visa'),
        ('E_VISA', 'e-Visa/Visa on Arrival'),
    )

    country = models.ForeignKey(
        'Country',
        on_delete=models.CASCADE,
        related_name='visas',
        help_text="Country this visa belongs to"
    )
    name = models.CharField(max_length=1000)  
    cost = models.PositiveIntegerField()
    type_of_visa = models.CharField(
        max_length=20,
        choices=VISA_TYPES,
        help_text="Type of visa"
    )
    describe = models.TextField(max_length=10000)

    class Meta:
        verbose_name = "Visa"
        verbose_name_plural = "Visas"
        unique_together = ('country', 'name')

    def __str__(self):
        return f"{self.name} ({self.type_of_visa})"


class WorkOpportunity(models.Model):
    university = models.ForeignKey(
        university,
        on_delete=models.CASCADE,
        help_text="University this Visa is assigned to"
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Partner_Agency(models.Model):
    name = models.CharField(max_length=200, db_index=True, help_text="Name of the partner agency")
    PARTNER_TYPE  = (("Preferred Partner", "Preferred Partner"),("Standard Partner","Standard Partner"))
    partner_type = models.CharField(max_length=80, choices=PARTNER_TYPE, default="Preferred Partner")
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
        return f"{self.university.name}"


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
    question = models.TextField(db_index=True, help_text="Frequently asked question")
    answer = models.TextField(help_text="Answer to the question")
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='faqs', db_index=True, help_text="University this FAQ belongs to")

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question

class Fact(models.Model):
    name = models.TextField()
    country = models.ForeignKey('Country', on_delete=models.CASCADE, related_name='facts')

    def __str__(self):
        return self.country.name + ": " + self.name.split(",")[0]