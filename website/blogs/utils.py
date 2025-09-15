#blogs.utils.py

import requests
from django.http import StreamingHttpResponse, HttpResponse

DRIVE_BASE_URL = "https://drive.google.com/thumbnail?id="

def stream_google_drive_image(file_id, width=None, height=None):
    if not file_id:
        return HttpResponse("Missing Google file ID", status=400)

    # Use Google Drive 'uc' link for faster access
    if width and height:
        url = f"{DRIVE_BASE_URL}{file_id}&sz=w{width}-h{height}"
    else:
        url = f"https://drive.google.com/uc?id={file_id}"

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, stream=True, timeout=10)
    except requests.RequestException as e:
        return HttpResponse(f"Error fetching image: {e}", status=500)

    if resp.status_code != 200:
        return HttpResponse("Image not found", status=resp.status_code)

    content_type = resp.headers.get("Content-Type", "image/jpeg")

    # Stream the response in chunks
    def stream_chunks():
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            if chunk:
                yield chunk

    return StreamingHttpResponse(stream_chunks(), content_type=content_type)
