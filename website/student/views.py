import json
import os
import random
import re
import secrets
import string
import threading
from uuid import uuid4

import requests
from course.models import *
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import DatabaseError, connection, transaction
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from google import genai

from website.utils import (
    api_key_required,
    has_perms,
    token_required,
    upload_file_to_drive_private,
    user_token_required,
)

from .models import *
from .models import Document, StudentLogs
from .utils import create_student_log, stream_private_drive_file
from website.utils import upload_profile_picture, delete_from_google_drive
from .models import StudentProfilePicture
from django.http import HttpResponse
from .utils import stream_google_drive_image

WHATSAPP_TOKEN = settings.WHATSAPP_TOKEN
WHATSAPP_PHONE_NUMBER_ID = settings.WHATSAPP_PHONE_NUMBER_ID

import logging

logger = logging.getLogger(__name__)


def send_whatsapp_otp(phone_number: str, otp: int):
    url = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": "91" + phone_number,
        "type": "template",
        "template": {
            "name": "auth",
            "language": {"code": "en"},
            "components": [
                {"type": "body", "parameters": [{"type": "text", "text": str(otp)}]},
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [{"type": "text", "text": str(otp)}],
                },
            ],
        },
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()
    except Exception as e:
        logger.error(f"Network error sending WhatsApp OTP: {e}")
        return {"status": "error", "reason": "network", "code": 502}

    if "error" in data or response.status_code != 200:
        logger.error(f"WhatsApp API error: {response.status_code} {data}")
        return {"status": "error", "reason": "provider_error", "code": 502}

    messages = data.get("messages")
    if (
        messages
        and isinstance(messages, list)
        and messages[0].get("message_status") == "accepted"
    ):
        return {"status": "success", "code": 200}

    logger.warning(f"Unexpected WhatsApp API response: {data}")
    return {"status": "error", "reason": "unexpected_response", "code": 502}


@csrf_exempt
@require_http_methods(["POST"])
def register_and_send_otp(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    full_name = str(data.get("full_name", "")).strip()
    phone_number = str(data.get("phone_number", "")).strip()
    email = str(data.get("email", "")).strip()

    if (
        not full_name
        or not phone_number
        or not email
        or not phone_number.isdigit()
        or len(phone_number) != 10
        or not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)
    ):
        return JsonResponse(
            {
                "status": "error",
                "message": "Invalid input. All fields are required and must be valid.",
            },
            status=400,
        )

    otp = str(secrets.randbelow(900000) + 100000)
    auth_token = str(uuid4())

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Check if phone number already exists
                cursor.execute(
                    "SELECT id FROM student_student WHERE phone_number = %s;",
                    [phone_number],
                )
                if cursor.fetchone():
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "This number is already registered with an account. Kindly login using this number",
                        },
                        status=400,
                    )

                # Check if email already exists
                cursor.execute(
                    "SELECT student_id FROM student_email WHERE email = %s;", [email]
                )
                if cursor.fetchone():
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "This email is already in use with another account.",
                        },
                        status=400,
                    )

                # Insert new student
                cursor.execute(
                    """
                    INSERT INTO student_student (phone_number, is_otp_verified, full_name, "authToken")
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                    """,
                    [phone_number, False, full_name, auth_token],
                )
                student_id_row = cursor.fetchone()
                if not student_id_row:
                    raise Exception("Failed to insert student")
                student_id = student_id_row[0]

                # Insert email into student_email table
                cursor.execute(
                    "INSERT INTO student_email (student_id, email) VALUES (%s, %s);",
                    [student_id, email],
                )

                # Request OTP
                cursor.execute("SELECT request_otp(%s, %s);", [phone_number, otp])
                result_status = cursor.fetchone()[0]

        if result_status == "success":
            send_result = send_whatsapp_otp(phone_number, otp)
            if send_result.get("status") != "success":
                logger.error(f"Failed to send OTP to {phone_number}: {send_result}")
                return JsonResponse(
                    {"status": "error", "message": "Could not send OTP"}, status=502
                )

            return JsonResponse(
                {"status": "success", "message": f"OTP sent to {phone_number}"},
                status=200,
            )

        elif result_status == "wait":
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Please wait before requesting OTP again",
                },
                status=429,
            )

        else:
            return JsonResponse(
                {"status": "error", "message": "Internal server error"}, status=500
            )

    except Exception as e:
        logger.exception(f"Error in register_and_send_otp: {e}")
        return JsonResponse(
            {"status": "error", "message": "An error occurred, try again later"},
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
def send_otp(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    phone_number = str(data.get("phone_number", "")).strip()
    if not phone_number.isdigit() or len(phone_number) != 10:
        return JsonResponse(
            {"status": "error", "message": "Invalid phone number"}, status=400
        )

    try:
        with connection.cursor() as cursor:
            # Check if student exists
            cursor.execute(
                "SELECT id FROM student_student WHERE phone_number = %s;",
                [phone_number],
            )
            student = cursor.fetchone()
            if not student:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Phone number not registered. Please register first.",
                    },
                    status=400,
                )

            # Generate OTP
            otp = str(secrets.randbelow(900000) + 100000)  # 6-digit OTP

            # Request OTP from Postgres function
            cursor.execute("SELECT request_otp(%s, %s);", [phone_number, otp])
            result_status = cursor.fetchone()[0]  # 'success', 'wait', or 'error'

        if result_status == "success":
            # Send OTP
            send_result = send_whatsapp_otp(phone_number, otp)
            if send_result.get("status") != "success":
                logger.error(f"Failed to send OTP to {phone_number}: {send_result}")
                return JsonResponse(
                    {"status": "error", "message": "Could not send OTP"}, status=502
                )

            return JsonResponse(
                {"status": "success", "message": f"OTP sent to {phone_number}"},
                status=200,
            )

        elif result_status == "wait":
            return JsonResponse(
                {
                    "status": "error",
                    "message": "Please wait before requesting OTP again",
                },
                status=429,
            )

        else:  # 'error'
            return JsonResponse(
                {"status": "error", "message": "Internal server error"}, status=500
            )

    except Exception as e:
        logger.exception(f"Error in send_otp: {e}")
        return JsonResponse(
            {"status": "error", "message": "An error occurred, try again later"},
            status=500,
        )


