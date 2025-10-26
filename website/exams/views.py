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
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)

    test_id = data.get("test_id")
    if not test_id:
        return JsonResponse({"status": "error", "message": "test_id is required"}, status=400)

    student_id = request.user.id  # assumes request.user is Student

    from exams.models import Test, TestStatus
    from .models import CourseLinkedStudent, CourseTest
    from django.utils import timezone
    from datetime import timedelta

    # ✅ Step 1: Check if student already has a TestStatus
    existing_status = TestStatus.objects.filter(student_id=student_id, test_id=test_id).first()

    # ✅ Step 2: If not assigned, verify if test belongs to a course that the student is enrolled in
    if not existing_status:
        is_linked = CourseLinkedStudent.objects.filter(
            student_id=student_id,
            course__tests__id=test_id
        ).exists()

        if not is_linked:
            return JsonResponse(
                {"status": "error", "eligible": False, "message": "Student not enrolled in a course containing this test"},
                status=403
            )

        # ✅ Step 3: Create a TestStatus record dynamically
        deadline = timezone.now() + timedelta(days=1)  # you can adjust duration logic as needed
        existing_status = TestStatus.objects.create(
            student_id=student_id,
            test_id=test_id,
            status="pending",
            deadline=deadline
        )

    # ✅ Step 4: Call your existing SQL function to start/resume the test
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT start_or_resume_test(%s, %s)", [student_id, test_id])
            result = cursor.fetchone()[0]

        if isinstance(result, str):
            result = json.loads(result)

        http_status = 200 if result.get("eligible") else 403
        return JsonResponse(result, status=http_status)

    except Exception as e:
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


import json
import re
import ast
import logging
import traceback

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils import timezone

from .models import TestStatus, Answer, Evaluation, Test
from exams.models import TestStatus, Answer, Evaluation
from website.utils import user_token_required
from .utils import get_subjective_eval_chain, subjective_eval_parser

logger = logging.getLogger(__name__)

def safe_jsonify_llm_output(raw_output):
    """
    Convert loosely formatted LLM output into valid JSON or Python list/dict.
    Handles:
      - LangChain reprs like "root=[SubjectiveEvaluation(qs_id=32, marks=10.0), ...]"
      - Python reprs with single quotes
      - JSON strings embedded in strings
    Returns a Python list/dict.
    """
    if raw_output is None:
        return []

    # If already parsed
    if isinstance(raw_output, (list, dict)):
        return raw_output

    # Unwrap `.root` if present
    if hasattr(raw_output, "root"):
        raw_output = getattr(raw_output, "root")

    text = str(raw_output).strip()

    # Handle "root=[SubjectiveEvaluation(...)]"
    if "SubjectiveEvaluation(" in text:
        # Extract each SubjectiveEvaluation(...) block
        pattern = r"SubjectiveEvaluation\(qs_id=(\d+),\s*marks=([\d.]+)\)"
        matches = re.findall(pattern, text)
        if matches:
            data = [{"qs_id": int(qs_id), "marks": float(marks)} for qs_id, marks in matches]
            return data

    # Handle "root=[{...}]" or plain JSON
    root_match = re.search(r"root\s*=\s*(\[.*\])", text, flags=re.S)
    if root_match:
        text = root_match.group(1)

    # Try JSON parsing directly
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try Python literal (handles single quotes, tuples)
    try:
        return ast.literal_eval(text)
    except Exception:
        pass

    # Try with single→double quote replacement
    try:
        fixed = re.sub(r"'", '"', text)
        return json.loads(fixed)
    except Exception:
        return []


from django.utils import timezone

