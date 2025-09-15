from django.http import JsonResponse
from functools import wraps
import uuid
import os
from functools import wraps
from authentication.models import Employee, Permission
from student.models import Student

def api_key_required(view_func):
    """
    Decorator to verify API key in request headers.
    Expects 'key' header with a valid UUID key.
    Returns JSON responses with appropriate HTTP status codes.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Get API key from headers
        api_key_value = request.headers.get('key')
        
        if not api_key_value:
            return JsonResponse(
                {'error': 'API key required'}, 
                status=401
            )
        
        try:
            # Convert string to UUID object for proper comparison
            api_key_uuid = uuid.UUID(api_key_value)
        except ValueError:
            return JsonResponse(
                {'error': 'Invalid API key format'}, 
                status=400
            )
        
        # Check if key exists in database
        api_key = uuid.UUID(os.getenv("API_KEY"))
        if api_key_uuid != api_key:
            return JsonResponse(
                {'error': 'Invalid API key'}, 
                status=403
            )
            
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def has_perms(employee_id: int, perms_list: list) -> bool:
    try:
        employee = Employee.objects.prefetch_related('job_roles__permissions').get(id=employee_id)
    except Employee.DoesNotExist:
        return False

    # Gather all permissions attached to the employee's job roles
    assigned_perms = set(
        perm.name for role in employee.job_roles.all() for perm in role.permissions.all()
    )

    for perm_name in perms_list:
        if perm_name not in assigned_perms:
            return False

    return True


def token_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        auth_token = request.headers.get("Authorization")
        if not auth_token:
            return JsonResponse({"error": "Authorization token missing"}, status=401)

        try:
            # Validate if it's a proper UUID first
            uuid_token = uuid.UUID(auth_token)
            request.user = Employee.objects.get(authToken=uuid_token)
        except (ValueError, Employee.DoesNotExist):
            return JsonResponse({"error": "Invalid or expired token"}, status=403)

        return view_func(request, *args, **kwargs)

    return wrapped

def user_token_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        auth_token = request.headers.get("Authorization")
        if not auth_token:
            return JsonResponse({"error": "Authorization token missing"}, status=401)

        try:
            # Validate if it's a proper UUID first
            uuid_token = uuid.UUID(auth_token)
            request.user = Student.objects.get(authToken=uuid_token)
        except (ValueError, Student.DoesNotExist):
            return JsonResponse({"error": "Invalid or expired token"}, status=403)

        return view_func(request, *args, **kwargs)

    return wrapped

# GDRIVE INTEGRATION FOR STRORING IMAGES AND FILES
#website/utils.py
import io
import uuid
from django.conf import settings
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

DEFAULT_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_drive_service():
    """
    Build a google drive service using client_id/secret and refresh_token from env.
    This uses an in-memory Credentials object and refreshes automatically when needed.
    """
    creds = Credentials(
        token=None,
        refresh_token=getattr(settings, "GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=getattr(settings, "GOOGLE_CLIENT_ID"),
        client_secret=getattr(settings, "GOOGLE_CLIENT_SECRET"),
        scopes=getattr(settings, "GOOGLE_SCOPES", DEFAULT_SCOPES),
    )

    if not creds.valid or creds.expired:
        creds.refresh(Request())

    return build("drive", "v3", credentials=creds)


PUBLIC_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
def upload_file_to_drive_public(file_obj, ext=None):
    """
    Upload file to Google Drive (public access).
    Supports: jpg, jpeg, png, webp
    """
    service = get_drive_service()
    generated_uuid = str(uuid.uuid4())

    if not ext:
        ext = file_obj.name.split(".")[-1].lower()

    if ext not in PUBLIC_ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {ext}")

    filename = f"{generated_uuid}.{ext}"

    metadata = {
        "name": filename,
        "parents": [getattr(settings, "GOOGLE_DRIVE_FOLDER_ID_PUBLIC")],
    }

    file_bytes = io.BytesIO(file_obj.read())

    try:
        media = MediaIoBaseUpload(file_bytes, mimetype=f"image/{ext}", resumable=False)
        uploaded = service.files().create(
            body=metadata, media_body=media, fields="id"
        ).execute()

        # Make it public
        service.permissions().create(
            fileId=uploaded["id"],
            body={"role": "reader", "type": "anyone"},
        ).execute()

        return uploaded["id"], generated_uuid

    finally:
        file_bytes.close()


PRIVATE_ALLOWED_EXTENSIONS = {"jpg", "jpeg", "webp", "pdf"}

def upload_file_to_drive_private(file_obj, ext=None):
    """
    Upload file to Google Drive (private access).
    Supported extensions: jpg, jpeg, webp, pdf
    """
    service = get_drive_service()
    generated_uuid = str(uuid.uuid4())

    if not ext:
        ext = file_obj.name.split(".")[-1].lower()

    if ext not in PRIVATE_ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {ext}")

    filename = f"{generated_uuid}.{ext}"

    metadata = {
        "name": filename,
        "parents": [getattr(settings, "GOOGLE_DRIVE_FOLDER_ID_PRIVATE")],
    }

    file_bytes = io.BytesIO(file_obj.read())

    try:
        # Set MIME type
        if ext == "pdf":
            mimetype = "application/pdf"
        else:
            mimetype = f"image/{ext}"

        media = MediaIoBaseUpload(file_bytes, mimetype=mimetype, resumable=False)
        uploaded = service.files().create(
            body=metadata, media_body=media, fields="id"
        ).execute()

        # File remains private by default
        return uploaded["id"], generated_uuid

    finally:
        file_bytes.close()