@csrf_exempt
@require_http_methods(["POST"])
def verify_otp_view(request):
    try:
        # Parse JSON body
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON body"}, status=400
            )

        phone_number = data.get("phone_number")
        otp = data.get("otp")

        if not phone_number or not otp:
            return JsonResponse(
                {"status": "error", "message": "Phone number and OTP are required"},
                status=400,
            )

        # Call Postgres function
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM verify_otp(%s, %s)", [phone_number, otp])
            result = cursor.fetchone()

        if not result:
            return JsonResponse(
                {"status": "error", "message": "Unexpected error"}, status=500
            )

        status, token, is_existing, full_name, email = result

        # Handle database response
        if status == "expired":
            return JsonResponse(
                {"status": "error", "message": "OTP expired"}, status=410
            )

        elif status == "invalid":
            return JsonResponse(
                {"status": "error", "message": "Invalid or expired OTP"}, status=401
            )

        elif status == "success":
            return JsonResponse(
                {
                    "status": "success",
                    "message": "OTP verified",
                    "phone_number": phone_number,
                    "name": full_name,
                    "email": email,
                    "type": "login" if is_existing else "register",
                    "auth_token": str(token),
                },
                status=200,
            )

        return JsonResponse(
            {"status": "error", "message": f"Unknown status: {status}"}, status=500
        )

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Server error: {str(e)}"}, status=500
        )



@csrf_exempt
@api_key_required
@user_token_required
@require_http_methods(["POST"])
def add_to_shortlist_university(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        university_name = data.get("university_name")

        if not university_name:
            return JsonResponse({"error": "University name is required."}, status=400)

        student_id = request.user.id  # logged in student

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM add_shortlist_university(%s::BIGINT, %s::TEXT)",
                    [student_id, university_name.strip()],
                )
                result = cursor.fetchone()

        status, shortlist_id, student_name, uni_name, added_on = result

        if status == "not_found":
            return JsonResponse({"error": "University not found."}, status=404)
        elif status == "duplicate":
            return JsonResponse(
                {"message": "University is already shortlisted."}, status=400
            )
        elif status == "success":
            return JsonResponse(
                {
                    "status": "success",
                    "shortlist": {
                        "id": shortlist_id,
                        "student": student_name,
                        "university": uni_name,
                        "added_on": added_on.strftime("%Y-%m-%d %H:%M:%S"),
                    },
                },
                status=201,
            )
        else:
            return JsonResponse({"error": "Internal server error."}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)
    except Exception as e:
        # return JsonResponse({"error": str(e)}, status=500)
        return JsonResponse({"error": "An error occured"}, status=500)


