import json
import os

from course.models import *
from django.db import DatabaseError, connection, transaction
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from google import genai

from website.utils import api_key_required, has_perms, token_required

from .models import *


@require_http_methods(["GET"])
@token_required
def get_all_students(request):
    employee = request.user  # comes from @token_required

    # Permission check
    if not has_perms(employee.id, ["student_logs_view"]):
        return JsonResponse(
            {
                "status": "error",
                "message": "You do not have permission to perform this task",
            },
            status=403,
        )

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT s.id, s.full_name, b.name AS bucket_name
            FROM student_student AS s
            LEFT JOIN student_bucket AS b ON s.category_id = b.id;
        """
        )
        rows = cursor.fetchall()

    # Convert rows -> list of dicts
    students = [{"id": row[0], "full_name": row[1], "bucket": row[2]} for row in rows]

    return JsonResponse(students, safe=False, status=200)


@csrf_exempt
@token_required
def get_student_details_with_student_id(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body)
        student_id = body.get("student_id")

        if not student_id:
            return JsonResponse({"error": "Student ID not provided"}, status=400)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT get_student_full_details_by_id(%s);", [int(student_id)]
            )
            row = cursor.fetchone()

        if not row or not row[0]:
            return JsonResponse({"error": "No student details found"}, status=404)

        student_data = json.loads(row[0])
        return JsonResponse(student_data, safe=False)

    except Exception as e:
        return JsonResponse(
            {"error": "An error occured, please try again later"}, status=500
        )


@token_required
def get_student_logs(request, student_id):
    employee = request.user  # comes from @token_required

    # Permission check
    if not has_perms(employee.id, ["student_logs_view"]):
        return JsonResponse(
            {
                "status": "error",
                "message": "You do not have permission to perform this task",
            },
            status=403,
        )

    """
    Fetch all logs (id, logs, added_on, student_id) from logs table.
    """
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT logs, added_on FROM student_logs WHERE student_id = %s;",
            [student_id],
        )
        rows = cursor.fetchall()

    logs = [
        {
            "log": row[0],
            "added_on": row[1].strftime("%Y-%m-%d %H:%M") if row[1] else None,
        }
        for row in rows
    ]

    return JsonResponse(logs, safe=False, status=200)


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def stream_gemini_response(prompt):
    """
    Stream Gemini response using the API key from .env.
    """
    if not GEMINI_API_KEY:
        return JsonResponse({"error": "GEMINI_API_KEY is not set"}, status=500)

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        stream = client.models.generate_content_stream(
            model="gemini-2.5-flash", contents=[prompt]
        )

        def event_stream():
            for chunk in stream:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text

        return StreamingHttpResponse(event_stream(), content_type="text/plain")

    except Exception as e:
        return JsonResponse({"error": "An error occured, try again later"}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@token_required
def summarize_student_interest(request):
    """
    Fetch student data from Postgres, send to Gemini for summarization,
    and return a streaming response.
    """
    employee = request.user

    # Permission check
    if not has_perms(employee.id, ["student_logs_view"]):
        return JsonResponse(
            {
                "status": "error",
                "message": "You do not have permission to perform this task",
            },
            status=403,
        )

    try:
        if request.method != "POST":
            return JsonResponse(
                {"status": "error", "message": "POST method required"}, status=405
            )

        # Read student_id from POST JSON body
        try:
            body = json.loads(request.body.decode("utf-8"))
            student_id = body.get("student_id")
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON body"}, status=400
            )

        if not student_id:
            return JsonResponse(
                {"status": "error", "message": "student_id is required"}, status=400
            )

        student_id = int(student_id)

        # --- Fetch student data from Postgres ---
        with connection.cursor() as cursor:
            cursor.execute("SELECT get_student_details_summary(%s);", [student_id])
            row = cursor.fetchone()

        if not row or not row[0]:
            return JsonResponse(
                {"status": "error", "message": "Student not found"}, status=404
            )

        student_data = json.loads(row[0]) if isinstance(row[0], str) else row[0]

        # --- Prepare prompt for Gemini ---
        prompt = f"""
            Also tell me how much profile is completed on teh scale of 1 to 100 by seeing all the data and missing fields.

            Analyze this student profile and give me a clear, easy-to-read summary with:

            Conversion Chance: High / Medium / Low → explain briefly why.

            Universities & Courses: List shortlisted universities + courses (with country, degree type, field).

            Country & Degree Preferences: Where and what degree they mainly want to study.

            Education: Degree, field, grades/CGPA, and any test scores (IELTS/TOEFL, etc.).

            Work Experience: Roles, companies, duration, key highlights.

            Personal Info: Nationality + current residence.

            Keep it structured but simple — something a counselor can quickly scan and understand.    
            Student data (JSON): {json.dumps(student_data)}
        """

        return stream_gemini_response(prompt)

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": "An error occured"}, status=500
        )


@require_http_methods(["GET"])
@csrf_exempt
@token_required
def bucket_list(request):
    employee = request.user

    # Permission check
    if not has_perms(employee.id, ["manage_buckets"]):
        return JsonResponse(
            {
                "status": "error",
                "message": "You do not have permission to perform this task",
            },
            status=403,
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name FROM student_bucket ORDER BY id;")
            rows = cursor.fetchall()

            if not rows:
                return JsonResponse({"error": "No buckets found"}, status=404)

            buckets = [{"id": row[0], "name": row[1]} for row in rows]

        return JsonResponse(buckets, safe=False, status=200)

    except Exception as e:
        # return JsonResponse({"error": f"Unexpected error {str(e)}"}, status=500)
        return JsonResponse({"error": f"Unexpected error"}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@token_required
def set_student_bucket(request):
    employee = request.user

    # Permission check
    if not has_perms(employee.id, ["manage_buckets"]):
        return JsonResponse(
            {
                "status": "error",
                "message": "You do not have permission to perform this task",
            },
            status=403,
        )

    try:
        payload = json.loads(request.body)
        student_id = payload.get("student_id")
        bucket_id = payload.get("bucket_id")

        if not student_id or not bucket_id:
            return JsonResponse(
                {"status": "error", "error": "student_id and bucket_id are required"},
                status=400,
            )

        # Call the Postgres function using cursor
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM set_student_bucket(%s, %s);", [student_id, bucket_id]
            )
            row = cursor.fetchone()

        if not row:
            return JsonResponse(
                {"status": "error", "error": "No response from database"}, status=500
            )

        result_student_id, result_bucket_id, error_message = row

        if error_message:
            return JsonResponse({"status": "error", "error": error_message}, status=400)

        return JsonResponse(
            {
                "status": "success",
                "message": "Student bucket updated successfully",
                "student_id": result_student_id,
                "bucket_id": result_bucket_id,
            },
            status=200,
        )

    except Exception as e:
        # return JsonResponse({"status": "error", "error": f"Unexpected error: {str(e)}"}, status=500)
        return JsonResponse(
            {"status": "error", "error": f"Unexpected error"}, status=500
        )


@csrf_exempt
@require_http_methods(["GET"])
@token_required
def get_assigned_students(request):
    try:
        employee_id = request.user.id
        if not employee_id:
            return JsonResponse(
                {"status": False, "error": "employee_id required"}, status=400
            )

        with connection.cursor() as cursor:
            cursor.execute("SELECT get_assigned_students(%s);", [employee_id])
            result = cursor.fetchone()[0]

        return JsonResponse({"status": True, "data": result if result else []})

    except Exception as e:
        return JsonResponse({"status": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@token_required
def total_student_applications(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
        student_id = body.get("student_id")
        employee_id = request.user.id

        if not isinstance(student_id, int):
            return JsonResponse(
                {"status": False, "error": "Invalid or missing student_id"}, status=400
            )

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1
                FROM student_assignedcounsellor
                WHERE student_id = %s AND employee_id = %s
                LIMIT 1;
                """,
                [student_id, employee_id],
            )
            if cursor.fetchone() is None:
                return JsonResponse(
                    {"status": False, "error": "You are not assigned to this student"},
                    status=403,
                )

        with connection.cursor() as cursor:
            cursor.execute("SELECT get_student_applications(%s);", [student_id])
            applications = cursor.fetchone()[0]

        return JsonResponse({"status": True, "applications": applications or []})

    except json.JSONDecodeError:
        return JsonResponse({"status": False, "error": "Invalid JSON body"}, status=400)

    except Exception as e:
        return JsonResponse({"status": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@token_required
def ask_for_documents(request):
    try:
        data = json.loads(request.body.decode())
        application_number = data.get("application_number")
        documents = data.get("documents")
        employee_id = request.user.id

        if not application_number:
            return JsonResponse(
                {"status": False, "error": "application_number is required"}, status=400
            )

        if not documents or not isinstance(documents, list):
            return JsonResponse(
                {"status": False, "error": "documents must be a list"}, status=400
            )

        # Get application + student
        try:
            application = AppliedUniversity.objects.select_related("student").get(
                application_number=application_number
            )
        except AppliedUniversity.DoesNotExist:
            return JsonResponse(
                {"status": False, "error": "Invalid application_number"}, status=404
            )

        student_id = application.student.id

        # Verify counsellor assigned
        assigned = AssignedCounsellor.objects.filter(
            student_id=student_id, employee_id=employee_id
        ).exists()

        if not assigned:
            return JsonResponse(
                {"status": False, "error": "You are not assigned to this student"},
                status=403,
            )

        created_or_assigned = []

        for doc in documents:
            doc_type_id = doc.get("document_type_id")
            name = doc.get("name")
            doc_type = doc.get("doc_type")
            sub_type = doc.get("sub_type")
            instructions = doc.get("instructions")

            # Case 1: Existing DocumentType
            if doc_type_id:
                try:
                    document_type = DocumentType.objects.get(id=doc_type_id)
                except DocumentType.DoesNotExist:
                    return JsonResponse(
                        {
                            "status": False,
                            "error": f"document_type_id {doc_type_id} not found",
                        },
                        status=404,
                    )

            # Case 2: Create new DocumentType
            else:
                if not name or not doc_type:
                    return JsonResponse(
                        {
                            "status": False,
                            "error": "For new document types, 'name' and 'doc_type' are required",
                        },
                        status=400,
                    )

                document_type, created = DocumentType.objects.get_or_create(
                    name=name,
                    defaults={
                        "doc_type": doc_type,
                        "sub_type": sub_type,
                        "is_default": False,
                    },
                )

                if not created:
                    # If name already exists but doc_type mismatches → reject
                    if document_type.doc_type != doc_type:
                        return JsonResponse(
                            {
                                "status": False,
                                "error": f"Document name '{name}' already exists with another type",
                            },
                            status=400,
                        )

            # Now assign requirement to student
            req, created_req = StudentDocumentRequirement.objects.get_or_create(
                student_id=student_id,
                document_type=document_type,
                requested_for_university=application,
                defaults={"requested_by_id": employee_id, "instructions": instructions},
            )

            if not created_req:
                req.instructions = instructions
                req.requested_by_id = employee_id
                req.save()

            created_or_assigned.append(
                {
                    "document_type_id": document_type.id,
                    "document_name": document_type.name,
                    "requirement_id": req.id,
                }
            )

        return JsonResponse(
            {
                "status": True,
                "message": "Documents processed successfully",
                "data": created_or_assigned,
            }
        )

    except Exception as e:
        return JsonResponse({"status": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@token_required
def get_student_application_details(request):
    try:
        data = json.loads(request.body.decode())
        application_number = data.get("application_number")

        if not application_number:
            return JsonResponse(
                {"status": False, "error": "application_number is required"}, status=400
            )

        employee_id = request.user.id

        # get student id from application_number
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT student_id 
                FROM student_applieduniversity 
                WHERE application_number = %s
            """,
                [application_number],
            )
            row = cursor.fetchone()

        if not row:
            return JsonResponse(
                {"status": False, "error": "Invalid application number"}, status=400
            )

        student_id = row[0]

        # Check counsellor assignment
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 
                FROM student_assignedcounsellor
                WHERE student_id = %s AND employee_id = %s
                LIMIT 1
            """,
                [student_id, employee_id],
            )
            assigned = cursor.fetchone()

        if not assigned:
            return JsonResponse(
                {"status": False, "error": "You are not assigned to this student"},
                status=403,
            )

        # CALL THE FUNCTION
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT get_student_application_details(%s);", [application_number]
            )
            result = cursor.fetchone()[0]

        return JsonResponse({"status": True, "data": result})

    except Exception as e:
        return JsonResponse({"status": False, "error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
@token_required
def update_document_status(request):
    try:
        data = json.loads(request.body.decode())

        student_id = data.get("student_id")
        doc_id = data.get("required_document_id")
        new_status = data.get("counsellor_status")
        new_comments = data.get("counsellor_comments")

        if not student_id:
            return JsonResponse(
                {"status": False, "error": "student_id is required"}, status=400
            )

        if not doc_id:
            return JsonResponse(
                {"status": False, "error": "required_document_id is required"},
                status=400,
            )

        if not new_status and not new_comments:
            return JsonResponse(
                {
                    "status": False,
                    "error": "At least one of counsellor_status or counsellor_comments is required",
                },
                status=400,
            )

        employee_id = request.user.id

        # Check if counsellor is assigned to this student
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 1 
                FROM student_assignedcounsellor
                WHERE student_id = %s AND employee_id = %s
                LIMIT 1;
            """,
                [student_id, employee_id],
            )
            allowed = cursor.fetchone()

        if not allowed:
            return JsonResponse(
                {"status": False, "error": "You are not assigned to this student"},
                status=403,
            )

        # Ensure the document requirement belongs to the student
        try:
            requirement = StudentDocumentRequirement.objects.get(
                id=doc_id, student_id=student_id
            )
        except StudentDocumentRequirement.DoesNotExist:
            return JsonResponse(
                {
                    "status": False,
                    "error": "Document requirement does not belong to the student",
                },
                status=404,
            )

        # Fetch or create the actual document record
        document, _created = Document.objects.get_or_create(
            required_document=requirement
        )

        # Apply updates
        if new_status:
            document.counsellor_status = new_status

        if new_comments:
            document.counsellor_comments = new_comments

        document.save()

        return JsonResponse(
            {"status": True, "message": "Document updated successfully"}
        )

    except Exception as e:
        return JsonResponse({"status": False, "error": str(e)}, status=500)


@require_http_methods(["GET"])
@token_required
def get_available_documents_list(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, name, doc_type, sub_type 
                FROM student_documenttype
            """
            )
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description]

        data = [dict(zip(columns, row)) for row in rows]

        return JsonResponse(
            {"status": "success", "count": len(data), "data": data}, status=200
        )

    except DatabaseError as e:
        return JsonResponse(
            {
                "status": "error",
                "message": "Something went wrong while fetching the documents.",
            },
            status=500,
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": "Something went wrong"}, status=500
        )

