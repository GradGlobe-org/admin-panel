import csv
from university.models import university

# Get universities with no AdmissionStats
universities_without_stats = university.objects.filter(admissionstats__isnull=True)

# Export to CSV
with open("universities_without_admission_stats.csv", mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["ID", "Name"])  # header row
    for uni in universities_without_stats:
        writer.writerow([uni.id, uni.name])

print(f"✅ Exported {universities_without_stats.count()} universities to universities_without_admission_stats.csv")
