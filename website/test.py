import csv
from django.db.models import Count
from university.models import university


def export_university_count_by_country():
    # Aggregate university counts per country
    data = (
        university.objects.values("location__country")
        .annotate(university_count=Count("id"))
        .order_by("location__country")
    )

    # Create the CSV file
    file_path = "university_count_by_country.csv"
    with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Country", "Number of Universities"])  # Header row

        for row in data:
            writer.writerow([row["location__country"], row["university_count"]])

    print(f"CSV exported successfully: {file_path}")


export_university_count_by_country()