@csrf_exempt
@api_key_required
@user_token_required
@require_http_methods(["POST"])
def add_to_shortlist_course(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        university_name = data.get("university_name")
        course_name = data.get("course_name")

        if not university_name or not course_name:
            return JsonResponse(
                {"error": "Both university_name and course_name are required."},
                status=400,
            )

        student_id = request.user.id  # logged-in student

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM add_shortlist_course(%s::BIGINT, %s::TEXT, %s::TEXT)",
                    [student_id, university_name.strip(), course_name.strip()],
                )
                result = cursor.fetchone()

        if not result:
            return JsonResponse({"error": "Function returned no data."}, status=500)

        status, shortlist_id, student_name, uni_name, program_name, added_on = result
        added_on_str = added_on.strftime("%Y-%m-%d %H:%M:%S") if added_on else None

        if status == "university_not_found":
            return JsonResponse({"error": "University not found."}, status=404)
        elif status == "course_not_found":
            return JsonResponse({"error": "Course not found."}, status=404)
        elif status == "duplicate":
            return JsonResponse(
                {"message": "Course is already shortlisted."}, status=400
            )
        elif status == "success":
            return JsonResponse(
                {
                    "status": "success",
                    "shortlist": {
                        "id": shortlist_id,
                        "student": student_name,
                        "university": uni_name,
                        "course": program_name,
                        "added_on": added_on_str,
                    },
                },
                status=201,
            )
        else:
            return JsonResponse({"error": "Internal server error."}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)
    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse({"error": "Internal server error."}, status=500)


