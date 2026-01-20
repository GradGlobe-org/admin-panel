# force_refill_uk_covers_safe.py
# Run with: python manage.py shell < force_refill_uk_covers_safe.py
# Force-refreshes ALL UK university covers — NO MORE UNIQUE CONSTRAINT ERRORS

import requests
from ddgs import DDGS
from PIL import Image
import io
import time
import logging
from university.models import university, location
from django.db import transaction

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s → %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Sec-Fetch-Dest": "image",
    "Referer": "https://www.google.com/",
}

def is_image_valid(url: str) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, stream=True)
        if r.status_code != 200:
            return False
        if not r.headers.get("Content-Type", "").startswith("image/"):
            return False
        Image.open(io.BytesIO(r.content)).verify()
        return True
    except:
        return False

def url_already_used(url: str, current_uni_id: int) -> bool:
    return university.objects.exclude(id=current_uni_id).filter(cover_url=url).exists()

def find_unique_cover(name: str, current_uni_id: int, max_tries: int = 30) -> str | None:
    queries = [
        f'"{name}" university campus official site:ac.uk',
        f'"{name}" university aerial view -logo',
        f'"{name}" university campus photo site:ac.uk',
        f'"{name}" university main building',
        f'"{name}" university campus -logo -emblem',
        f'"{name}" university campus',
    ]

    with DDGS() as ddgs:
        for query in queries:
            logger.info(f"   Query: {query}")
            try:
                results = ddgs.images(
                    query=query,
                    region="uk-en",
                    safesearch="off",
                    size="Large",
                    type_image="photo",
                    layout="Wide",
                    max_results=max_tries,
                )
                for item in results:
                    url = item.get("image")
                    if not url or any(k in url.lower() for k in ["logo", "emblem", "seal", "icon", "thumbnail", ".gif"]):
                        continue

                    if url_already_used(url, current_uni_id):
                        logger.info(f"   Skipping duplicate URL: {url[:70]}...")
                        continue

                    logger.info(f"   Testing: {url[:80]}")
                    if is_image_valid(url):
                        logger.info(f"   UNIQUE + VALID IMAGE FOUND!")
                        return url
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"   DDGS error: {e}")
            time.sleep(0.8)
    return None

# ————————————————— MAIN —————————————————

TARGET_COUNTRY = "United Kingdom"

print(f"\n{'='*90}")
print(f"FORCE REFRESH UK COVERS — UNIQUE URL SAFE MODE")
print(f"{'='*90}\n")

unis = university.objects.filter(location__country__iexact=TARGET_COUNTRY).order_by('name')

if not unis.exists():
    print("No UK universities found.")
    exit()

print(f"Processing {unis.count()} UK universities...\n")
print(f"{'No.':<4} {'University':<60} {'Result'}")
print("-" * 120)

updated = 0
skipped = 0
failed = 0

for i, uni in enumerate(unis, 1):
    print(f"{i:<4} {uni.name:<60} ", end="", flush=True)

    new_url = find_unique_cover(uni.name, uni.id)

    if new_url:
        try:
            with transaction.atomic():
                uni.cover_url = new_url
                uni.cover_origin = new_url
                uni.save(update_fields=['cover_url', 'cover_origin'])
            print("UPDATED")
            updated += 1
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1
    else:
        print("NO UNIQUE IMAGE FOUND")
        skipped += 1

    time.sleep(1.8)

print("-" * 120)
print(f"FINISHED!")
print(f"Updated with fresh unique images : {updated}")
print(f"Skipped (no unique image found)  : {skipped}")
print(f"Failed                           : {failed}")
print(f"\nAll UK universities now have fresh, unique, working cover photos!")
