from django.shortcuts import render
import json
from django.http import JsonResponse
from website.utils import api_key_required, has_perms, token_required
from .models import university, location, ranking_agency, Partner_Agency
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import *
from django.db import connection
from django.db import transaction
from scholarship.models import Scholarship
from django.db.models import Avg, Count, Min
from psycopg2.extras import RealDictCursor
from student.utils import create_student_log

@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def get_university_location(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, city, state FROM university_location")
        columns = [col[0] for col in cursor.description]
        locations = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return JsonResponse({"locations": locations}, status=200)


@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["GET"])
def get_university_ranking_agency(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT id, name, description, logo FROM university_ranking_agency")
        columns = [col[0] for col in cursor.description]
        agencies = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return JsonResponse({"Ranking Agencies": agencies}, status=200)


@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["GET"])
def get_university_partner_agency(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM university_partner_agency")
        columns = [col[0] for col in cursor.description]
        agencies = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return JsonResponse({"Partner Agencies": agencies}, status=200)


# just a utility function
def dictfetchall(cursor):
    """Return all rows from a cursor as a list of dicts."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

# Invoked by a Supbase function 'paginated_universities_fn'


@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def paginated_universities(request):
    page = int(request.GET.get("page", 1))
    city_param = request.GET.get("city")
    state_param = request.GET.get("state")

    cities = [c.strip() for c in city_param.split(",")] if city_param else []
    states = [s.strip() for s in state_param.split(",")] if state_param else []

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT * FROM paginated_universities_fn(%s, %s, %s);
            """,
            [page, cities, states]
        )
        results = dictfetchall(cursor)

    return JsonResponse({
        "results": results,
        "page": page,
        "count": len(results)
    })


# Invoked by a supabase Function 'get_university_with_courses'
@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def get_university_by_name(request):
    university_name = request.GET.get("name")

    if not university_name:
        return JsonResponse({"error": "Missing 'name' query parameter"}, status=400)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT get_university_with_courses(%s);",
            [university_name]
        )
        row = cursor.fetchone()

    if not row or not row[0]:
        return JsonResponse({"error": "University not found"}, status=404)
    create_student_log(request, f"Oppened University Page for '{university_name}'")
    return JsonResponse(row[0], safe=False, status=200)


@csrf_exempt
# @api_key_required
@require_http_methods(["GET"])
def destination_page(request):
    # Get country from query parameters
    country_name = request.GET.get("country")

    # Validate country parameter
    if not country_name:
        return JsonResponse({"error": "Country parameter is required"}, status=400)

    # Execute the get_destination_page function using a cursor
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT get_destination_page(%s)", [country_name])
            result = cursor.fetchone()[0]  # Fetch the JSON result

        create_student_log(request, f"Oppened Destination Page for '{country_name}'")
        # Return the JSON response directly
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": f"Database error: {str(e)}"}, status=500)
