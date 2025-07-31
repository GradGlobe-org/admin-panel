# update_university_covers_shell.py
import os
import django
from serpapi import GoogleSearch
from urllib.parse import urlparse

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')  # Updated to match your provided settings
django.setup()

from university.models import university  # Import the lowercase university model

# SerpAPI parameters
serpapi_params = {
    "engine": "google_images",
    "ijn": "0",
    "api_key": "1d365ffaff28f8c2bc333b0a53fbc465c0ea86683f16792ba28a17fe881e4555"
}

# Get all published universities
published_universities = university.objects.filter(status="PUBLISH")

if not published_universities:
    print("No published universities found.")
    exit()

updated_count = 0
failed_count = 0

for uni in published_universities:
    try:
        # Update search query with university name
        serpapi_params["q"] = uni.name

        # Perform search
        search = GoogleSearch(serpapi_params)
        results = search.get_dict()

        # Get first image result
        images = results.get("images_results", [])
        if images:
            first_image = images[0]
            cover_url = first_image.get("original")  # Use original image URL for cover_url
            source_url = first_image.get("link")  # Get the source website link

            # Extract domain from source_url for cover_origin
            if source_url:
                parsed_url = urlparse(source_url)
                cover_origin = parsed_url.netloc  # Extract domain (e.g., www.example.com)
            else:
                cover_origin = "Unknown"

            # Update university
            uni.cover_url = cover_url
            uni.cover_origin = cover_origin
            uni.save()

            print(f"Updated {uni.name}: cover_url={cover_url}, cover_origin={cover_origin}")
            updated_count += 1
        else:
            print(f"No images found for {uni.name}")
            failed_count += 1

    except Exception as e:
        print(f"Error updating {uni.name}: {str(e)}")
        failed_count += 1

# Summary
print(f"Update complete. {updated_count} universities updated, {failed_count} failed.")