def build_test_report(test_status, evaluation):
    """
    Build structured report of evaluated test with per-question marks,
    properly handling multiple selected options and negative marking.
    """
    answers = (
        Answer.objects.filter(test_status=test_status)
        .select_related("question", "question__section")
        .prefetch_related("selected_options", "question__options")
    )

    report = {
        "status": "success",
        "test_id": test_status.test.id,
        "test_title": test_status.test.title,
        "attempt_time": (
            test_status.completed_at.strftime("%Y-%m-%d %H:%M:%S")
            if test_status.completed_at
            else None
        ),
        "total_marks": evaluation.total_marks,
        "obtained_marks": evaluation.obtained_marks,
        "sections": [],
    }

    sections = {}
    for ans in answers:
        section = ans.question.section
        section_name = section.title

        if section_name not in sections:
            sections[section_name] = {
                "section": section_name,
                "question_mode": section.question_mode,
                "questions": []
            }

        q_data = {
            "qs_no": ans.question.id,
            "qs": ans.question.question,
            "full_marks": ans.question.marks,
        }

        if section.question_mode == "MCQ":
            # Prepare selected and correct options
            selected_ids = set(ans.selected_options.values_list("id", flat=True))
            options = []
            correct_count = 0
            selected_correct_count = 0
            total_selected = len(selected_ids)

            for opt in ans.question.options.all():
                is_correct = opt.is_correct
                is_selected = opt.id in selected_ids
                options.append({
                    "option": opt.option_name,
                    "is_correct": is_correct,
                    "is_selected": is_selected
                })
                if is_correct:
                    correct_count += 1
                    if is_selected:
                        selected_correct_count += 1

            # Calculate marks including negative marking
            marks_obtained = 0.0
            if total_selected > 0 and correct_count > 0:
                # Positive marks proportion
                marks_obtained = ans.question.marks * (selected_correct_count / correct_count)
                # Negative marks for wrong options
                wrong_selected = total_selected - selected_correct_count
                if wrong_selected > 0 and section.negative_marking_factor > 0:
                    negative = wrong_selected * section.negative_marking_factor
                    marks_obtained -= negative
                    if marks_obtained < 0:
                        marks_obtained = 0.0
            q_data["obtained_marks"] = marks_obtained
            q_data["options"] = options

        else:  # Subjective
            q_data.update({
                "obtained_marks": ans.marks_obtained or 0.0,
                "answer": ans.subjective_answer or "",
                "remarks": ans.remarks or "",
            })

        sections[section_name]["questions"].append(q_data)

    report["sections"] = list(sections.values())
    return report


def build_section_marks_summary(test_status, evaluation=None):
    answers = (
        Answer.objects.filter(test_status=test_status)
        .select_related("question", "question__section")
    )

    section_summary = {}
    total_marks = 0.0
    obtained_marks = 0.0

    for ans in answers:
        section = ans.question.section
        section_name = section.title

        if section_name not in section_summary:
            section_summary[section_name] = {
                "section": section_name,
                "question_mode": section.question_mode,
                "total_marks": 0.0,
                "obtained_marks": 0.0,
            }

        section_summary[section_name]["total_marks"] += ans.question.marks or 0.0
        section_summary[section_name]["obtained_marks"] += ans.marks_obtained or 0.0
        total_marks += ans.question.marks or 0.0
        obtained_marks += ans.marks_obtained or 0.0

    return {
        "status": "success",
        "test_id": test_status.test.id,
        "test_title": test_status.test.title,
        "total_marks": evaluation.total_marks if evaluation else total_marks,
        "obtained_marks": evaluation.obtained_marks if evaluation else obtained_marks,
        "sections": list(section_summary.values()),
    }


