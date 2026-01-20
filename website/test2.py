# test.py
# Lists all universities in a specific country (e.g. United Kingdom)
# Works with your exact models

from university.models import university, location
from django.db.models import Q

# CHANGE THIS TO ANY COUNTRY YOU WANT
TARGET_COUNTRY = "United Kingdom"

print(f"\nSearching for universities in: {TARGET_COUNTRY}")
print("=" * 100)

# Find all location objects where country matches (case-insensitive)
locations_in_country = location.objects.filter(
    country__iexact=TARGET_COUNTRY
).distinct()

if not locations_in_country.exists():
    print(f"No locations found with country = '{TARGET_COUNTRY}'")
    print("\nAvailable countries in your database:")
    countries = location.objects.values('country').distinct().order_by('country')
    for item in countries[:50]:  # Show first 50
        print(f"   • {item['country']}")
    if countries.count() > 50:
        print(f"   ... and {countries.count() - 50} more")
    exit()

# Get all universities in those locations
unis = university.objects.filter(
    location__country__iexact=TARGET_COUNTRY
).order_by('name')

print(f"Found {locations_in_country.count()} location(s) in {TARGET_COUNTRY}")
print(f"Found {unis.count()} universit{'' if unis.count() == 1 else 'ies'} total\n")

if unis.count() == 0:
    print("No universities found.")
else:
    print(f"{'No.':<4} {'University Name':<65} {'City':<25} {'Cover Image'}")
    print("-" * 120)

    for i, uni in enumerate(unis, 1):
        city = uni.location.city if uni.location else "Unknown"
        has_cover = "YES" if uni.cover_url and uni.cover_url.strip() else "NO "
        name_truncated = uni.name[:63] + "..." if len(uni.name) > 63 else uni.name
        print(f"{i:<4} {name_truncated:<65} {city:<25} {has_cover}")

    print("-" * 120)
    filled = unis.filter(cover_url__isnull=False).exclude(cover_url='').count()
    missing = unis.count() - filled
    print(f"TOTAL: {unis.count()} universities")
    print(f"With cover image : {filled}")
    print(f"Missing cover    : {missing} ← run your image filler on these!")
    print(f"Success rate     : {filled/unis.count()*100:.1f}%" if unis.count() > 0 else "")

print("\nDone!")
