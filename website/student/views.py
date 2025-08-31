import json
from django.http import JsonResponse
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
from website.utils import api_key_required, user_token_required
from django.db import transaction
import string
import random
from .utils import create_student_log
from .models import StudentLogs

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

            # Check for existing email
            if Email.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already registered."}, status=400)

            # Check for existing mobile number
            if PhoneNumber.objects.filter(mobile_number=mobile_number).exists():
                return JsonResponse({"error": "Mobile number already registered."}, status=400)

            # Create student and associated records within a transaction
            with transaction.atomic():
                # Create student with full_name
                student = Student.objects.create(
                    full_name=full_name.strip(),  # Save full_name
                    password=make_password(password),
                    authToken=uuid4(),
                )

                # Student Log

                StudentLogs.objects.create(
                    student = student,
                    logs = "Registered Via Email"
                )
                 
                # Link email
                Email.objects.create(
                    student=student,
                    email=email,
                )

                # Link phone number
                PhoneNumber.objects.create(
                    student=student,
                    mobile_number=mobile_number,
                )

            return JsonResponse(
                {
                    "status": "success",
                    "email": email,
                    "mobile_number": mobile_number,
                    "full_name": full_name,  # Include full_name in response
                    "authToken": str(student.authToken),
                },
                status=201,
            )

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)
        except Exception as e:
            # Log the error in production
            return JsonResponse({"error": "Internal server error."}, status=500)


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

            try:
                email_obj = Email.objects.get(email=email)
                user = email_obj.student
                StudentLogs.objects.create(
                    student = student,
                    logs = "Logged in Via Email"
                )

            except Email.DoesNotExist:
                return JsonResponse({"error": "Invalid credentials."}, status=400)

            if not check_password(password, user.password):
                return JsonResponse({"error": "Invalid credentials."}, status=400)
            
            user.authToken = uuid4()
            user.save()

            return JsonResponse(
                {
                    "status": "success",
                    "email": email,
                    "authToken": str(user.authToken),
                },
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)


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

        student = request.user
        uni = get_object_or_404(university, name__iexact=university_name.strip())


        # Check if already shortlisted
        if ShortlistedUniversity.objects.filter(student=student, university=uni).exists():
            return JsonResponse(
                {"message": "University is already shortlisted."}, status=400
            )

        shortlist = ShortlistedUniversity.objects.create(
            student=student, university=uni, added_on=timezone.now()
        )

        create_student_log(request, f"Shortlisted University '{university_name}'")
        return JsonResponse(
            {
                "status": "success",
                "shortlist": {
                    "id": shortlist.id,
                    "student": shortlist.student.full_name,
                    "university": shortlist.university.name,
                    "added_on": shortlist.added_on.strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)


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
            return JsonResponse({"error": "Both university_name and course_name are required."}, status=400)

        student = request.user
        uni = get_object_or_404(university, name__iexact=university_name.strip())
        course = get_object_or_404(Course, university=uni, program_name__iexact=course_name.strip())

        # Check if already shortlisted
        if ShortlistedCourse.objects.filter(student=student, course=course).exists():
            return JsonResponse(
                {"message": "Course is already shortlisted."}, status=400
            )

        shortlist = ShortlistedCourse.objects.create(
            student=student, course=course, added_on=timezone.now()
        )
        create_student_log(request, f"Shortlisted Course '{course_name}'")
        return JsonResponse(
            {
                "status": "success",
                "shortlist": {
                    "id": shortlist.id,
                    "student": shortlist.student.full_name,
                    "course": shortlist.course.program_name,
                    "university": shortlist.course.university.name,
                    "added_on": shortlist.added_on.strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)


@csrf_exempt
@api_key_required
@user_token_required
@require_http_methods(["GET"])
def get_shortlisted_items(request):
    student = request.user

    # Get shortlisted universities
    universities = ShortlistedUniversity.objects.filter(student=student).select_related("university__location")
    uni_list = [
        {
            "id": su.id,
            "university_id": su.university.id,
            "university_name": su.university.name,
            "cover_url": su.university.cover_url,
            "location": {
                "city": su.university.location.city,
                "state": su.university.location.state,
                "country": su.university.location.country,
            },
            "added_on": su.added_on.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for su in universities
    ]

    # Get shortlisted courses
    courses = ShortlistedCourse.objects.filter(student=student).select_related("course__university")
    course_list = [
        {
            "id": sc.id,
            "course_id": sc.course.id,
            "program_name": sc.course.program_name,
            "program_level": sc.course.program_level,
            "tuition_fees": sc.course.tution_fees,  # Added tuition fee
            "university_id": sc.course.university.id,
            "university_name": sc.course.university.name,
            "added_on": sc.added_on.strftime("%Y-%m-%d %H:%M:%S"),
        }
        for sc in courses
    ]
    
    create_student_log(request, f"Opened Shortlisted Page")
    return JsonResponse(
        {
            "status": "success",
            "universities": uni_list,
            "courses": course_list,
        },
        status=200,
    )


@csrf_exempt
@api_key_required
@user_token_required
@require_http_methods(["GET"])
def get_student_details(request):
    try:
        student = request.user
        student_id = student.id

        student_data = {
            'full_name': student.full_name,  # Add full_name
        }

        email_obj = getattr(student, 'email', None)
        email_data = {
            'email': getattr(email_obj, 'email', ''),
        }

        phone_obj = getattr(student, 'phone_number', None)
        phone_number_data = {
            'mobile_number': getattr(phone_obj, 'mobile_number', ''),
        }

        student_details_obj = getattr(student, 'details', None)
        student_details_data = {
            'first_name': getattr(student_details_obj, 'first_name', ''),
            'last_name': getattr(student_details_obj, 'last_name', ''),
            'gender': getattr(student_details_obj, 'gender', ''),
            'dob': student_details_obj.dob.isoformat() if student_details_obj and student_details_obj.dob else '',
            'nationality': getattr(student_details_obj, 'nationality', ''),
            'address': getattr(student_details_obj, 'address', ''),
            'state': getattr(student_details_obj, 'state', ''),
            'city': getattr(student_details_obj, 'city', ''),
            'zip_code': getattr(student_details_obj, 'zip_code', ''),
            'country': getattr(student_details_obj, 'country', ''),
        }

        edu_obj = getattr(student, 'education_details', None)
        education_details_data = {
            'institution_name': getattr(edu_obj, 'institution_name', ''),
            'degree': getattr(edu_obj, 'degree', ''),
            'study_field': getattr(edu_obj, 'study_field', ''),
            'cgpa': str(edu_obj.cgpa) if edu_obj and edu_obj.cgpa is not None else None,
            'start_date': edu_obj.start_date.isoformat() if edu_obj and edu_obj.start_date else '',
            'end_date': edu_obj.end_date.isoformat() if edu_obj and edu_obj.end_date else None,
        }

        experience_details_data = [
            {
                'company_name': exp.company_name,
                'title': exp.title,
                'city': exp.city,
                'country': exp.country,
                'employment_type': exp.employment_type,
                'industry_type': exp.industry_type,
                'start_date': exp.start_date.isoformat(),
                'end_date': exp.end_date.isoformat() if exp.end_date else '',
                'currently_working': exp.currently_working,
            }
            for exp in student.experiences.all()
        ]

        test_obj = getattr(student, 'test_scores', None)
        test_scores_data = {
            'exam_type': getattr(test_obj, 'exam_type', ''),
            'english_exam_type': getattr(test_obj, 'english_exam_type', ''),
            'date': test_obj.date.isoformat() if test_obj and test_obj.date else '',
            'listening_score': getattr(test_obj, 'listening_score', ''),
            'reading_score': getattr(test_obj, 'reading_score', ''),
            'writing_score': getattr(test_obj, 'writing_score', ''),
        }

        pref_obj = getattr(student, 'preference', None)
        preference_data = {
            'country': getattr(pref_obj, 'country', ''),
            'degree': getattr(pref_obj, 'degree', ''),
            'discipline': getattr(pref_obj, 'discipline', ''),
            'sub_discipline': getattr(pref_obj, 'sub_discipline', ''),
            'date': pref_obj.date.isoformat() if pref_obj and pref_obj.date else '',
            'budget': getattr(pref_obj, 'budget', ''),
        }

        shortlisted_universities_data = [
            {
                'university': su.university_id,
                'added_on': su.added_on.isoformat(),
            }
            for su in student.shortlisted_universities.all()
        ]

        choices_data = {
            'gender_choices': [{'value': v, 'label': l} for v, l in StudentDetails.GENDERS],
            'degree_choices': [{'value': v, 'label': l} for v, l in Preference.DEGREE_CHOICES],
            'exam_type_choices': [{'value': v, 'label': l} for v, l in TestScores.EXAM_TYPE_CHOICES],
            'country_choices': [v for v, _ in COUNTRY_CHOICES],
        }

        create_student_log(request, f"Opened Profile Page")
        return JsonResponse({
            'student': student_data,
            'email': email_data,
            'phone_number': phone_number_data,
            'student_details': student_details_data,
            'education_details': education_details_data,
            'experience_details': experience_details_data,
            'test_scores': test_scores_data,
            'preference': preference_data,
            'shortlisted_universities': shortlisted_universities_data,
            'choices': choices_data
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def validate_required_fields(data, required_fields):
    missing_fields = [field for field in required_fields if not data.get(field)]
    return missing_fields


@csrf_exempt
@api_key_required
@user_token_required
@require_http_methods(["POST"])
def update_student_profile(request):
    student = request.user
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON body"}, status=400)

    if not data:
        return JsonResponse({"status": "error", "message": "Empty JSON body"}, status=400)

    results = {}
    allowed_sections = {
        "student",  # Add student section for updating full_name
        "student_details",
        "education_details",
        "test_scores",
        "preference",
        "experience_details",
    }

    # Check for invalid/unknown keys
    unknown_keys = set(data.keys()) - allowed_sections
    if unknown_keys:
        return JsonResponse({
            "status": "error",
            "message": f"Unknown sections provided: {', '.join(unknown_keys)}. Only these are allowed: {', '.join(allowed_sections)}"
        }, status=400)

    try:
        # 1. Student (for updating full_name)
        if "student" in data:
            section = "student"
            student_data = data[section]
            required_fields = ["full_name"]
            missing = validate_required_fields(student_data, required_fields)
            if missing:
                return JsonResponse({"status": "error", "message": f"Missing required fields in {section}: {', '.join(missing)}"}, status=400)

            full_name = student_data.get("full_name").strip()
            # Validate full_name
            if not (1 <= len(full_name) <= 200):
                return JsonResponse(
                    {"status": "error", "message": "Full name must be between 1 and 200 characters."},
                    status=400,
                )

            try:
                with transaction.atomic():
                    student.full_name = full_name
                    student.save()
                    results[section] = "updated"
            except Exception as e:
                results[section] = f"error: {str(e)}"

        # 2. StudentDetails
        if "student_details" in data:
            section = "student_details"
            details_data = data[section]
            required_fields = [
                "first_name", "last_name", "gender", "dob", "nationality",
                "address", "state", "city", "zip_code", "country"
            ]
            missing = validate_required_fields(details_data, required_fields)
            if missing:
                return JsonResponse({"status": "error", "message": f"Missing required fields in {section}: {', '.join(missing)}"}, status=400)

            try:
                with transaction.atomic():
                    StudentDetails.objects.update_or_create(
                        student=student,
                        defaults=details_data
                    )
                    results[section] = "updated"
            except Exception as e:
                results[section] = f"error: {str(e)}"

        # 3. EducationDetails
        if "education_details" in data:
            section = "education_details"
            edu_data = data[section]
            required_fields = ["institution_name", "degree", "study_field", "cgpa", "start_date", "end_date"]
            missing = validate_required_fields(edu_data, required_fields)
            if missing:
                return JsonResponse({"status": "error", "message": f"Missing required fields in {section}: {', '.join(missing)}"}, status=400)

            try:
                with transaction.atomic():
                    EducationDetails.objects.update_or_create(
                        student=student,
                        defaults=edu_data
                    )
                    results[section] = "updated"
            except Exception as e:
                results[section] = f"error: {str(e)}"

        # 4. TestScores
        if "test_scores" in data:
            section = "test_scores"
            ts_data = data[section]
            required_fields = ["exam_type", "english_exam_type", "date", "listening_score", "reading_score", "writing_score"]
            missing = validate_required_fields(ts_data, required_fields)
            if missing:
                return JsonResponse({"status": "error", "message": f"Missing required fields in {section}: {', '.join(missing)}"}, status=400)

            try:
                with transaction.atomic():
                    TestScores.objects.update_or_create(
                        student=student,
                        defaults=ts_data
                    )
                    results[section] = "updated"
            except Exception as e:
                results[section] = f"error: {str(e)}"

        # 5. Preference
        if "preference" in data:
            section = "preference"
            pref_data = data[section]
            required_fields = ["country", "degree", "discipline", "sub_discipline", "date", "budget"]
            missing = validate_required_fields(pref_data, required_fields)
            if missing:
                return JsonResponse({"status": "error", "message": f"Missing required fields in {section}: {', '.join(missing)}"}, status=400)

            try:
                with transaction.atomic():
                    Preference.objects.update_or_create(
                        student=student,
                        defaults=pref_data
                    )
                    results[section] = "updated"
            except Exception as e:
                results[section] = f"error: {str(e)}"

        # 6. ExperienceDetails (List)
        if "experience_details" in data:
            section = "experience_details"
            exp_list = data[section]
            if not isinstance(exp_list, list):
                return JsonResponse({"status": "error", "message": f"{section} should be a list"}, status=400)

            required_fields = [
                "company_name", "title", "city", "country",
                "employment_type", "industry_type", "start_date"
            ]

            for idx, exp in enumerate(exp_list):
                missing = validate_required_fields(exp, required_fields)
                if missing:
                    return JsonResponse({"status": "error", "message": f"Missing required fields in {section}[{idx}]: {', '.join(missing)}"}, status=400)

            try:
                with transaction.atomic():
                    student.experiences.all().delete()
                    for exp in exp_list:
                        ExperienceDetails.objects.create(
                            student=student,
                            **exp
                        )
                    results[section] = "updated"
            except Exception as e:
                results[section] = f"error: {str(e)}"

        create_student_log(request, f"Updated Profile")
        return JsonResponse({"status": "success", "results": results}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)    

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
