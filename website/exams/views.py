from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import json
from website.utils import token_required, user_token_required
from django.db import connection, transaction
from django.utils import timezone
from exams.models import TestStatus, Question, Option, Answer

# @csrf_exempt
# @token_required
# def create_test_view(request):
#     employee = request.user
#     employee_id = employee.id

#     if request.method != "POST":
#         return JsonResponse({"success": False, "error": "Invalid request"}, status=405)

#     try:
#         data = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({"success": False, "error": "Invalid JSON payload"}, status=400)

#     title = data.get("title")
#     questions_data = data.get("questions")

#     # 🔒 Validate title
#     if not title or not title.strip():
#         return JsonResponse({"success": False, "error": "title is required"}, status=400)

#     # 🔒 Validate questions
#     if not isinstance(questions_data, list) or len(questions_data) == 0:
#         return JsonResponse({"success": False, "error": "At least one question is required"}, status=400)

#     # ✅ Defaults
#     description = data.get("description", "")
#     duration_minutes = data.get("duration_minutes", 30)
#     priority = data.get("priority", "low")
#     negative_marking_factor = data.get("negative_marking_factor", 0)

#     # 🔒 Duration validation
#     if not isinstance(duration_minutes, int) or duration_minutes <= 0:
#         return JsonResponse({"success": False, "error": "duration_minutes must be a positive integer"}, status=400)

#     # 🔒 Priority validation
#     if priority not in ["low", "med", "high"]:
#         return JsonResponse({"success": False, "error": "Invalid priority. Must be one of: low, med, high"}, status=400)

#     # 🔒 Negative marking validation
#     if negative_marking_factor not in [0, 0.25, 0.5, 0.33, 0.2]:
#         return JsonResponse({"success": False, "error": "Invalid negative_marking_factor. Allowed: 0, 0.25, 0.5, 0.33, 0.2"}, status=400)

#     # 🔒 Validate each question before hitting DB
#     for idx, q in enumerate(questions_data, start=1):
#         q_type = q.get("question_type", "MCQ")
#         if not q.get("question") or not q["question"].strip():
#             return JsonResponse({"success": False, "error": f"Question {idx} must have non-empty text"}, status=400)

#         if q_type not in ["MCQ", "SUB"]:
#             return JsonResponse({"success": False, "error": f"Question {idx} has invalid type. Allowed: MCQ, SUB"}, status=400)

#         marks = q.get("marks", 1.0)
#         try:
#             marks = float(marks)
#             if marks <= 0:
#                 return JsonResponse({"success": False, "error": f"Question {idx} marks must be positive"}, status=400)
#         except ValueError:
#             return JsonResponse({"success": False, "error": f"Question {idx} marks must be a number"}, status=400)

#         order = q.get("order")
#         if order is not None:
#             try:
#                 order = int(order)
#                 if order < 0:
#                     return JsonResponse({"success": False, "error": f"Question {idx} order must be non-negative"}, status=400)
#             except ValueError:
#                 return JsonResponse({"success": False, "error": f"Question {idx} order must be an integer"}, status=400)

#         if q_type == "MCQ":
#             options = q.get("options", [])
#             if not isinstance(options, list) or len(options) == 0:
#                 return JsonResponse({"success": False, "error": f"Question {idx} must have options"}, status=400)

#             if q.get("options") and q_type == "SUB":
#                 return JsonResponse({"success": False, "error": f"Subjective Question {idx} should not have options"}, status=400)

#             correct_count = sum(1 for opt in options if opt.get("is_correct", False))
#             if correct_count == 0:
#                 return JsonResponse({"success": False, "error": f"Question {idx} must have at least one correct option"}, status=400)

#             for j, opt in enumerate(options, start=1):
#                 if not opt.get("option_name") or not opt["option_name"].strip():
#                     return JsonResponse({"success": False, "error": f"Option {j} in Question {idx} must have non-empty option_name"}, status=400)
#                 if not isinstance(opt.get("is_correct", False), bool):
#                     return JsonResponse({"success": False, "error": f"Option {j} in Question {idx} is_correct must be boolean"}, status=400)