@csrf_exempt
@api_key_required
@user_token_required
@require_http_methods(["GET"])
def get_shortlisted_items(request):
    student_id = request.user.id

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # Call the Postgres function using student_id
                cursor.execute("SELECT get_shortlisted_items(%s::BIGINT)", [student_id])
                result = cursor.fetchone()
                if not result:
                    return JsonResponse({"error": "No data returned."}, status=500)

                result_json = result[0]
                # Ensure it's a dict
                if isinstance(result_json, str):
                    import json

                    result_json = json.loads(result_json)

        # Log action in Django for flexibility
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO student_logs (student_id, logs, added_on)
                VALUES (%s, %s, NOW())
                """,
                [student_id, "Opened Shortlisted Page"],
            )

        return JsonResponse(result_json, status=200)

    except Exception as e:
        import traceback

        traceback.print_exc()
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)


@csrf_exempt
@api_key_required
@user_token_required
@require_http_methods(["GET"])
def get_student_details(request):
    try:
        student = request.user
        student_id = student.id

    except Exception as e:
        return JsonResponse(
            {"error": "Error, kindly enter correct student id or try again"}
        )

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT get_student_full_details(%s);", [student_id])
            row = cursor.fetchone()
            result_json = row[0] if row else {}

        return JsonResponse(result_json)

    except Exception as e:
        return JsonResponse({"error": "An error occured, try again later"}, status=500)


def validate_required_fields(data, required_fields):
    missing_fields = [field for field in required_fields if not data.get(field)]
    return missing_fields


@csrf_exempt
@api_key_required
@user_token_required
@require_http_methods(["POST"])
def update_student_profile(request):
    student_id = request.user.id

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON body"}, status=400
        )

    if not data:
        return JsonResponse(
            {"status": "error", "message": "Empty JSON body"}, status=400
        )

    results = {}
    allowed_sections = {
        "student",
        "student_details",
        "education_details",
        "test_scores",
        "preference",
        "experience_details",
    }

    unknown_keys = set(data.keys()) - allowed_sections
    if unknown_keys:
        return JsonResponse(
            {
                "status": "error",
                "message": f"Unknown sections provided: {', '.join(unknown_keys)}. Only these are allowed: {', '.join(allowed_sections)}",
            },
            status=400,
        )

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                # 1️⃣ Student (update full_name)
                if "student" in data:
                    section = "student"
                    full_name = data[section].get("full_name", "").strip()
                    if not (1 <= len(full_name) <= 200):
                        return JsonResponse(
                            {
                                "status": "error",
                                "message": "Full name must be between 1 and 200 characters.",
                            },
                            status=400,
                        )

                    cursor.execute(
                        "UPDATE student_student SET full_name = %s WHERE id = %s",
                        [full_name, student_id],
                    )
                    results[section] = "updated"

                # 2️⃣ StudentDetails
                if "student_details" in data:
                    section = "student_details"
                    sd = data[section]
                    cursor.execute(
                        """
                        INSERT INTO student_studentdetails(student_id, first_name, last_name, gender, dob, nationality, address, state, city, zip_code, country)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_id) 
                        DO UPDATE SET first_name=EXCLUDED.first_name, last_name=EXCLUDED.last_name,
                                      gender=EXCLUDED.gender, dob=EXCLUDED.dob, nationality=EXCLUDED.nationality,
                                      address=EXCLUDED.address, state=EXCLUDED.state, city=EXCLUDED.city,
                                      zip_code=EXCLUDED.zip_code, country=EXCLUDED.country
                    """,
                        [
                            student_id,
                            sd.get("first_name"),
                            sd.get("last_name"),
                            sd.get("gender"),
                            sd.get("dob"),
                            sd.get("nationality"),
                            sd.get("address"),
                            sd.get("state"),
                            sd.get("city"),
                            sd.get("zip_code"),
                            sd.get("country"),
                        ],
                    )
                    results[section] = "updated"

                email_value = sd.get("email")
                if email_value:
                    cursor.execute(
                        """
                        INSERT INTO student_email (student_id, email)
                        VALUES (%s, %s)
                        ON CONFLICT (student_id)
                        DO UPDATE SET email = EXCLUDED.email
                        """,
                        [student_id, email_value],
                    )

                results[section] = "updated"

                # 3️⃣ EducationDetails
                if "education_details" in data:
                    section = "education_details"
                    ed = data[section]
                    cursor.execute(
                        """
                        INSERT INTO student_educationdetails(student_id, institution_name, degree, study_field, cgpa, start_date, end_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_id)
                        DO UPDATE SET institution_name=EXCLUDED.institution_name, degree=EXCLUDED.degree,
                                      study_field=EXCLUDED.study_field, cgpa=EXCLUDED.cgpa,
                                      start_date=EXCLUDED.start_date, end_date=EXCLUDED.end_date
                    """,
                        [
                            student_id,
                            ed.get("institution_name"),
                            ed.get("degree"),
                            ed.get("study_field"),
                            ed.get("cgpa"),
                            ed.get("start_date"),
                            ed.get("end_date"),
                        ],
                    )
                    results[section] = "updated"

                # 4️⃣ TestScores
                if "test_scores" in data:
                    section = "test_scores"
                    ts = data[section]
                    cursor.execute(
                        """
                        INSERT INTO student_testscores(student_id, exam_type, english_exam_type, date, listening_score, reading_score, writing_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_id)
                        DO UPDATE SET exam_type=EXCLUDED.exam_type, english_exam_type=EXCLUDED.english_exam_type,
                                      date=EXCLUDED.date, listening_score=EXCLUDED.listening_score,
                                      reading_score=EXCLUDED.reading_score, writing_score=EXCLUDED.writing_score
                    """,
                        [
                            student_id,
                            ts.get("exam_type"),
                            ts.get("english_exam_type"),
                            ts.get("date"),
                            ts.get("listening_score"),
                            ts.get("reading_score"),
                            ts.get("writing_score"),
                        ],
                    )
                    results[section] = "updated"

                # 5️⃣ Preference
                if "preference" in data:
                    section = "preference"
                    pref = data[section]
                    cursor.execute(
                        """
                        INSERT INTO student_preference(student_id, country, degree, discipline, sub_discipline, date, budget)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_id)
                        DO UPDATE SET country=EXCLUDED.country, degree=EXCLUDED.degree,
                                      discipline=EXCLUDED.discipline, sub_discipline=EXCLUDED.sub_discipline,
                                      date=EXCLUDED.date, budget=EXCLUDED.budget
                    """,
                        [
                            student_id,
                            pref.get("country"),
                            pref.get("degree"),
                            pref.get("discipline"),
                            pref.get("sub_discipline"),
                            pref.get("date"),
                            pref.get("budget"),
                        ],
                    )
                    results[section] = "updated"

                # 6️⃣ ExperienceDetails (list)
                if "experience_details" in data:
                    section = "experience_details"
                    exp_list = data[section]
                    if not isinstance(exp_list, list):
                        return JsonResponse(
                            {
                                "status": "error",
                                "message": f"{section} should be a list",
                            },
                            status=400,
                        )

                    cursor.execute(
                        "DELETE FROM student_experiencedetails WHERE student_id = %s",
                        [student_id],
                    )
                    for exp in exp_list:
                        cursor.execute(
                            """
                            INSERT INTO student_experiencedetails(student_id, company_name, title, city, country, employment_type, industry_type, start_date, end_date, currently_working)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                            [
                                student_id,
                                exp.get("company_name"),
                                exp.get("title"),
                                exp.get("city"),
                                exp.get("country"),
                                exp.get("employment_type"),
                                exp.get("industry_type"),
                                exp.get("start_date"),
                                exp.get("end_date"),
                                exp.get("currently_working", False),
                            ],
                        )
                    results[section] = "updated"

        # Log action (keep your existing function)
        create_student_log(request, f"Updated Profile")
        return JsonResponse({"status": "success", "results": results}, status=200)

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "message": "Oh! Uh! Some error happended, try again later",
            },
            status=500,
        )


