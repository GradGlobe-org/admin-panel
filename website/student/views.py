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
from website.utils import api_key_required, user_token_required, has_perms, token_required
from django.db import transaction
import string
import random
from .utils import create_student_log
from .models import StudentLogs
from django.db import connection
from google import genai
import os



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
                    {"error": "Email, password, mobile number, and full name are required."},
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
            return JsonResponse({"error": "Internal server error.",}, status=500)
            # return JsonResponse({"error": str(e),}, status=500)


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
                        return JsonResponse({"error": "Invalid credentials."}, status=400)

                    student_id = row[0]

                    cursor.execute(
                        "SELECT password FROM student_student WHERE id = %s",
                        [student_id],
                    )
                    row = cursor.fetchone()
                    if not row:
                        return JsonResponse({"error": "Invalid credentials."}, status=400)

                    db_password = row[0]

                    if not check_password(password, db_password):
                        return JsonResponse({"error": "Invalid credentials."}, status=400)

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
                    """
                    SELECT id, name
                    FROM university_university
                    WHERE LOWER(name) = LOWER(%s)
                    LIMIT 1
                    """,
                    [university_name.strip()],
                )
                uni_row = cursor.fetchone()
                if not uni_row:
                    return JsonResponse({"error": "University not found."}, status=404)

                uni_id, uni_name = uni_row

                cursor.execute(
                    """
                    SELECT 1
                    FROM student_shortlisteduniversity
                    WHERE student_id = %s AND university_id = %s
                    LIMIT 1
                    """,
                    [student_id, uni_id],
                )
                if cursor.fetchone():
                    return JsonResponse(
                        {"message": "University is already shortlisted."}, status=400
                    )

                added_on = timezone.now()
                cursor.execute(
                    """
                    INSERT INTO student_shortlisteduniversity (student_id, university_id, added_on)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    [student_id, uni_id, added_on],
                )
                shortlist_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO student_logs (student_id, logs)
                    VALUES (%s, %s)
                    """,
                    [student_id, f"Shortlisted University '{uni_name}'"],
                )

        return JsonResponse(
            {
                "status": "success",
                "shortlist": {
                    "id": shortlist_id,
                    "student": request.user.full_name,
                    "university": uni_name,
                    "added_on": added_on.strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)

    except Exception:
        return JsonResponse({"error": "Internal server error."}, status=500)


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
                #Get university
                cursor.execute(
                    """
                    SELECT id, name
                    FROM university_university
                    WHERE LOWER(name) = LOWER(%s)
                    LIMIT 1
                    """,
                    [university_name.strip()],
                )
                uni_row = cursor.fetchone()
                if not uni_row:
                    return JsonResponse({"error": "University not found."}, status=404)

                uni_id, uni_name = uni_row

                #Get course
                cursor.execute(
                    """
                    SELECT id, program_name
                    FROM course_course
                    WHERE university_id = %s
                      AND LOWER(program_name) = LOWER(%s)
                    LIMIT 1
                    """,
                    [uni_id, course_name.strip()],
                )
                course_row = cursor.fetchone()
                if not course_row:
                    return JsonResponse({"error": "Course not found."}, status=404)

                course_id, program_name = course_row

                #Check if already shortlisted
                cursor.execute(
                    """
                    SELECT 1
                    FROM student_shortlistedcourse
                    WHERE student_id = %s AND course_id = %s
                    LIMIT 1
                    """,
                    [student_id, course_id],
                )
                if cursor.fetchone():
                    return JsonResponse(
                        {"message": "Course is already shortlisted."}, status=400
                    )

                #Insert shortlist
                added_on = timezone.now()
                cursor.execute(
                    """
                    INSERT INTO student_shortlistedcourse (student_id, course_id, added_on)
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    [student_id, course_id, added_on],
                )
                shortlist_id = cursor.fetchone()[0]

                #Insert student log
                cursor.execute(
                    """
                    INSERT INTO student_logs (student_id, logs)
                    VALUES (%s, %s)
                    """,
                    [student_id, f"Shortlisted Course '{program_name}'"],
                )

        return JsonResponse(
            {
                "status": "success",
                "shortlist": {
                    "id": shortlist_id,
                    "student": request.user.full_name,
                    "course": program_name,
                    "university": uni_name,
                    "added_on": added_on.strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)

    except Exception:
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
                # Call the Postgres function for universities
                cursor.execute("SELECT get_shortlisted_universities(%s)", [student_id])
                uni_result = cursor.fetchone()[0]  # JSON result from function
                uni_list = uni_result if uni_result is not None else []

                # Fetch shortlisted courses directly
                cursor.execute(
                    """
                    SELECT sc.id,
                           c.id AS course_id,
                           c.program_name,
                           c.program_level,
                           c.tution_fees,
                           u.id AS university_id,
                           u.name AS university_name,
                           sc.added_on
                    FROM student_shortlistedcourse sc
                    JOIN course_course c ON sc.course_id = c.id
                    JOIN university_university u ON c.university_id = u.id
                    WHERE sc.student_id = %s
                    ORDER BY sc.added_on DESC
                    """,
                    [student_id],
                )
                course_rows = cursor.fetchall()

                course_list = [
                    {
                        "id": row[0],
                        "course_id": row[1],
                        "program_name": row[2],
                        "program_level": row[3],
                        "tuition_fees": row[4],
                        "university_id": row[5],
                        "university_name": row[6],
                        "added_on": row[7].strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    for row in course_rows
                ]

                # Log the action (kept in Django for flexibility)
                cursor.execute(
                    """
                    INSERT INTO student_logs (student_id, logs, added_on)
                    VALUES (%s, %s, NOW())
                    """,
                    [student_id, "Opened Shortlisted Page"],
                )

        return JsonResponse(
            {
                "status": "success",
                "universities": uni_list,
                "courses": course_list,
            },
            status=200,
        )

    except Exception as e:
        return JsonResponse(
            {"error": "An unexpected error occurred."}, status=500
        )
    
@csrf_exempt
@api_key_required
@user_token_required
@require_http_methods(["GET"])
def get_student_details(request):
    try:
        student = request.user
        student_id = student.id
    
    except Exception as e:
        return JsonResponse({'error': 'Error, kindly enter correct student id or try again'})

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT get_student_full_details(%s);", [student_id])
            row = cursor.fetchone()
            result_json = row[0] if row else {}

        return JsonResponse(result_json)

    except Exception as e:
        return JsonResponse({'error': "An error occured, try again later"}, status=500)


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
        return JsonResponse({"status": "error", "message": "Invalid JSON body"}, status=400)

    if not data:
        return JsonResponse({"status": "error", "message": "Empty JSON body"}, status=400)

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
        return JsonResponse({
            "status": "error",
            "message": f"Unknown sections provided: {', '.join(unknown_keys)}. Only these are allowed: {', '.join(allowed_sections)}"
        }, status=400)

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:

                # 1️⃣ Student (update full_name)
                if "student" in data:
                    section = "student"
                    full_name = data[section].get("full_name", "").strip()
                    if not (1 <= len(full_name) <= 200):
                        return JsonResponse({"status": "error", "message": "Full name must be between 1 and 200 characters."}, status=400)

                    cursor.execute(
                        "UPDATE student_student SET full_name = %s WHERE id = %s",
                        [full_name, student_id]
                    )
                    results[section] = "updated"

                # 2️⃣ StudentDetails
                if "student_details" in data:
                    section = "student_details"
                    sd = data[section]
                    cursor.execute("""
                        INSERT INTO student_studentdetails(student_id, first_name, last_name, gender, dob, nationality, address, state, city, zip_code, country)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_id) 
                        DO UPDATE SET first_name=EXCLUDED.first_name, last_name=EXCLUDED.last_name,
                                      gender=EXCLUDED.gender, dob=EXCLUDED.dob, nationality=EXCLUDED.nationality,
                                      address=EXCLUDED.address, state=EXCLUDED.state, city=EXCLUDED.city,
                                      zip_code=EXCLUDED.zip_code, country=EXCLUDED.country
                    """, [
                        student_id, sd.get("first_name"), sd.get("last_name"), sd.get("gender"), sd.get("dob"),
                        sd.get("nationality"), sd.get("address"), sd.get("state"), sd.get("city"),
                        sd.get("zip_code"), sd.get("country")
                    ])
                    results[section] = "updated"

                # 3️⃣ EducationDetails
                if "education_details" in data:
                    section = "education_details"
                    ed = data[section]
                    cursor.execute("""
                        INSERT INTO student_educationdetails(student_id, institution_name, degree, study_field, cgpa, start_date, end_date)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_id)
                        DO UPDATE SET institution_name=EXCLUDED.institution_name, degree=EXCLUDED.degree,
                                      study_field=EXCLUDED.study_field, cgpa=EXCLUDED.cgpa,
                                      start_date=EXCLUDED.start_date, end_date=EXCLUDED.end_date
                    """, [
                        student_id, ed.get("institution_name"), ed.get("degree"), ed.get("study_field"),
                        ed.get("cgpa"), ed.get("start_date"), ed.get("end_date")
                    ])
                    results[section] = "updated"

                # 4️⃣ TestScores
                if "test_scores" in data:
                    section = "test_scores"
                    ts = data[section]
                    cursor.execute("""
                        INSERT INTO student_testscores(student_id, exam_type, english_exam_type, date, listening_score, reading_score, writing_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_id)
                        DO UPDATE SET exam_type=EXCLUDED.exam_type, english_exam_type=EXCLUDED.english_exam_type,
                                      date=EXCLUDED.date, listening_score=EXCLUDED.listening_score,
                                      reading_score=EXCLUDED.reading_score, writing_score=EXCLUDED.writing_score
                    """, [
                        student_id, ts.get("exam_type"), ts.get("english_exam_type"), ts.get("date"),
                        ts.get("listening_score"), ts.get("reading_score"), ts.get("writing_score")
                    ])
                    results[section] = "updated"

                # 5️⃣ Preference
                if "preference" in data:
                    section = "preference"
                    pref = data[section]
                    cursor.execute("""
                        INSERT INTO student_preference(student_id, country, degree, discipline, sub_discipline, date, budget)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (student_id)
                        DO UPDATE SET country=EXCLUDED.country, degree=EXCLUDED.degree,
                                      discipline=EXCLUDED.discipline, sub_discipline=EXCLUDED.sub_discipline,
                                      date=EXCLUDED.date, budget=EXCLUDED.budget
                    """, [
                        student_id, pref.get("country"), pref.get("degree"), pref.get("discipline"),
                        pref.get("sub_discipline"), pref.get("date"), pref.get("budget")
                    ])
                    results[section] = "updated"

                # 6️⃣ ExperienceDetails (list)
                if "experience_details" in data:
                    section = "experience_details"
                    exp_list = data[section]
                    if not isinstance(exp_list, list):
                        return JsonResponse({"status": "error", "message": f"{section} should be a list"}, status=400)

                    cursor.execute("DELETE FROM student_experiencedetails WHERE student_id = %s", [student_id])
                    for exp in exp_list:
                        cursor.execute("""
                            INSERT INTO student_experiencedetails(student_id, company_name, title, city, country, employment_type, industry_type, start_date, end_date, currently_working)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, [
                            student_id, exp.get("company_name"), exp.get("title"), exp.get("city"), exp.get("country"),
                            exp.get("employment_type"), exp.get("industry_type"), exp.get("start_date"), exp.get("end_date"),
                            exp.get("currently_working", False)
                        ])
                    results[section] = "updated"

        # Log action (keep your existing function)
        create_student_log(request, f"Updated Profile")
        return JsonResponse({"status": "success", "results": results}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": "Oh! Uh! Some error happended, try again later"}, status=500)
  

@require_http_methods(['GET'])
def get_all_choices(request):
    choices = {
        "countries": [country for country, _ in COUNTRY_CHOICES],
        "genders": [gender for gender, _ in [('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]],
        "degree_choices": [deg for deg, _ in EducationDetails.DEGREE_CHOICES],
        "study_fields": [field for field, _ in EducationDetails.FIELD_CHOICES],
        "employment_types": [emp for emp, _ in ExperienceDetails.EMPLOYMENT_TYPE_CHOICES],
        "industry_types": [ind for ind, _ in ExperienceDetails.INDUSTRY_TYPE_CHOICES],
        "exam_types": [exam for exam, _ in TestScores.EXAM_TYPE_CHOICES],
        "english_exam_types": [exam for exam, _ in TestScores.ENGLISH_EXAM_CHOICES],
        "preference_degrees": [deg for deg, _ in Preference.DEGREE_CHOICES],
        "preference_disciplines": [disc for disc, _ in Preference.DISCIPLINE_CHOICES],
        "preference_sub_disciplines": [sub for sub, _ in Preference.SUB_DISCIPLINE_CHOICES],
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

            # Check if email already exists
            try:
                email_obj = Email.objects.get(email=email)
                student = email_obj.student

                StudentLogs.objects.create(
                    student = student,
                    logs = "Logged in via google"
                )

                # Update authToken for existing user
                student.authToken = uuid4()
                student.save()
                return JsonResponse(
                    {
                        "status": "success",
                        "message": "User already exists, logged in successfully.",
                        "email": email,
                        "full_name": student.full_name,
                        "authToken": str(student.authToken),
                    },
                    status=200,
                )
            except Email.DoesNotExist:
                # Generate a random password
                random_password = ''.join(random.choices(
                    string.ascii_letters + string.digits, k=12
                ))
                # Create new user within a transaction
                try:
                    with transaction.atomic():
                        # Create student with full_name and random password
                        student = Student.objects.create(
                            full_name=full_name.strip(),
                            authToken=uuid4(),
                            password=make_password(random_password),  # Hash the random password
                        )

                        # Student Log
                        StudentLogs.objects.create(
                            student = student,
                            logs = "Registered Via Google"
                        )

                        # Link email
                        Email.objects.create(
                            student=student,
                            email=email,
                        )
                        
                        # Skip phone_number for Google Sign-In
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Failed to create user: {str(e)}", exc_info=True)
                    return JsonResponse(
                        {"error": "Failed to create user.", "details": str(e)},
                        status=500,
                    )

                return JsonResponse(
                    {
                        "status": "success",
                        "message": "User registered successfully via Google Sign-In.",
                        "email": email,
                        "full_name": full_name,
                        "authToken": str(student.authToken),
                    },
                    status=201,
                )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Google Sign-In Error: {str(e)}", exc_info=True)
            return JsonResponse(
                {"error": "Internal server error.", "details": str(e)},
                status=500,
            )

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
        cursor.execute("SELECT id, full_name FROM student_student;")
        rows = cursor.fetchall()

    # Convert rows -> list of dicts
    students = [{"id": row[0], "full_name": row[1]} for row in rows]

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
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to perform this task'
        }, status=403)
    
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
            model="gemini-2.5-flash",
            contents=[prompt]
        )

        def event_stream():
            for chunk in stream:
                if hasattr(chunk, "text") and chunk.text:
                    yield chunk.text

        return StreamingHttpResponse(event_stream(), content_type='text/plain')

    except Exception as e:
        return JsonResponse({"error": "An error occured, try again later"}, status=500)

@require_http_methods(['POST'])
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
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to perform this task'
        }, status=403)

    try:
        if request.method != "POST":
            return JsonResponse({"status": "error", "message": "POST method required"}, status=405)

        # Read student_id from POST JSON body
        try:
            body = json.loads(request.body.decode("utf-8"))
            student_id = body.get("student_id")
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON body"}, status=400)

        if not student_id:
            return JsonResponse({"status": "error", "message": "student_id is required"}, status=400)

        student_id = int(student_id)

        # --- Fetch student data from Postgres ---
        with connection.cursor() as cursor:
            cursor.execute("SELECT get_student_details_summary(%s);", [student_id])
            row = cursor.fetchone()

        if not row or not row[0]:
            return JsonResponse({
                "status": "error",
                "message": "Student not found"
            }, status=404)

        student_data = json.loads(row[0]) if isinstance(row[0], str) else row[0]

        # --- Prepare prompt for Gemini ---
        prompt = f"""
        Analyze this student's profile and generate a detailed, structured summary including the following:

        1. **Interested Universities & Courses:** List the actual names of the universities and courses the student has shortlisted. Include location, degree type, and field of study. If there are multiple universities or courses, summarize the main focus areas and priorities.

        2. **Educational Background:** Include degree, field of study, CGPA, key achievements, and language proficiency (e.g., IELTS scores).

        3. **Professional Experience:** Summarize relevant work experience, job titles, companies, locations, employment type, duration, and notable achievements.

        4. **Personal Details:** Include nationality and current country of residence.

        Keep the summary clear, structured and detailed, so a counselor can quickly understand the student’s profile and interests.

        Student data (JSON): {json.dumps(student_data)}

        """

        return stream_gemini_response(prompt)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": "An error occured"
        }, status=500)