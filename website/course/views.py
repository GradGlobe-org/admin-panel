from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from website.utils import api_key_required
from .models import *
from university.models import *
from psycopg2.extras import register_default_jsonb
import json
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from student.utils import create_student_log
from django.views import View
from search.utils import save_unsanitized_query
import threading
from .FilterAi import (
    parser,
    get_chain,
    SearchParams,
    ChatResponseToUser,
    chat_parser,
    chat_chain,
)
from pydantic import ValidationError
from website.utils import user_token_required
from django.utils.decorators import method_decorator


@require_GET
@api_key_required
def search_course(request):
    # Get and validate parameters
    university_name = request.GET.get("university", "").strip()
    course_name = request.GET.get("course", "").strip()
    create_student_log(
        request,
        f"Looked for Course Named '{course_name}' of university '{university_name}'",
    )
    if not university_name or not course_name:
        return JsonResponse(
            {"error": "Both university and course parameters are required"}, status=400
        )

    try:
        with connection.cursor() as cursor:
            # Execute the function call
            cursor.execute(
                "SELECT * FROM search_course(%s, %s)", [university_name, course_name]
            )
            result = cursor.fetchone()

            if not result:
                return JsonResponse({"error": "Course not found"}, status=404)

            # The function returns a single JSON column which becomes the first item in the tuple
            response_data = result[0]

            # If the response already contains an error, return it with appropriate status
            if isinstance(response_data, dict) and "error" in response_data:
                status_code = (
                    404 if response_data["error"] == "Course not found" else 400
                )
                return JsonResponse(response_data, status=status_code)

            # Otherwise return the successful response
            return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({"error": f"Database error: {str(e)}"}, status=500)


# Uses The Supabase Function SELECT * FROM compare_course_search();
@require_GET
@api_key_required
def compare_course_search(request):
    # Get query parameters
    course_name = request.GET.get("course_name", None)
    program_level = request.GET.get("program_level", None)

    # Validate program_level if provided
    valid_program_levels = [choice[0] for choice in Course.PROGRAM_LEVEL_CHOICES]
    if program_level and program_level not in valid_program_levels:
        return JsonResponse(
            {
                "error": f"Invalid program_level. Must be one of: {', '.join(valid_program_levels)}"
            },
            status=400,
        )

    # SQL query to call the course_search function
    query = "SELECT compare_course_search(%s, %s) AS result"
    params = [course_name, program_level]
    create_student_log(request, f"Compared Course '{course_name}'")
    # Execute the query
    with connection.cursor() as cursor:
        register_default_jsonb(connection.connection, loads=json.loads, globally=False)
        cursor.execute(query, params)
        result = cursor.fetchone()[0]  # Fetch the JSONB result

    # Return the result directly as JSON
    return JsonResponse(result, safe=False)


def safe_parse(parser, text):
    try:
        return parser.parse(text)
    except ValidationError as e:
        # Create dict with None for invalid fields
        raw = e.body if hasattr(e, "body") else {}
        safe_data = {}
        for field in SearchParams.model_fields.keys():
            try:
                safe_data[field] = SearchParams.model_validate(
                    {field: raw.get(field)}
                ).dict()[field]
            except Exception:
                safe_data[field] = None
        return SearchParams(**safe_data)
    except Exception:
        # fallback: everything None
        return SearchParams()


