import json
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.utils.decorators import method_decorator
from django.views import View
from uuid import uuid4
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import *
from course.models import *
from website.utils import (
    api_key_required,
    user_token_required,
    has_perms,
    token_required,
)
from django.db import transaction
import string
import random
from .utils import create_student_log
from .models import StudentLogs
from django.db import connection
from google import genai
import os
from django.conf import settings
import secrets
import requests

WHATSAPP_TOKEN = settings.WHATSAPP_TOKEN
WHATSAPP_PHONE_NUMBER_ID = settings.WHATSAPP_PHONE_NUMBER_ID

import logging

logger = logging.getLogger(__name__)

# -------------------------
# Sync WhatsApp OTP Sender
# -------------------------
def send_whatsapp_otp(phone_number: str, otp: int):
    url = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": "91" + phone_number,
        "type": "template",
        "template": {
            "name": "auth",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": [{"type": "text", "text": str(otp)}]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [{"type": "text", "text": str(otp)}]
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        data = response.json()
    except Exception as e:
        logger.error(f"Network error sending WhatsApp OTP: {e}")
        return {"status": "error", "reason": "network"}

    # Log all non-success responses for debugging
    if "error" in data:
        logger.error(f"WhatsApp API error: {data}")
        return {"status": "error", "reason": "provider_error"}

    if response.status_code != 200:
        logger.error(f"HTTP error from WhatsApp API: {response.status_code} {data}")
        return {"status": "error", "reason": "provider_error"}

    messages = data.get("messages")
    if messages and isinstance(messages, list) and messages[0].get("message_status") == "accepted":
        return {"status": "success"}

    logger.warning(f"Unexpected WhatsApp API response: {data}")
    return {"status": "error", "reason": "unexpected_response"}


# ---------------- Send OTP ----------------
@csrf_exempt
@require_http_methods(["POST"])
def send_otp(request):
    """
    Generates a 6-digit OTP and calls the request_otp Postgres function.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    phone_number = str(data.get("phone_number", "")).strip()
    if not phone_number.isdigit() or len(phone_number) != 10:
        return JsonResponse({"status": "error", "message": "Invalid phone number"}, status=400)

    otp = str(secrets.randbelow(900000) + 100000)  # 6-digit OTP

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT request_otp(%s, %s);",
                [phone_number, otp]
            )
            result = cursor.fetchone()[0]  # request_otp returns JSON
            # result is a dict if psycopg2 extras JSON is enabled, else string
            if isinstance(result, str):
                result = json.loads(result)

        if result.get("status") == "wait":
            return JsonResponse(result, status=200)

        # Here, you can call your actual WhatsApp/SMS sending function
        send_success = send_whatsapp_otp(phone_number, otp)  # Implement separately
        if send_success.get("status") != "success":
            return JsonResponse({
                "status": "error",
                "message": "Could not send OTP",
                "reason": send_success.get("reason", "unknown")
            }, status=400)

        return JsonResponse({
            "status": "success",
            "message": f"OTP successfully sent to {phone_number}"
        })

    except Exception as e:
        logger.exception("Error sending OTP")
        return JsonResponse({"status": "error", "message": "Internal server error"}, status=500)


# ---------------- Verify OTP ----------------
@csrf_exempt
@require_http_methods(["POST"])
def verify_otp_view(request):
    """
    Verifies OTP using the verify_otp Postgres function.
    """
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    phone_number = str(data.get("phone_number", "")).strip()
    otp = str(data.get("otp", "")).strip()

    if not phone_number.isdigit() or len(phone_number) != 10:
        return JsonResponse({"status": "error", "message": "Invalid phone number"}, status=400)
    if not otp.isdigit() or len(otp) != 6:
        return JsonResponse({"status": "error", "message": "Invalid OTP"}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT verify_otp(%s, %s);",
                [phone_number, otp]
            )
            result = cursor.fetchone()[0]  # verify_otp returns JSON
            if isinstance(result, str):
                result = json.loads(result)

        return JsonResponse(result)

    except Exception as e:
        logger.exception("Error verifying OTP")
        return JsonResponse({"status": "error", "message": "Internal server error"}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(require_http_methods(["POST"]), name="dispatch")
class RegisterView(View):
    @method_decorator(api_key_required)
    def post(self, request):
        try:
            data = json.loads(request.body.decode("utf-8"))

            email = data.get("email")
            password = data.get("password")
            mobile_number = data.get("mobile_number")
            full_name = data.get("full_name")  # Add full_name

            # Validate presence of required fields
            if not email or not password or not mobile_number or not full_name:
                return JsonResponse(
                    {
                        "error": "Email, password, mobile number, and full name are required."
                    },
                    status=400,
                )

            # Validate email format
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({"error": "Invalid email format."}, status=400)

            # Validate mobile number format (basic validation, adjust as needed)
            if not (8 <= len(mobile_number) <= 15 and mobile_number.isdigit()):
                return JsonResponse(
                    {"error": "Invalid mobile number format. Must be 8-15 digits."},
                    status=400,
                )

            # Validate full_name (basic validation, e.g., not empty and reasonable length)
            if not (1 <= len(full_name.strip()) <= 200):
                return JsonResponse(
                    {"error": "Full name must be between 1 and 200 characters."},
                    status=400,
                )

            # Create student and associated records within a transaction
            with transaction.atomic():
                with connection.cursor() as cursor:
                    hashed_password = make_password(password)
                    auth_token = str(uuid4())

                    # Insert student
                    cursor.execute(
                        """
                        INSERT INTO student_student (full_name, password, "authToken")
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        [full_name.strip(), hashed_password, auth_token],
                    )
                    student_id = cursor.fetchone()[0]

                    # Insert student log
                    cursor.execute(
                        """
                        INSERT INTO student_logs (student_id, logs)
                        VALUES (%s, %s)
                        """,
                        [student_id, "Registered Via Email"],
                    )

                    # Insert email
                    cursor.execute(
                        """
                        INSERT INTO student_email (student_id, email)
                        VALUES (%s, %s)
                        """,
                        [student_id, email],
                    )

                    # Insert phone number
                    cursor.execute(
                        """
                        INSERT INTO student_phonenumber (student_id, mobile_number)
                        VALUES (%s, %s)
                        """,
                        [student_id, mobile_number],
                    )

            return JsonResponse(
                {
                    "status": "success",
                    "email": email,
                    "mobile_number": mobile_number,
                    "full_name": full_name,  # Include full_name in response
                    "authToken": auth_token,
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        except Exception as e:
            # Log the error in production
            return JsonResponse(
                {
                    "error": "Internal server error.",
                },
                status=500,
            )
            # return JsonResponse({"error": str(e),}, status=500)


# This view uses django password hashing which is difficult to do in postgres function, so leave it as it is
@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(require_http_methods(["POST"]), name="dispatch")
class LoginView(View):
    @method_decorator(api_key_required)
    def post(self, request):
        try:
            data = json.loads(request.body.decode("utf-8"))
            email = data.get("email")
            password = data.get("password")

            if not email or not password:
                return JsonResponse(
                    {"error": "Both email and password are required."}, status=400
                )

            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT student_id FROM student_email WHERE email = %s LIMIT 1",
                        [email],
                    )
                    row = cursor.fetchone()
                    if not row:
                        return JsonResponse(
                            {"error": "Invalid credentials."}, status=400
                        )

                    student_id = row[0]

                    cursor.execute(
                        "SELECT password FROM student_student WHERE id = %s",
                        [student_id],
                    )
                    row = cursor.fetchone()
                    if not row:
                        return JsonResponse(
                            {"error": "Invalid credentials."}, status=400
                        )

                    db_password = row[0]

                    if not check_password(password, db_password):
                        return JsonResponse(
                            {"error": "Invalid credentials."}, status=400
                        )

                    auth_token = str(uuid4())
                    cursor.execute(
                        'UPDATE student_student SET "authToken" = %s WHERE id = %s',
                        [auth_token, student_id],
                    )

                    cursor.execute(
                        """
                        INSERT INTO student_logs (student_id, logs)
                        VALUES (%s, %s)
                        """,
                        [student_id, "Logged in Via Email"],
                    )

            return JsonResponse(
                {
                    "status": "success",
                    "email": email,
                    "authToken": auth_token,
                },
                status=200,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)

        except Exception:
            return JsonResponse({"error": "Internal server error."}, status=500)


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


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(require_http_methods(["POST"]), name="dispatch")
class GoogleSignInView(View):
    @method_decorator(api_key_required)
    def post(self, request):
        try:
            data = json.loads(request.body.decode("utf-8"))
            email = data.get("email")
            full_name = data.get("full_name")

            # Validate presence of required fields
            if not email or not full_name:
                return JsonResponse(
                    {"error": "Email and full name are required."},
                    status=400,
                )

            # Validate email format
            try:
                validate_email(email)
            except ValidationError:
                return JsonResponse({"error": "Invalid email format."}, status=400)

            # Validate full_name
            if not (1 <= len(full_name.strip()) <= 200):
                return JsonResponse(
                    {"error": "Full name must be between 1 and 200 characters."},
                    status=400,
                )

            with transaction.atomic():
                with connection.cursor() as cursor:
                    # Check if email already exists
                    cursor.execute(
                        """
                        SELECT s.id, s.full_name
                        FROM student_student s
                        JOIN student_email e ON e.student_id = s.id
                        WHERE e.email = %s
                        LIMIT 1
                        """,
                        [email],
                    )
                    row = cursor.fetchone()

                    if row:
                        # Existing student
                        student_id, student_name = row
                        new_token = str(uuid4())

                        # Update authToken
                        cursor.execute(
                            'UPDATE student_student SET "authToken" = %s WHERE id = %s',
                            [new_token, student_id],
                        )

                        # Log login
                        cursor.execute(
                            """
                            INSERT INTO student_logs (student_id, logs, added_on)
                            VALUES (%s, %s, NOW())
                            """,
                            [student_id, "Logged in via Google"],
                        )

                        return JsonResponse(
                            {
                                "status": "success",
                                "message": "User already exists, logged in successfully.",
                                "email": email,
                                "full_name": student_name,
                                "authToken": new_token,
                            },
                            status=200,
                        )

                    else:
                        # New student → register
                        random_password = "".join(
                            random.choices(string.ascii_letters + string.digits, k=12)
                        )
                        hashed_password = make_password(random_password)
                        new_token = str(uuid4())

                        # Insert into student_student
                        cursor.execute(
                            """
                            INSERT INTO student_student (full_name, password, "authToken", added_on)
                            VALUES (%s, %s, %s, NOW())
                            RETURNING id
                            """,
                            [full_name.strip(), hashed_password, new_token],
                        )
                        student_id = cursor.fetchone()[0]

                        # Log registration
                        cursor.execute(
                            """
                            INSERT INTO student_logs (student_id, logs, added_on)
                            VALUES (%s, %s, NOW())
                            """,
                            [student_id, "Registered via Google"],
                        )

                        # Insert email
                        cursor.execute(
                            """
                            INSERT INTO student_email (student_id, email, added_on)
                            VALUES (%s, %s, NOW())
                            """,
                            [student_id, email],
                        )

                        return JsonResponse(
                            {
                                "status": "success",
                                "message": "User registered successfully via Google Sign-In.",
                                "email": email,
                                "full_name": full_name,
                                "authToken": new_token,
                            },
                            status=201,
                        )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        except Exception as e:
            # return JsonResponse(
            #     {"error": "Internal server error.", "details": str(e)}, status=500
            # )
            return JsonResponse(
                    {"error": "Internal server error."}, status=500
                )


@require_http_methods(['GET'])
@token_required
def get_all_students(request):
    employee = request.user  # comes from @token_required

    # Permission check
    if not has_perms(employee.id, ["student_logs_view"]):
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to perform this task'
        }, status=403)
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT s.id, s.full_name, b.name AS bucket_name
            FROM student_student AS s
            LEFT JOIN student_bucket AS b ON s.category_id = b.id;
        """)
        rows = cursor.fetchall()

    # Convert rows -> list of dicts
    students = [{"id": row[0], "full_name": row[1], "bucket":row[2]} for row in rows]

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
        return JsonResponse({"error": "an error occured"}, status=500)


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
        return JsonResponse({"status": "error", "error": f"Unexpected error"}, status=500)
