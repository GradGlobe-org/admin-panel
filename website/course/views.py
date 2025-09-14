from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from website.utils import api_key_required
from .models import *
from university.models import *
from psycopg2.extras import register_default_jsonb
import json
import os
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from student.utils import create_student_log
from django.views import View

# Uses The Supabase Function SELECT * FROM search_course('New York University', 'Applied Physics');


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


from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel
from typing import Optional, Annotated
from enum import Enum
from pydantic import Field

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")


class ProgramLevel(str, Enum):
    bachelors = "bachelors"
    masters = "masters"


class Country(str, Enum):
    Australia = "Australia"
    Austria = "Austria"
    Belgium = "Belgium"
    Brazil = "Brazil"
    Canada = "Canada"
    Denmark = "Denmark"
    Estonia = "Estonia"
    Finland = "Finland"
    France = "France"
    Georgia = "Georgia"
    Germany = "Germany"
    Hungary = "Hungary"
    Iceland = "Iceland"
    India = "India"
    Indonesia = "Indonesia"
    Ireland = "Ireland"
    Italy = "Italy"
    Japan = "Japan"
    Lithuania = "Lithuania"
    Malta = "Malta"
    Mexico = "Mexico"
    Netherlands = "Netherlands"
    Poland = "Poland"
    Portugal = "Portugal"
    Russia = "Russia"
    Singapore = "Singapore"
    SouthKorea = "South Korea"
    Spain = "Spain"
    Sweden = "Sweden"
    Switzerland = "Switzerland"
    Ukraine = "Ukraine"
    UAE = "United Arab Emirates"
    UK = "United Kingdom"
    USA = "United States"


class SearchParams(BaseModel):
    university_name: Optional[str] = Field(None, description="Name of the university")
    program_name: Optional[str] = Field(None, description="Name of the program/course")

    # Make program_level mandatory, allow only ProgramLevel Enum
    program_level: Annotated[
        Optional[ProgramLevel],
        Field(description="Program level, e.g., bachelors, masters"),
    ] = None

    # Country restricted to Country Enum
    country_name: Annotated[
        Optional[Country], Field(description="Country name from allowed list")
    ] = None

    duration_min: Annotated[
        Optional[int], Field(ge=0, description="Minimum duration in years")
    ] = None
    duration_max: Annotated[
        Optional[int], Field(ge=0, description="Maximum duration in years")
    ] = None

    tuition_fees_min: Annotated[
        Optional[int], Field(ge=0, description="Minimum tuition fees in USD")
    ] = None
    tuition_fees_max: Annotated[
        Optional[int], Field(ge=0, description="Maximum tuition fees")
    ] = None

    gpa_min: Annotated[
        Optional[float], Field(ge=0.0, le=4.0, description="Minimum GPA")
    ] = None
    gpa_max: Annotated[
        Optional[float], Field(ge=0.0, le=4.0, description="Maximum GPA")
    ] = None

    sat_min: Annotated[
        Optional[float], Field(ge=400, le=1600, description="Minimum SAT score")
    ] = None
    sat_max: Annotated[
        Optional[float], Field(ge=400, le=1600, description="Maximum SAT score")
    ] = None

    act_min: Annotated[
        Optional[float], Field(ge=1, le=36, description="Minimum ACT score")
    ] = None
    act_max: Annotated[
        Optional[float], Field(ge=1, le=36, description="Maximum ACT score")
    ] = None

    ielts_min: Annotated[
        Optional[float], Field(ge=0.0, le=9.0, description="Minimum IELTS score")
    ] = None
    ielts_max: Annotated[
        Optional[float], Field(ge=0.0, le=9.0, description="Maximum IELTS score")
    ] = None

    limit_val: Annotated[
        int, Field(gt=0, le=200, description="Pagination limit, max 200")
    ] = 20
    offset_val: Annotated[int, Field(ge=0, description="Pagination offset")] = 0

    class Config:
        use_enum_values = True


llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=GOOGLE_API_KEY)
parser = PydanticOutputParser(pydantic_object=SearchParams)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a mentor and your task is to suggest university/course to students going abroad"
            + "You have to play safe and only recommend things that is asked"
            + "Be very carefull about what to fill"
            + "example: 'I want to study in us.' you cannot fill the name of a uni or course"
            + "You also can't leave every field totally None"
            + "You have to complete the query with details",
        ),
        (
            "human",
            "{query}\n\n. Return only JSON in this format:\n{format_instructions}",
        ),
    ]
)

chain = prompt | llm | parser


# @method_decorator(api_key_required, name="dispatch")
class FilterSearchView(View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get("search_query", "").strip()
        if not query:
            return JsonResponse({"error": "Missing query"}, status=400)

        print(f"[DEBUG] Incoming query: {query}")

        try:
            # Step 1: Use Gemini to parse query → structured params
            params: SearchParams = chain.invoke(
                {
                    "query": query,
                    "format_instructions": parser.get_format_instructions(),
                }
            )

            print("[DEBUG] Extracted Params:", params.dict())

            # Step 2: Call Postgres function
            with connection.cursor() as cursor:
                print("[DEBUG] Executing filter_search_advance with args:")
                print(params.dict())

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

            # print("[DEBUG] Raw DB Result:", result)

            # Step 3: Send raw DB JSON back
            return JsonResponse({"courses": result}, status=200, safe=False)

        except Exception as e:
            print("[ERROR] Exception occurred:", str(e))
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
# @api_key_required
def filter_search(request):
    # Get the search query from GET parameters
    search_query = request.GET.get("search_query", "").strip()

    # Require at least 3 characters
    if len(search_query) < 3:
        return JsonResponse(
            {"error": "Search query must be at least 3 characters long."}, status=400
        )
    create_student_log(request, f"Smart Searched '{search_query}'")
    # Use a cursor to call the Supabase function
    with connection.cursor() as cursor:
        cursor.execute("SELECT public.filter_search(%s)", [search_query])
        result = cursor.fetchone()[0]  # Fetch the JSON result

    return JsonResponse({"courses": result}, status=200)