@require_http_methods(["GET"])
def get_all_choices(request):
    choices = {
        "countries": [country for country, _ in COUNTRY_CHOICES],
        "genders": [
            gender
            for gender, _ in [
                ("Male", "Male"),
                ("Female", "Female"),
                ("Other", "Other"),
            ]
        ],
        "degree_choices": [deg for deg, _ in EducationDetails.DEGREE_CHOICES],
        "study_fields": [field for field, _ in EducationDetails.FIELD_CHOICES],
        "employment_types": [
            emp for emp, _ in ExperienceDetails.EMPLOYMENT_TYPE_CHOICES
        ],
        "industry_types": [ind for ind, _ in ExperienceDetails.INDUSTRY_TYPE_CHOICES],
        "exam_types": [exam for exam, _ in TestScores.EXAM_TYPE_CHOICES],
        "english_exam_types": [exam for exam, _ in TestScores.ENGLISH_EXAM_CHOICES],
        "preference_degrees": [deg for deg, _ in Preference.DEGREE_CHOICES],
        "preference_disciplines": [disc for disc, _ in Preference.DISCIPLINE_CHOICES],
        "preference_sub_disciplines": [
            sub for sub, _ in Preference.SUB_DISCIPLINE_CHOICES
        ],
    }

    return JsonResponse(choices, status=200)


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
        cursor.execute("""
            SELECT s.id, s.full_name, b.name AS bucket_name
            FROM student_student AS s
            LEFT JOIN student_bucket AS b ON s.category_id = b.id;
        """)
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


MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB


@csrf_exempt
@require_http_methods(["POST"])
@user_token_required
def upload_document(request):
    """
    Upload a document for a student using template_document_id.
    Updates StudentDocumentRequirement automatically.
    """
    try:
        student_id = request.user.id
        student = get_object_or_404(Student, id=student_id)

        file_obj = request.FILES.get("document")
        template_document_id = request.POST.get("template_document_id")

        if not file_obj:
            return JsonResponse({"error": "No file uploaded."}, status=400)
        if file_obj.size > MAX_FILE_SIZE:
            return JsonResponse({"error": "File size exceeds 1 MB."}, status=400)
        if not template_document_id:
            return JsonResponse({"error": "template_document_id is required."}, status=400)

        # Fetch template document
        template_doc = get_object_or_404(TemplateDocument, id=template_document_id)

        # Use template's doc_type and name if not provided
        doc_type = template_doc.doc_type
        name = template_doc.name

        existing_document = Document.objects.filter(
            student=student,
            template_document=template_doc
        ).first()

        old_google_file_id = existing_document.file_id if existing_document else None

        if old_google_file_id:
            try:
                delete_from_google_drive(old_google_file_id)
            except Exception:
                pass

        # Upload to Google Drive (private)
        try:
            file_id, file_uuid = upload_file_to_drive_private(file_obj)
        except Exception as e:
            return JsonResponse({"error": f"Upload failed: {e}"}, status=500)

        # Create Document entry
        document, created = Document.objects.update_or_create(
            student=student,
            template_document=template_doc,
            defaults={
                "name": name,
                "doc_type": doc_type,
                "status": "uploaded",
                "file_id": file_id,
                "file_uuid": file_uuid,
            },
        )

        # Update or create StudentDocumentRequirement
        try:
            StudentDocumentRequirement.objects.get_or_create(
                student=student,
                template_document=template_doc
            )
        except Exception:
            # skip silently if anything goes wrong
            pass

        return JsonResponse(
            {
                "message": "Document uploaded successfully.",
                "document_id": document.id,
                "template_document_id": template_doc.id,
                # "file_uuid": str(document.file_uuid),
                # "file_id": document.file_id,
            },
            status=201,
        )

    except Exception as e:
        return JsonResponse({"error": f"Unexpected error: Error in uploading documents"}, status=500)


@require_http_methods(["GET"])
@user_token_required
def download_document(request):
    """
    Stream a private Google Drive document to the authenticated user.
    Only allows access if the document belongs to the requesting student.
    Returns JSON errors if anything goes wrong.
    """
    document_id = request.GET.get("document_id")

    if not document_id:
        return JsonResponse({"error": "document_id is required."}, status=400)

    try:
        # Verify ownership: only the student who uploaded can download
        document = get_object_or_404(Document, id=document_id, student_id=request.user.id)

        # Stream the file from Google Drive
        response = stream_private_drive_file(document.file_id, filename=document.name)

        # If streaming fails and returns JsonResponse, return it directly
        if isinstance(response, JsonResponse):
            return response

        return response

    except Document.DoesNotExist:
        return JsonResponse(
            {"error": "Document not found or access denied."}, status=404
        )

    except Exception as e:
        return JsonResponse(
            {"error": f"Unable to download document: {str(e)}"}, status=500
        )


