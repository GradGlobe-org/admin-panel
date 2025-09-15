import csv
from django.db.models import Q
from university.models import (  # replace app_name with your Django app name
    university,
    AdmissionStats,
    Visa,
    WorkOpportunity,
    Uni_contact,
    stats,
    videos_links,
    university_ranking,
    faqs,
)

# Output file
outfile = "university_data_gaps.csv"

# Fields of university model to check for null/blank
UNI_FIELDS = [
    "cover_url",
    "cover_origin",
    "name",
    "type",
    "establish_year",
    "location",
    "about",
    "admission_requirements",
    "location_map_link",
    "review_rating",
    "avg_acceptance_rate",
    "avg_tution_fee",
]

# Related models to check
RELATED_MODELS = {
    "AdmissionStats": AdmissionStats,
    "Visa": Visa,
    "WorkOpportunity": WorkOpportunity,
    "Uni_contact": Uni_contact,
    "Stats": stats,
    "VideoLinks": videos_links,
    "UniversityRanking": university_ranking,
    "FAQs": faqs,
}


def check_university(u):
    """Return a list of missing fields and related data for a university"""
    missing = []

    # Check direct fields
    for field in UNI_FIELDS:
        value = getattr(u, field, None)
        if value in (None, "", 0):
            missing.append(field)

    # Check related models (existence)
    for label, model in RELATED_MODELS.items():
        if not model.objects.filter(university=u).exists():
            missing.append(label)

    return missing


with open(outfile, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["University", "Missing Fields/Relations"])

    for u in university.objects.all():
        missing = check_university(u)

        # Print progress in console
        if missing:
            print(f"Processing: {u.name} → Missing: {', '.join(missing)}")
            writer.writerow([u.name, ", ".join(missing)])
        else:
            print(f"Processing: {u.name} → All Data Present")
            writer.writerow([u.name, "All Data Present"])

print(f"\n✅ Report written to {outfile}")
