# test3.py - Django Shell Script with Case-Insensitive Search and Default Values

import os
import csv
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Q
from course.models import Course
from university.models import university

def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_str(value, default='NA'):
    return str(value).strip() if value else default

def import_courses():
    base_dir = '/run/media/mayank/53e82406-7352-475e-956c-829701cfe78f/Projects/GRAD GLOBE/Country Wise Bachelor'
    processed_files = 0
    created_courses = 0
    skipped_universities = 0

    # Use transaction for better performance
    with transaction.atomic():
        # Walk through all country directories
        for country_dir in os.listdir(base_dir):
            country_path = os.path.join(base_dir, country_dir)
            
            if not os.path.isdir(country_path):
                continue
                
            # Process each CSV file in the directory
            for filename in os.listdir(country_path):
                if not filename.endswith('.csv'):
                    continue
                    
                file_path = os.path.join(country_path, filename)
                processed_files += 1
                print(f"Processing file {processed_files}: {filename}")
                
                with open(file_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    
                    for row in reader:
                        try:
                            # Case-insensitive university search
                            try:
                                university_obj = university.objects.get(
                                    Q(name__iexact=row['school_name']) | 
                                    Q(alias__iexact=row.get('alias', ''))
                            except university.DoesNotExist:
                                print(f"Warning: University not found (tried: {row['school_name']}, {row.get('alias', '')})")
                                skipped_universities += 1
                                continue
                            except university.MultipleObjectsReturned:
                                university_obj = university.objects.filter(
                                    Q(name__iexact=row['school_name']) | 
                                    Q(alias__iexact=row.get('alias', ''))).first()
                                print(f"Warning: Multiple universities found, using first match for {row['school_name']}")

                            # Convert duration to years with safe defaults
                            duration = safe_int(row.get('duration', 12))
                            duration_unit = row.get('duration_unit', 'months').lower()
                            duration_in_years = round(duration / 12, 1) if duration_unit == 'months' else duration

                            # Parse intake dates with fallbacks
                            intakes = [x.strip() for x in row.get('intake', '').split(',') if x.strip()]
                            next_intake_str = intakes[0] if intakes else None
                            
                            if next_intake_str:
                                try:
                                    next_intake = datetime.strptime(f"{next_intake_str} {datetime.now().year}", "%b %Y").date()
                                except ValueError:
                                    next_intake = datetime.now().date() + timedelta(days=90)
                            else:
                                next_intake = datetime.now().date() + timedelta(days=90)
                            
                            # Calculate deadlines with fallbacks
                            submission_deadline = next_intake - timedelta(days=30)
                            offshore_deadline = next_intake - timedelta(days=45)

                            # Prepare all fields with defaults
                            course_data = {
                                'program_level': 'bachelors',
                                'duration_in_years': duration_in_years,
                                'next_intake': next_intake,
                                'about': safe_str(row.get('about', f"Information about {row['program_name']}")),
                                'start_date': next_intake,
                                'submission_deadline': submission_deadline,
                                'offshore_onshore_deadline': offshore_deadline,
                                'brochure_url': safe_str(row.get('program_url', 'NA')),
                            }

                            # Create course with all fields
                            course, created = Course.objects.get_or_create(
                                program_name=safe_str(row['program_name']),
                                university=university_obj,
                                defaults=course_data
                            )
                            
                            if created:
                                created_courses += 1
                                print(f"Created: {course.program_name} at {university_obj.name}")
                                
                        except Exception as e:
                            print(f"Error processing row: {dict(row)}")
                            print(f"Error details: {str(e)}")
                            continue

    # Print summary
    print("\nImport completed:")
    print(f"- Processed {processed_files} files")
    print(f"- Created {created_courses} new course records")
    print(f"- Skipped {skipped_universities} courses due to missing universities")


import_courses()