@require_http_methods(["GET"])
@user_token_required
def get_student_documents_list(request):
    """
    Fetch all documents for the authenticated student.
    Returns JSON with document name, type, status, and download link.
    Includes documents not yet uploaded.
    """
    student_id = request.user.id

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    td.id AS template_document_id,
                    td.name AS document_name,
                    td.doc_type,
                    COALESCE(d.status, 'not_uploaded') AS status,
                    d.id AS document_id
                FROM student_templatedocument td
                LEFT JOIN student_studentdocumentrequirement sdr
                    ON sdr.template_document_id = td.id AND sdr.student_id = %s
                LEFT JOIN student_document d
                    ON d.template_document_id = td.id AND d.student_id = %s
                ORDER BY td.name
                """,
                [student_id, student_id],
            )

            rows = cursor.fetchall()

        # Build response
        documents = []
        for row in rows:
            template_doc_id, name, doc_type, status, doc_id = row
            download_link = (
                f"/user/download_document/?document_id={doc_id}"
                if doc_id is not None
                else None
            )
            documents.append(
                {
                    "template_document_id": template_doc_id,
                    "name": name,
                    "doc_type": doc_type,
                    "status": status,
                    "download_link": download_link,
                }
            )

        return JsonResponse({"documents": documents})

    except Exception as e:
        return JsonResponse(
            {"error": f"Unable to fetch documents: {str(e)}"}, status=500
        )


@csrf_exempt
@require_http_methods(["POST"])
@user_token_required
def remove_from_shortlist_view(request):
    """
    Removes a university or course from the student's shortlist.
    Example body:
    {
        "type": "university",  # or "course"
        "id": 12
    }
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        item_type = data.get("type")
        item_id = data.get("id")
        student_id = request.user.id

        if item_type not in ["university", "course"]:
            return JsonResponse(
                {"error": "Invalid type. Must be 'university' or 'course'."},
                status=400,
            )

        if not item_id:
            return JsonResponse({"error": "id is required."}, status=400)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT remove_from_shortlist(%s, %s, %s);",
                [student_id, item_id, item_type],
            )
            result = cursor.fetchone()[0]

        if not result.get("success"):
            return JsonResponse(result, status=404)

        return JsonResponse(result, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body."}, status=400)

    except Exception as e:
        # For debugging:
        # return JsonResponse({"error": str(e)}, status=500)
        # For production (user-friendly message):
        return JsonResponse(
            {"error": "Something went wrong on the server."}, status=500
        )


@csrf_exempt
@require_http_methods(["GET"])
@user_token_required
def student_dashboard_view(request):
    """
    Returns a JSON dashboard summary for the logged-in student.
    Uses PostgreSQL function get_student_dashboard(p_student_id).
    """
    try:
        student_id = request.user.id

        with connection.cursor() as cursor:
            cursor.execute("SELECT get_student_dashboard(%s);", [student_id])
            result = cursor.fetchone()[0]

        if not result:
            return JsonResponse(
                {"message": "No data found for this student."}, status=404
            )

        return JsonResponse(result, safe=False, status=200)

    except DatabaseError as db_err:
        # Debug line: Uncomment for internal debugging
        # return JsonResponse({"error": str(db_err)}, status=500)
        return JsonResponse(
            {"error": "A database error occurred. Please try again later."}, status=500
        )

    except Exception as e:
        # Debug line: Uncomment for internal debugging
        # return JsonResponse({"error": str(e)}, status=500)
        return JsonResponse(
            {"error": "Something went wrong while fetching dashboard data."}, status=500
        )


def get_application_data(course_id: int, student_id: int):
    """
    Fetches student, course, and university data for Telegram notification.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT 
                    s.id AS student_id,
                    s.full_name AS student_name,
                    s.phone_number AS student_mobile,
                    c.id AS course_id,
                    c.program_name AS course_name,
                    u.id AS university_id,
                    u.name AS university_name
                FROM student_student s
                JOIN course_course c ON c.id = %s
                JOIN university_university u ON u.id = c.university_id
                WHERE s.id = %s
                LIMIT 1;
                """,
                [course_id, student_id],
            )
            row = cursor.fetchone()
            if not row:
                return None

            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))

    except Exception as e:
        print(f"❌ Error fetching application data: {e}")
        return None


def send_applications_to_telegram(
    student_id: int,
    student_name: str,
    student_mobile: str,
    course_id: int,
    course_name: str,
    university_id: int,
    university_name: str,
):
    try:
        text = (
            "*📩 Student Application Received*\n\n"
            f"*👤 Student Details:*\n"
            f"• *ID:* `{student_id}`\n"
            f"• *Name:* {student_name}\n"
            f"• *Mobile:* `{student_mobile}`\n\n"
            f"*🎓 Course Details:*\n"
            f"• *Course ID:* `{course_id}`\n"
            f"• *Course Name:* {course_name}\n"
            f"• *University ID:* `{university_id}`\n"
            f"• *University Name:* {university_name}"
        )

        url = "https://api.telegram.org/bot8468883427:AAGvyBk9hKjY42Dw0fEZH-vNz1iQU6J-GIY/sendMessage"
        data = {"chat_id": "-1003360381829", "text": text, "parse_mode": "MarkdownV2"}
        requests.post(url, data=data, timeout=5)

    except Exception as e:
        print(f"⚠️ Failed to send Telegram message: {e}")