#     # 🚀 Insert into DB
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute(
#                 """
#                 SELECT create_test_with_questions(%s, %s, %s, %s, %s, %s, %s)
#                 """,
#                 [
#                     employee_id,
#                     title,
#                     description,
#                     duration_minutes,
#                     priority,
#                     negative_marking_factor,
#                     json.dumps(questions_data)  # ensure JSON
#                 ]
#             )
#             test_id = cursor.fetchone()[0]

#         return JsonResponse({"success": True, "test_id": test_id}, status=201)

#     except Exception as e:
#         return JsonResponse({"success": False, "error": f"Database error: {str(e)}"}, status=400)


# @csrf_exempt
# @token_required
# def get_all_tests_view(request):
#     if request.method != "GET":
#         return JsonResponse({"success": False, "error": "Invalid request method. Use GET."}, status=405)

#     employee = request.user
#     employee_id = employee.id

#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT * FROM get_all_tests()")
#             columns = [col[0] for col in cursor.description]
#             tests = [dict(zip(columns, row)) for row in cursor.fetchall()]

#         return JsonResponse({
#             "success": True,
#             "tests": tests,
#             "count": len(tests)
#         }, status=200)

#     except Exception as e:
#         return JsonResponse({"success": False, "error": f"Database error: {str(e)}"}, status=500)
    
# @csrf_exempt
# @token_required
# def get_employee_tests_view(request):
#     if request.method != "GET":
#         return JsonResponse({"success": False, "error": "Invalid request method. Use GET."}, status=405)

#     employee = request.user
#     employee_id = employee.id

#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT * FROM get_all_tests(%s)", [employee_id])
#             columns = [col[0] for col in cursor.description]
#             tests = [dict(zip(columns, row)) for row in cursor.fetchall()]

#         return JsonResponse({
#             "success": True,
#             "tests": tests,
#             "count": len(tests)
#         }, status=200)

#     except Exception as e:
#         return JsonResponse({"success": False, "error": f"Database error: {str(e)}"}, status=500)
    

# @csrf_exempt
# @token_required
# def add_test_to_course_view(request):
#     if request.method != "POST":
#         return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

#     try:
#         data = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)

#     course_id = data.get("course_id")
#     test_id = data.get("test_id")
#     order = data.get("order")  # optional

#     # Input validation
#     if not course_id:
#         return JsonResponse({"status": "error", "message": "course_id is required"}, status=400)
#     if not test_id:
#         return JsonResponse({"status": "error", "message": "test_id is required"}, status=400)

#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT add_test_to_course(%s, %s, %s)", [course_id, test_id, order])
#             result = cursor.fetchone()[0]  # JSON returned from function

#         return JsonResponse(result, status=200 if result.get('status') == 'success' else 400)

#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=400)
    
# @csrf_exempt
# @token_required
# def assign_course_to_student_view(request):
#     if request.method != "POST":
#         return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

#     try:
#         data = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)

#     student_id = data.get("student_id")
#     course_id = data.get("course_id")

#     # Validate input
#     if not student_id:
#         return JsonResponse({"status": "error", "message": "student_id is required"}, status=400)
#     if not course_id:
#         return JsonResponse({"status": "error", "message": "course_id is required"}, status=400)

#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT assign_course_to_student(%s, %s)", [student_id, course_id])
#             result = cursor.fetchone()[0]  # JSON returned from function

#         return JsonResponse(result, status=200 if result.get('status') == 'success' else 400)

#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=400)
    

# @csrf_exempt
# @token_required
# def create_course_view(request):
#     if request.method != "POST":
#         return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

#     try:
#         data = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)

#     name = data.get("name")
#     description = data.get("description", "")

#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT create_course(%s, %s)", [name, description])
#             result = cursor.fetchone()[0]

#         return JsonResponse(result, status=200 if result.get('status') == 'success' else 400)

#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=400)
    

# @csrf_exempt
# @token_required
# def get_all_courses_view(request):
#     if request.method != "GET":
#         return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT get_all_courses()")
#             result = cursor.fetchone()[0]

#         return JsonResponse(result, status=200 if result.get('status') == 'success' else 400)

#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=400)
    
    
@csrf_exempt
@user_token_required
def get_student_courses_with_test_status_view(request):
    if request.method != "GET":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    student_id = request.user.id  # from token

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT get_student_courses_with_test_status(%s)", 
                [student_id]
            )
            result = cursor.fetchone()[0]  # JSON from function

        return JsonResponse(result, status=200 if result.get('status') == 'success' else 400)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    

@csrf_exempt
@user_token_required
def get_test_rules_view(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request method"},
            status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON payload"},
            status=400
        )

    test_id = data.get("test_id")
    if not test_id:
        return JsonResponse(
            {"status": "error", "message": "test_id is required"},
            status=400
        )

    student_id = request.user.id

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT get_test_rules_for_student(%s, %s)",
                [student_id, test_id]
            )
            result = cursor.fetchone()[0]

        # Convert JSONB (string) → Python dict
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except Exception:
                return JsonResponse(
                    {"status": "error", "message": "Invalid JSON from database"},
                    status=500
                )

        # Ensure valid dict
        if not isinstance(result, dict):
            return JsonResponse(
                {"status": "error", "message": "Invalid response from database"},
                status=500
            )

        # Choose status code based on eligibility/error
        status_code = 200 if result.get("status") == "success" else 403
        return JsonResponse(result, status=status_code)

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=500
        )
    