# @method_decorator(api_key_required, name="dispatch")
class FilterSearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("search_query", "").strip()
        if not query:
            return JsonResponse({"error": "Missing query"}, status=400)
        if len(query) < 3:
            return JsonResponse(
                {"status": "error", "message": "Query must be at least 3 characters"},
                status=400,
            )

        threading.Thread(
            target=save_unsanitized_query, args=(query,), daemon=True
        ).start()
        threading.Thread(
            target=create_student_log,
            args=(request, f"Smart Searched '{query}'"),
            daemon=True,
        ).start()

        try:
            params: SearchParams = get_chain().invoke(
                {
                    "query": query,
                    "format_instructions": parser.get_format_instructions(),
                }
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * from public.filter_search_advance(
                        %s,%s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s
                    )
                """,
                    [
                        None,
                        params.university_name,
                        params.program_name,
                        params.program_level,
                        params.country_name,
                        params.duration_min,
                        params.duration_max,
                        params.tuition_fees_min,
                        params.tuition_fees_max,
                        params.gpa_min,
                        params.gpa_max,
                        params.sat_min,
                        params.sat_max,
                        params.act_min,
                        params.act_max,
                        params.ielts_min,
                        params.ielts_max,
                        10,
                        params.offset_val,
                    ],
                )
                result = cursor.fetchone()[0]

            return JsonResponse({"courses": result}, status=200, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(user_token_required, name="get")
class UserFilterSearchView(View):
    def get(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return JsonResponse({"error": "Missing Authorization header"}, status=401)

        logs_text = ""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT * FROM recent_logs(%s);", [auth_header])
                rows = cursor.fetchall()
                if rows:
                    logs_text = "\n".join(r[0] for r in rows)
        except Exception as e:
            print("Error fetching logs:", str(e))

        print(logs_text)

        try:
            # Parse the search params from your chain
            params: SearchParams = get_chain().invoke(
                {
                    "query": logs_text,
                    "format_instructions": parser.get_format_instructions(),
                }
            )
            print(params)

            # Helper function to run query
            def run_query(p: SearchParams):
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * from public.filter_search_advance(
                            %s,%s,%s,%s,%s,
                            %s,%s,%s,%s,
                            %s,%s,%s,%s,
                            %s,%s,%s,%s,
                            %s,%s
                        )
                        """,
                        [
                            None,
                            p.university_name,
                            p.program_name,
                            p.program_level,
                            p.country_name,
                            p.duration_min,
                            p.duration_max,
                            p.tuition_fees_min,
                            p.tuition_fees_max,
                            p.gpa_min,
                            p.gpa_max,
                            p.sat_min,
                            p.sat_max,
                            p.act_min,
                            p.act_max,
                            p.ielts_min,
                            p.ielts_max,
                            10,
                            p.offset_val,
                        ],
                    )
                    return cursor.fetchone()[0]

            # First try: full search
            result = run_query(params)

            # Fallback mode if first search is empty
            fallback_fields = [
                "university_name",
                "program_level",
                "country_name",
                "program_name",
            ]
            if not result.get("courses"):
                # Start with all fallback filters
                fallback_params = SearchParams(
                    university_name=params.university_name,
                    program_name=params.program_name,
                    program_level=params.program_level,
                    country_name=params.country_name,
                    duration_min=None,
                    duration_max=None,
                    tuition_fees_min=None,
                    tuition_fees_max=None,
                    gpa_min=None,
                    gpa_max=None,
                    sat_min=None,
                    sat_max=None,
                    act_min=None,
                    act_max=None,
                    ielts_min=None,
                    ielts_max=None,
                    limit_val=params.limit_val,
                    offset_val=params.offset_val,
                )

                # Gradually remove fallback fields one by one if results are empty
                for i in range(len(fallback_fields) + 1):
                    current_params = fallback_params.copy()
                    # Remove the first 'i' filters
                    for field in fallback_fields[:i]:
                        setattr(current_params, field, None)

                    print(f"Fallback search removing: {fallback_fields[:i]}")
                    result = run_query(current_params)

                    if result.get("courses"):
                        break  # stop when we find results

            return JsonResponse({"courses": result}, status=200, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class FilterSuggest(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("search_query", "").strip()
        if not query:
            return JsonResponse({"error": "Missing query"}, status=400)
        if len(query) < 3:
            return JsonResponse(
                {"status": "error", "message": "Query must be at least 3 characters"},
                status=400,
            )
        threading.Thread(
            target=create_student_log,
            args=(request, f"Smart Suggested with '{query}'"),
            daemon=True,
        ).start()

        try:
            params: SearchParams = get_chain().invoke(
                {
                    "query": query,
                    "format_instructions": parser.get_format_instructions(),
                }
            )

            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * from public.filter_search_advance(
                        %s,%s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s,%s,%s,
                        %s,%s
                    )
                """,
                    [
                        None,
                        params.university_name,
                        params.program_name,
                        params.program_level,
                        params.country_name,
                        params.duration_min,
                        params.duration_max,
                        params.tuition_fees_min,
                        params.tuition_fees_max,
                        params.gpa_min,
                        params.gpa_max,
                        params.sat_min,
                        params.sat_max,
                        params.act_min,
                        params.act_max,
                        params.ielts_min,
                        params.ielts_max,
                        params.limit_val,
                        params.offset_val,
                    ],
                )
                result = cursor.fetchone()[0]

            return JsonResponse({"courses": result}, status=200, safe=False)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")
class ChatSuggest(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        query = data.get("search_query", "").strip()

        if not query:
            return JsonResponse({"error": "Missing query"}, status=400)
        if len(query) < 2:
            return JsonResponse(
                {"status": "error", "message": "Query must be at least 3 characters"},
                status=400,
            )

        try:
            chat_parser: ChatResponseToUser = chat_chain().invoke(
                {
                    "query": query,
                    "format_instructions": parser.get_format_instructions(),
                }
            )
            if chat_parser.should_suggest:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT * from public.filter_search_advance(
                            %s,%s,%s,%s,%s,
                            %s,%s,%s,%s,
                            %s,%s,%s,%s,
                            %s,%s,%s,%s,
                            %s,%s
                        )
                    """,
                        [
                            None,
                            chat_parser.university_name,
                            chat_parser.program_name,
                            chat_parser.program_level,
                            chat_parser.country_name,
                            chat_parser.duration_min,
                            chat_parser.duration_max,
                            chat_parser.tuition_fees_min,
                            chat_parser.tuition_fees_max,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            None,
                            5,
                            0,
                        ],
                    )
                    result = cursor.fetchone()[0]
            else:
                result = ""
            return JsonResponse(
                {"response": str(chat_parser.response_text), "courses": result},
                status=200,
                safe=False,
            )

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# @csrf_exempt
# @require_http_methods(["GET"])
# # @api_key_required
# def filter_search(request):
#     # Get the search query from GET parameters
#     search_query = request.GET.get("search_query", "").strip()
#
#     # Require at least 3 characters
#     if len(search_query) < 3:
#         return JsonResponse(
#             {"error": "Search query must be at least 3 characters long."}, status=400
#         )
#     create_student_log(request, f"Smart Searched '{search_query}'")
#     # Use a cursor to call the Supabase function
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT public.filter_search(%s)", [search_query])
#         result = cursor.fetchone()[0]  # Fetch the JSON result
#
#     return JsonResponse({"courses": result}, status=200)
