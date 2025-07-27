import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.hashers import make_password, check_password
from django.utils.decorators import method_decorator
from django.views import View
from .models import Student
from uuid import uuid4
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import *
from website.utils import api_key_required, user_token_required
from django.db import transaction


@method_decorator(csrf_exempt, name="dispatch")
@method_decorator(require_http_methods(["POST"]), name="dispatch")
class RegisterView(View):
    @method_decorator(api_key_required)
    def post(self, request):
        try:
            data = json.loads(request.body.decode("utf-8"))

            username = data.get("username")
            email_address = data.get("email")
            password = data.get("password")

            # Validate presence of required fields
            if not username or not email_address or not password:
                return JsonResponse(
                    {"error": "All fields (username, email, password) are required."},
                    status=400,
                )

            # Validate email format
            try:
                validate_email(email_address)
            except ValidationError:
                return JsonResponse({"error": "Invalid email format."}, status=400)

            # Check for existing username or email
            if Student.objects.filter(username=username).exists():
                return JsonResponse({"error": "Username already exists."}, status=400)

            if Email.objects.filter(email=email_address).exists():
                return JsonResponse({"error": "Email already registered."}, status=400)

            # Create student
            student = Student.objects.create(
                username=username,
                password=make_password(password),
                authToken=uuid4(),
            )

            # Link email
            Email.objects.create(
                student=student,
                email=email_address,
            )

            return JsonResponse(
                {
                    "status": "success",
                    "username": student.username,
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
            username = data.get("username")
            password = data.get("password")

            if not username or not password:
                return JsonResponse(
                    {"error": "Both username and password are required."}, status=400
                )

            try:
                user = Student.objects.get(username=username)
            except Student.DoesNotExist:
                return JsonResponse({"error": "Invalid credentials."}, status=400)

            if not check_password(password, user.password):
                return JsonResponse({"error": "Invalid credentials."}, status=400)
            
            user.authToken = uuid4()
            user.save()

            # Generate a simple session token (JWT recommended for production)
            return JsonResponse(
                {
                    "status":"success",
                    "username": user.username,
                    "authToken": user.authToken,
                },
                status=200,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON."}, status=400)


@csrf_exempt
@user_token_required
@require_http_methods(["POST"])
def add_to_shortlist(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
        student_id = data.get("student_id")
        university_id = data.get("university_id")

        if not student_id or not university_id:
            return JsonResponse(
                {"error": "student_id and university_id are required."},
                status=400,
            )

        # Fetch student and university objects
        student = get_object_or_404(Student, id=student_id)
        uni = get_object_or_404(university, id=university_id)

        # Check if this university is already shortlisted by this student
        if ShortlistedUniversity.objects.filter(student=student, university=uni).exists():
            return JsonResponse(
                {"message": "University is already shortlisted."}, status=400
            )

        # Create shortlisted university
        shortlist = ShortlistedUniversity.objects.create(
            student=student, university=uni, added_on=timezone.now()
        )

        return JsonResponse(
            {
                "status": "success",
                "shortlist": {
                    "id": shortlist.id,
                    "student": shortlist.student.username,
                    "university": shortlist.university.name,
                    "added_on": shortlist.added_on.strftime("%Y-%m-%d %H:%M:%S"),
                },
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format."}, status=400)

@csrf_exempt
@user_token_required
@require_http_methods(["GET"])
def get_student_details(request):
    try:
        student = request.user
        student_id = student.id

        student_data = {
            'username': student.username
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
            'country_choices': [v for v, _ in COUNTRY_CHOICES],  # ← as array of country names
        }

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
@user_token_required
@require_http_methods(["POST"])
def update_student_profile(request):
    student = request.user
    data = json.loads(request.body.decode("utf-8"))

    if not data:
        return JsonResponse({
            "status": "error",
            "message": "Empty JSON body"
        }, status=400)

    results = {}
    allowed_sections = {
        "student_details",
        "education_details",
        "test_scores",
        "preference",
        "experience_details",
    }

    # 🔒 Check for invalid/unknown keys
    unknown_keys = set(data.keys()) - allowed_sections
    if unknown_keys:
        return JsonResponse({
            "status": "error",
            "message": f"Unknown sections provided: {', '.join(unknown_keys)}. Only these are allowed: {', '.join(allowed_sections)}"
        }, status=400)

    try:
        # 1. StudentDetails
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

        # 2. EducationDetails
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

        # 3. TestScores
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

        # 4. Preference
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

        # 5. ExperienceDetails (List)
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

        return JsonResponse({"status": "success", "results": results}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)