# export_countries.py
import os
import django
import pandas as pd

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website.settings')  # <-- Change this
django.setup()

from university.models import Country  # <-- Change this

def export_countries_to_csv(output_file='countries.csv'):
    # Get all country names ordered alphabetically
    countries = Country.objects.values_list('name', flat=True).order_by('name')

    # Create DataFrame
    df = pd.DataFrame(list(countries), columns=['Country Name'])

    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"✅ Exported {len(df)} countries to {output_file}")




export_countries_to_csv()
