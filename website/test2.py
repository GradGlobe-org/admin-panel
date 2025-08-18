import pandas as pd
import os
from django.db import transaction
from university.models import university
from course.models import Course

# Directory containing the CSV files
directory = "/run/media/mayank/53e82406-7352-475e-956c-829701cfe78f/Projects/GRAD GLOBE/Country Wise Bachelor"

# Approximate exchange rates to USD (as of a general reference, update as needed)
exchange_rates = {
    'USD': 1.0,
    'UAH': 0.024,  # Ukrainian Hryvnia
    'CHF': 1.15,   # Swiss Franc
    'EUR': 1.11,   # Euro
    'RUB': 0.011,  # Russian Ruble
    'CAD': 0.73,   # Canadian Dollar
    'AED': 0.27,   # UAE Dirham
    'GBP': 1.29,   # British Pound
    'SEK': 0.095,  # Swedish Krona
    'AUD': 0.67,   # Australian Dollar
}

def convert_to_usd(amount, currency):
    """Convert amount from given currency to USD."""
    if pd.isna(amount) or pd.isna(currency) or currency not in exchange_rates:
        return None
    try:
        return int(float(amount) * exchange_rates[currency])
    except (ValueError, TypeError):
        return None

def update_course_tuition():
    """Update tuition fees in USD for courses based on CSV data."""
    updated_count = 0
    not_found_count = 0
    error_count = 0

    # Walk through the directory to find all CSV files
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".csv"):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                try:
                    # Read the CSV file
                    df = pd.read_csv(file_path)
                    for _, row in df.iterrows():
                        program_name = row.get('program_name')
                        tuition_fee = row.get('tuition_fee')
                        tuition_fee_currency = row.get('tuition_fee_currency')
                        school_name = row.get('school_name')

                        # Skip if required fields are missing
                        if pd.isna(program_name) or pd.isna(tuition_fee) or pd.isna(tuition_fee_currency) or pd.isna(school_name):
                            print(f"Skipping row with missing data: {program_name}, {school_name}")
                            continue

                        # Convert tuition fee to USD
                        tuition_usd = convert_to_usd(tuition_fee, tuition_fee_currency)
                        if tuition_usd is None:
                            print(f"Could not convert tuition fee for {program_name}, {school_name}")
                            continue

                        # Find the university
                        try:
                            uni = university.objects.get(name=school_name)
                        except university.DoesNotExist:
                            print(f"University not found: {school_name}")
                            not_found_count += 1
                            continue
                        except university.MultipleObjectsReturned:
                            print(f"Multiple universities found for: {school_name}")
                            error_count += 1
                            continue

                        # Find the course by university and program_name
                        try:
                            course = Course.objects.get(
                                university=uni,
                                program_name=program_name
                            )
                            # Update tuition fee
                            course.tution_fees = tuition_usd
                            course.save()
                            updated_count += 1
                            print(f"Updated {program_name} at {school_name}: ${tuition_usd} USD")
                        except Course.DoesNotExist:
                            print(f"Course not found: {program_name} at {school_name}")
                            not_found_count += 1
                        except Course.MultipleObjectsReturned:
                            print(f"Multiple courses found: {program_name} at {school_name}")
                            error_count += 1

                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    error_count += 1

    print(f"\nSummary:")
    print(f"Updated {updated_count} courses")
    print(f"Not found: {not_found_count} courses/universities")
    print(f"Errors: {error_count} cases")

# Run the update within a transaction for data integrity

update_course_tuition()