@csrf_exempt
@user_token_required
@transaction.atomic
def evaluate_subjective_answers(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

    # Step 1: Parse request
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)

    test_id = payload.get("test_id")
    student_id = getattr(request.user, "id", None)

    if not test_id or not student_id:
        return JsonResponse({"status": "error", "message": "Missing required parameters"}, status=400)

    # Step 2: Fetch test & test status
    try:
        test = Test.objects.get(id=test_id)
    except Test.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Test not found"}, status=404)

    try:
        test_status = TestStatus.objects.get(student_id=student_id, test=test)
    except TestStatus.DoesNotExist:
        return JsonResponse({"status": "error", "message": "No test assigned to this student"}, status=404)

    if str(test_status.status).lower() != "completed":
        return JsonResponse(
            {"status": "error", "message": f"Test not completed (status={test_status.status})"},
            status=400,
        )

    # Step 3: Check if already evaluated
    evaluation = Evaluation.objects.filter(test_status=test_status).first()
    if evaluation and not evaluation.is_error_evaluating:
        # Already evaluated → build report & return immediately
        return JsonResponse(build_section_marks_summary(test_status, evaluation), status=200)

    # Step 4: Evaluate MCQs
    mcq_answers = Answer.objects.filter(
        test_status=test_status,
        question__section__question_mode="MCQ"
    ).select_related("question", "question__section").prefetch_related("selected_options", "selected_options__question")

    for ans in mcq_answers:
        try:
            ans.evaluate()
            if ans.marks_obtained is None or ans.marks_obtained < 0:
                ans.marks_obtained = 0
            if ans.marks_obtained > ans.question.marks:
                ans.marks_obtained = ans.question.marks
            ans.save(update_fields=["marks_obtained"])
        except Exception:
            logger.exception("Error evaluating MCQ id=%s for test_status id=%s", ans.id, test_status.id)
            return JsonResponse({"status": "error", "message": "MCQ evaluation failed"}, status=500)

    # Step 5: Subjective evaluation
    subjective_answers_qs = Answer.objects.filter(
        test_status=test_status,
        question__section__question_mode="SUB"
    ).select_related("question")

    if subjective_answers_qs.exists():
        data_for_ai = [
            {
                "qs_id": ans.id,
                "qs": ans.question.question,
                "qs_answer": ans.subjective_answer or "",
                "qs_max_marks": ans.question.marks,
            }
            for ans in subjective_answers_qs
        ]

        try:
            chain = get_subjective_eval_chain()
            format_instructions = subjective_eval_parser.get_format_instructions()
            raw_ai_output = chain.invoke({
                "subjective_data_json": json.dumps(data_for_ai),
                "format_instructions": format_instructions
            })
            evaluations_output = safe_jsonify_llm_output(raw_ai_output)
        except Exception:
            logger.exception("LLM subjective eval failed")
            evaluation, _ = Evaluation.objects.get_or_create(test_status=test_status)
            evaluation.is_error_evaluating = True
            evaluation.save(update_fields=["is_error_evaluating"])
            return JsonResponse({"status": "error", "message": "Subjective evaluation failed"}, status=500)

        # Map marks
        marks_map = {}
        for item in evaluations_output:
            try:
                qs_id = int(item.get("qs_id") or item.get("id"))
                marks = float(item.get("marks") or item.get("score"))
                marks_map[qs_id] = marks
            except Exception:
                logger.warning("Invalid item in eval output: %s", item)

        # Apply marks
        for ans in subjective_answers_qs:
            val = marks_map.get(ans.id, 0.0)
            if val < 0:
                val = 0
            if val > ans.question.marks:
                val = ans.question.marks
            ans.marks_obtained = val
            ans.save(update_fields=["marks_obtained"])

    # Step 6: Finalize totals
    total_marks = 0
    obtained_marks = 0
    for ans in Answer.objects.filter(test_status=test_status).select_related("question"):
        total_marks += ans.question.marks
        obtained_marks += ans.marks_obtained or 0

    evaluation, _ = Evaluation.objects.get_or_create(test_status=test_status)
    evaluation.total_marks = total_marks
    evaluation.obtained_marks = obtained_marks
    evaluation.is_error_evaluating = False
    evaluation.save()

    # Step 7: Return structured report
    return JsonResponse(build_section_marks_summary(test_status, evaluation), status=200)