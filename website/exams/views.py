from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
import json
from website.utils import token_required, user_token_required
from django.db import connection, transaction
from django.utils import timezone

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
    

# @csrf_exempt
# @user_token_required
# def get_test_details_view(request):
#     if request.method != "POST":
#         return JsonResponse({"status": "error", "message": "Invalid request method"}, status=405)

#     try:
#         data = json.loads(request.body)
#     except json.JSONDecodeError:
#         return JsonResponse({"status": "error", "message": "Invalid JSON payload"}, status=400)

#     test_id = data.get("test_id")
#     if not test_id:
#         return JsonResponse({"status": "error", "message": "test_id is required"}, status=400)

#     student_id = request.user.id

#     try:
#         with connection.cursor() as cursor:
#             cursor.execute(
#                 "SELECT get_test_details_for_student(%s, %s)",
#                 [student_id, test_id]
#             )
#             result = cursor.fetchone()[0]

#         return JsonResponse(result, status=200 if result.get('status') == 'success' else 403)

#     except Exception as e:
#         return JsonResponse({"status": "error", "message": str(e)}, status=400)
    

# @csrf_exempt
# @user_token_required
# def start_or_get_test_view(request):
#     """
#     Calls the Postgres function to start the test if not started and fetch full test details.
#     """
#     if request.method != "POST":
#         return JsonResponse({"status":"error","message":"Invalid request method"}, status=405)

#     try:
#         data = json.loads(request.body)
#         test_id = data.get("test_id")
#         if not test_id:
#             return JsonResponse({"status":"error","message":"test_id is required"}, status=400)

#         student_id = request.user.id

#         with connection.cursor() as cursor:
#             cursor.execute(
#                 "SELECT start_and_get_test_for_student(%s, %s)",
#                 [student_id, test_id]
#             )
#             result = cursor.fetchone()[0]

#         status_code = 200 if result.get('status') == 'success' else 403
#         return JsonResponse(result, status=status_code)

#     except Exception as e:
#         return JsonResponse({"status":"error","message": str(e)}, status=400)