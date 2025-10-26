import csv
from django.conf import settings
from django.db.models import Count
from university.models import university

# Output CSV path
output_path = settings.BASE_DIR / "universities_without_workopportunity.csv"

# Query: find universities with 0 related workopportunity entries
universities_without_workopportunity = (
    university.objects.annotate(workopportunity_count=Count("workopportunity"))
    .filter(workopportunity_count=0)
    .select_related("location")
)

# Write to CSV
with open(output_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(
        [
            "id",
            "University Name",
            "Type",
            "Establish Year",
            "City",
            "State",
            "Country",
            "Review Rating",
            "Status",
        ]
    )

    for uni in universities_without_workopportunity:
        writer.writerow(
            [
                uni.id,
                uni.name,
                uni.type,
                uni.establish_year,
                uni.location.city if uni.location else "",
                uni.location.state if uni.location else "",
                uni.location.country if uni.location else "",
                uni.review_rating,
                uni.status,
            ]
        )

print(
    f"✅ Exported {universities_without_workopportunity.count()} universities without work opportunity info to:"
)
print(output_path)

