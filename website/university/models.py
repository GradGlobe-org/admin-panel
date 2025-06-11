from django.db import models

class location(models.Model):
    name = models.CharField(max_length=1000)

    class Meta:
        verbose_name = "Location"
        verbose_name_plural = "Locations"

    def __str__(self):
        return self.name


class university(models.Model):
    cover_url = models.URLField(max_length=1000)
    cover_origin = models.URLField(max_length=1000)
    name = models.CharField(max_length=1000)
    TYPE = (
        ("PUBLIC", "PUBLIC"),
        ("PRIVATE", "PRIVATE"),
        ("SEMI GOVERNMENT", "SEMI GOVERNMENT"),
        ("GOVERNMENT", "GOVERNMENT"),
        ("FUNDED", "FUNDED"),
    )
    type = models.CharField(max_length=50, choices=TYPE)
    establish_year = models.DateField()
    location = models.ForeignKey(location, on_delete=models.PROTECT, related_name='university')
    about = models.TextField()
    admission_requirements = models.TextField()

    class Meta:
        verbose_name = "University"
        verbose_name_plural = "Universities"

    def __str__(self):
        return self.name


class stats(models.Model):
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=1000)
    icon = models.TextField()
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='stats')

    class Meta:
        verbose_name = "Statistic"
        verbose_name_plural = "Statistics"

    def __str__(self):
        return f"{self.name} ({self.university.name})"


class videos_links(models.Model):
    url = models.URLField(max_length=2000)
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='video_links')

    class Meta:
        verbose_name = "Video Link"
        verbose_name_plural = "Video Links"

    def __str__(self):
        return self.url


class ranking_agency(models.Model):
    name = models.CharField(max_length=1000)
    description = models.TextField()
    logo = models.URLField(max_length=2000)

    class Meta:
        verbose_name = "Ranking Agency"
        verbose_name_plural = "Ranking Agencies"

    def __str__(self):
        return self.name


class university_ranking(models.Model):
    rank = models.CharField(max_length=50)
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='rankings')
    ranking_agency = models.ForeignKey(ranking_agency, on_delete=models.CASCADE, related_name='university_rankings')

    class Meta:
        verbose_name = "University Ranking"
        verbose_name_plural = "University Rankings"

    def __str__(self):
        return f"{self.university.name} - {self.ranking_agency.name}: {self.rank}"


class faqs(models.Model):
    question = models.TextField()
    answer = models.TextField()
    university = models.ForeignKey(university, on_delete=models.CASCADE, related_name='faqs')

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question
