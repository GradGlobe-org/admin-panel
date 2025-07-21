import json
from django.core.exceptions import ObjectDoesNotExist
from university.models import location, university, stats, videos_links, faqs, university_ranking, Uni_contact, AdmissionStats, Visa, WorkOpportunity, ranking_agency

# Load JSON data from file
json_file_path = 'data.json'  # Adjust path as needed
try:
    with open(json_file_path, 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    print(f"Error: File {json_file_path} not found.")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: Invalid JSON format in {json_file_path}.")
    exit(1)

# Step 1: Handle Location
location_data = data['General']['location']
try:
    # Check if location already exists
    loc = location.objects.get(
        city=location_data['city'],
        state=location_data['state'],
        country=location_data['country']
    )
except ObjectDoesNotExist:
    # Create new location if it doesn't exist
    loc = location.objects.create(
        city=location_data['city'],
        state=location_data['state'],
        country=location_data['country']
    )

# Step 2: Create or Update University
uni_data = data['General']
try:
    uni = university.objects.get(name=uni_data['name'])
    # Update existing university
    uni.cover_url = uni_data['cover_url']
    uni.cover_origin = uni_data['cover_origin']
    uni.type = uni_data['type']
    uni.establish_year = uni_data['establish_year']
    uni.location = loc
    uni.about = uni_data['about']
    uni.admission_requirements = uni_data['admission_requirements']
    uni.location_map_link = uni_data['location_map_link']
    uni.review_rating = uni_data['review_rating']
    uni.avg_acceptance_rate = uni_data['avg_acceptance_rate']
    uni.avg_tution_fee = uni_data['avg_tution_fee']
    uni.status = uni_data['status']
    uni.save()
except ObjectDoesNotExist:
    # Create new university
    uni = university.objects.create(
        cover_url=uni_data['cover_url'],
        cover_origin=uni_data['cover_origin'],
        name=uni_data['name'],
        type=uni_data['type'],
        establish_year=uni_data['establish_year'],
        location=loc,
        about=uni_data['about'],
        admission_requirements=uni_data['admission_requirements'],
        location_map_link=uni_data['location_map_link'],
        review_rating=uni_data['review_rating'],
        avg_acceptance_rate=uni_data['avg_acceptance_rate'],
        avg_tution_fee=uni_data['avg_tution_fee'],
        status=uni_data['status']
    )

# Step 3: Update Statistics
# Clear existing statistics
uni.statistics.all().delete()
for stat in data['Statistics']:
    stats.objects.create(
        university=uni,
        name=stat['name'],
        value=stat['value']
    )

# Step 4: Update Video Links
# Clear existing video links
uni.video_links.all().delete()
for video in data['Video Links']:
    videos_links.objects.create(
        university=uni,
        url=video['url']
    )

# Step 5: Update FAQs
# Clear existing FAQs
uni.faqs.all().delete()
for faq in data['FAQs']:
    faqs.objects.create(
        university=uni,
        question=faq['question'],
        answer=faq['answer']
    )

# Step 6: Update University Rankings
# Clear existing rankings
uni.rankings.all().delete()
# Create a dictionary to store the latest ranking per agency
latest_rankings = {}
for ranking in data['University Rankings']:
    agency_id = ranking['ranking_agency_id']
    # Update if this is the first ranking or a more recent year
    if agency_id not in latest_rankings or ranking['year'] > latest_rankings[agency_id]['year']:
        latest_rankings[agency_id] = ranking

# Create rankings for the latest year only
for ranking in latest_rankings.values():
    try:
        agency = ranking_agency.objects.get(id=ranking['ranking_agency_id'])
        university_ranking.objects.create(
            university=uni,
            ranking_agency=agency,
            rank=ranking['rank']
        )
    except ObjectDoesNotExist:
        print(f"Ranking agency with ID {ranking['ranking_agency_id']} not found, skipping ranking.")

# Step 7: Update University Contacts
# Clear existing contacts
uni.contacts.all().delete()
for contact in data['University Contacts']:
    Uni_contact.objects.create(
        university=uni,
        name=contact['name'],
        designation=contact['designation'],
        email=contact['email'],
        phone=contact['phone']
    )

# Step 8: Update Admission Stats
# Clear existing admission stats
uni.admissionstats_set.all().delete()
for admission in data['Admission Stats']:
    AdmissionStats.objects.create(
        university=uni,
        admission_type=admission['admission_type'],
        GPA_min=int(admission['GPA_min']),  # Convert to int to match PositiveIntegerField
        GPA_max=int(admission['GPA_max']),  # Convert to int to match PositiveIntegerField
        SAT_min=admission['SAT_min'],
        SAT_max=admission['SAT_max'],
        ACT_min=admission['ACT_min'],
        ACT_max=admission['ACT_max'],
        IELTS_min=admission['IELTS_min'],
        IELTS_max=admission['IELTS_max']
    )

# Step 9: Update Visas
# Clear existing visas
uni.visa_set.all().delete()
for visa in data['Visas']:
    Visa.objects.create(
        university=uni,
        name=visa['name'],
        cost=visa['cost'],
        type_of_visa=visa['type_of_visa'],
        describe=visa['describe']
    )

# Step 10: Update Work Opportunities
# Clear existing work opportunities
uni.workopportunity_set.all().delete()
for work in data['Work Opportunities']:
    WorkOpportunity.objects.create(
        university=uni,
        name=work['name']
    )

print(f"Successfully updated/created data for {uni.name}")