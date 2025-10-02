from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from .models import Student, StudentLogs

def create_student_log(request, log_text = "Empty Action"):
    # Get authToken from headers (using 'X-Auth-Token' as header name)
    auth_token = request.headers.get('X-Auth-Token')
    
    if not auth_token:
        return False
   
    try:
        # Find student by authToken
        student = Student.objects.get(authToken=auth_token)
        
        # Create new log entry
        StudentLogs.objects.create(
            student=student,
            logs=log_text
        )
    
    except ObjectDoesNotExist:
        return False
    except Exception as e:
        return False


# utils.py
from django.http import StreamingHttpResponse, JsonResponse
from website.utils import get_drive_service
import io


# This thing works good, gets you stored private file uploaded on Google Drive.
# Needs more memory if increasing chunk size
# For this view, at a if 50 students downloads file at same time, 50MB of RAM will be required(where max file_size<1MB(since i set the cap of 1 MB))
def stream_private_drive_file(file_id, filename=None):
    """
    Fast streaming for small private files (<1 MB) via Google Drive API.
    Downloads the file in a single request instead of chunked download.
    """
    service = get_drive_service()

    try:
        # Fetch file metadata for MIME type
        file_meta = service.files().get(fileId=file_id, fields="mimeType").execute()
        content_type = file_meta.get("mimeType", "application/octet-stream")

        # Fetch the file in a single request (fast for small files)
        file_data = service.files().get_media(fileId=file_id).execute()
        fh = io.BytesIO(file_data)
        fh.seek(0)

        # Stream the file to user
        response = StreamingHttpResponse(fh, content_type=content_type)
        if filename:
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        return JsonResponse({"error": f"Unable to fetch file: {e}"}, status=500)