@csrf_exempt
@require_http_methods(["POST"])
@user_token_required
def apply_to_university_view(request):
    """
    Handles student course applications.
    Calls PostgreSQL function apply_to_university(p_student_id, p_course_id).
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
        course_id = data.get("course_id")
        student_id = request.user.id

        if not course_id:
            return JsonResponse({"error": "course_id is required."}, status=400)
        try:
            course_id = int(course_id)
        except (TypeError, ValueError):
            return JsonResponse({"error": "course_id must be an integer."}, status=400)

        if course_id <= 0:
            return JsonResponse({"error": "Invalid course_id value."}, status=400)

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT apply_to_university(%s, %s);", [student_id, course_id]
            )
            result = cursor.fetchone()[0]

        if not isinstance(result, dict):
            return JsonResponse(
                {"error": "Unexpected response from database."}, status=500
            )

        if "error" in result:
            return JsonResponse(result, status=400)

        app_data = get_application_data(course_id, student_id)

        if app_data:
            send_applications_to_telegram(
                student_id=app_data["student_id"],
                student_name=app_data["student_name"],
                student_mobile=app_data["student_mobile"],
                course_id=app_data["course_id"],
                course_name=app_data["course_name"],
                university_id=app_data["university_id"],
                university_name=app_data["university_name"],
            )
        return JsonResponse(result, safe=False, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Application could not be processed"}, status=400)

    except DatabaseError as db_err:
        # Debug line: Uncomment for internal debugging
        # return JsonResponse({"error": str(db_err)}, status=500)
        return JsonResponse(
            {"error": "An unexpected error occurred. Please try again later."},
            status=500,
        )

    except Exception as e:
        # Debug line: Uncomment for internal debugging
        # return JsonResponse({"error": str(e)}, status=500)
        return JsonResponse(
            {"error": "An unexpected error occurred. Please try again later."},
            status=500,
        )


@csrf_exempt
@require_http_methods(["GET"])
@user_token_required
def student_applied_view(request):
    """
    Returns JSON data of applied courses and universities for the logged-in student.
    Uses PostgreSQL function get_applied_items(p_student_id).
    """
    try:
        student_id = request.user.id

        with connection.cursor() as cursor:
            cursor.execute("SELECT get_applied_items(%s);", [student_id])
            result = cursor.fetchone()[0]

        if not result:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "No applied data found for this student.",
                },
                status=404,
            )

        return JsonResponse(result, safe=False, status=200)

    except DatabaseError:
        return JsonResponse(
            {
                "status": "error",
                "message": "A database error occurred. Please try again later.",
            },
            status=500,
        )

    except Exception:
        return JsonResponse(
            {
                "status": "error",
                "message": "Something went wrong while fetching applied items.",
            },
            status=500,
        )


@require_http_methods(["POST"])
@csrf_exempt
@user_token_required
def upload_image_to_drive(request):
    student = request.user
    MAX_IMAGE_SIZE_KB = 500
    upload_file = request.FILES.get("image")

    if not upload_file:
        return JsonResponse({"error": "No image provided."}, status=400)

    if upload_file.size > MAX_IMAGE_SIZE_KB * 1024:
        return JsonResponse(
            {"error": f"Image size must be under {MAX_IMAGE_SIZE_KB} KB."}, status=400
        )

    try:
        existing_pic = StudentProfilePicture.objects.filter(student=student).first()
        old_google_file_id = existing_pic.google_file_id if existing_pic else None

        drive_file_id, generated_uuid = upload_profile_picture(upload_file)
        featured_image_url = f"https://admin.gradglobe.org/profile/images?id={drive_file_id}"

        StudentProfilePicture.objects.update_or_create(
            student=student,
            defaults={
                "google_file_id": drive_file_id,
                "image_uuid": generated_uuid,
            },
        )

        if old_google_file_id:
            try:
                delete_from_google_drive(old_google_file_id)
            except Exception:
                pass

        return JsonResponse(
            {
                "success": True,
                "featured_image": featured_image_url,
            }
        )

    except Exception:
        return JsonResponse(
            {"error": "Server error while uploading the image."}, status=500
        )

@user_token_required
def get_profile_pic(request):
    student = request.user
    width = request.GET.get("w")
    height = request.GET.get("h")

    width = int(width) if width else 200
    height = int(height) if height else 200

    try:
        profile_pic = StudentProfilePicture.objects.get(student=student)
        file_id = profile_pic.google_file_id

        if not file_id:
            return HttpResponse("Profile image not found", status=404)

        return stream_google_drive_image(file_id, width, height)

    except StudentProfilePicture.DoesNotExist:
        return HttpResponse("Profile image not found", status=404)
    except Exception:
        return JsonResponse({"error": "Error streaming profile image."}, status=500)
    
def test_error(request):
    return 5 / 0