@csrf_exempt
@user_token_required
def start_or_resume_test_view(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Invalid request method"},
            status=405
        )

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"status": "error", "message": "Invalid JSON payload"},
            status=400
        )

    test_id = data.get("test_id")
    if not test_id:
        return JsonResponse(
            {"status": "error", "message": "test_id is required"},
            status=400
        )

    student_id = request.user.id  # assumes request.user is Student

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT start_or_resume_test(%s, %s)",
                [student_id, test_id]
            )
            result = cursor.fetchone()[0]  # get JSONB result

        # Determine HTTP status based on eligibility
        if isinstance(result, str):
            result = json.loads(result)

        http_status = 200 if result.get("eligible") else 403

        return JsonResponse(result, status=http_status)

    except Exception as e:
        # Log error (optional)
        print(f"Error in start_or_resume_test_view: {e}")

        return JsonResponse(
            {"status": "error", "eligible": False, "message": str(e)},
            status=500
        )


@csrf_exempt
@user_token_required
def save_student_answer_view(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    try:
        payload = json.loads(request.body)
        student_id = request.user.id  # From token
        test_id = payload.get("test_id")
        question_id = payload.get("question_id")
        selected_option_ids = payload.get("selected_option_ids", [])
        subjective_answer = payload.get("subjective_answer", None)

        if not test_id or not question_id:
            return JsonResponse({"status": "error", "message": "Missing test_id or question_id"}, status=400)

        # Fetch test status
        try:
            test_status = TestStatus.objects.get(student_id=student_id, test_id=test_id)
        except TestStatus.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Test not assigned to this student"}, status=400)

        # Check if test is active
        now = timezone.now()
        if test_status.status in ["completed", "expired"] or (test_status.valid_till and test_status.valid_till < now):
            if test_status.status != "completed":
                test_status.status = "expired"
                test_status.completed_at = now
                test_status.save()
            return JsonResponse({"status": "error", "message": "Test time has expired"}, status=400)

        # Fetch question
        try:
            question = Question.objects.get(id=question_id, section__test_id=test_id)
        except Question.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Question does not belong to this test"}, status=400)

        # Handle MCQ
        if question.question_type == "MCQ":
            # Validate option IDs
            valid_option_ids = set(Option.objects.filter(question=question).values_list('id', flat=True))
            if any(opt_id not in valid_option_ids for opt_id in selected_option_ids):
                return JsonResponse({"status": "error", "message": "One or more selected options are invalid"}, status=400)

            # Check single-answer constraint
            if question.is_single_answer and len(selected_option_ids) > 1:
                return JsonResponse({"status": "error", "message": "This question allows only a single answer"}, status=400)

        # Normalize subjective answer
        if subjective_answer is not None:
            subjective_answer = subjective_answer.strip()
            if subjective_answer == "":
                subjective_answer = None

        # Fetch or create Answer
        answer, created = Answer.objects.get_or_create(
            test_status=test_status,
            question=question,
            defaults={
                "subjective_answer": subjective_answer,
                "marks_obtained": 0
            }
        )

        # Update answer if exists
        if not created:
            answer.subjective_answer = subjective_answer
            answer.selected_options.clear()

        # Set selected options for MCQ
        if question.question_type == "MCQ":
            if selected_option_ids:
                options = Option.objects.filter(id__in=selected_option_ids)
                answer.selected_options.add(*options)

        answer.answered_at = timezone.now()
        answer.save()

        return JsonResponse({"status": "success", "message": "Answer saved successfully"}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
@user_token_required
def confirm_before_submit_view(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)

    student_id = request.user.id
    test_id = data.get("test_id")

    if not test_id:
        return JsonResponse({"status": "error", "message": "test_id is required"}, status=400)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT confirm_before_submit(%s, %s)",
                [student_id, test_id]
            )
            result_str = cursor.fetchone()[0]  # this is a string from Postgres

        # Convert the string to Python dict
        result = json.loads(result_str) if isinstance(result_str, str) else result_str

        return JsonResponse(result, status=200 if result.get("status") == "success" else 400)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@csrf_exempt
@user_token_required
def submit_test_view(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        test_id = data.get("test_id")
        student_id = request.user.id

        if not test_id:
            return JsonResponse({"status": "error", "message": "test_id is required"}, status=400)

        now = timezone.now()

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE exams_teststatus
                SET status = 'completed',
                    completed_at = %s
                WHERE student_id = %s AND test_id = %s
                  AND status = 'ongoing'
                RETURNING id
            """, [now, student_id, test_id])
            updated = cursor.fetchone()

        if updated:
            return JsonResponse({"status": "success", "message": "Test marked as completed", "completed_at": now})
        else:
            return JsonResponse({"status": "error", "message": "Test not found or already completed"}, status=400)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


# def calculate_test_score(request):
