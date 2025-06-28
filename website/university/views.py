from django.shortcuts import render
import json
from django.http import JsonResponse
from website.utils import api_key_required, has_perms, token_required
from .models import university, location, ranking_agency, Partner_Agency
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import location
from django.db import connection
# Create your views here.

@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["POST"])
def add_university(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)

    required_fields = [
        'cover_url', 'cover_origin', 'name', 'type',
        'establish_year', 'location_id', 'about',
        'admission_requirements', 'location_map_link', 'status'
    ]

    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return JsonResponse({
            'status': 'error',
            'message': 'Missing required fields',
            'missingFields': missing_fields
        }, status=400)

    employee = request.user

    # Permission check
    if not has_perms(employee.id, ["add_university"]):
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to perform this task'
        }, status=403)

    # Fetch location object
    try:
        location_obj = location.objects.get(id=data['location_id'])
    except location.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid location_id'
        }, status=400)

    # Create university object
    try:
        university_obj = university.objects.create(
            cover_url=data['cover_url'],
            cover_origin=data['cover_origin'],
            name=data['name'],
            type=data['type'],
            establish_year=data['establish_year'],
            location=location_obj,
            about=data['about'],
            admission_requirements=data['admission_requirements'],
            location_map_link=data['location_map_link'],
            status=data['status']
        )
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Error while creating university',
            'error': str(e)
        }, status=500)

    return JsonResponse({
        'status': 'success',
        'message': f'University "{university_obj.name}" created successfully by {employee.name}',
        'universityId': university_obj.id,
        'authorName': employee.name
    }, status=201)



@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def get_university_location(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, city, state FROM university_location")
        columns = [col[0] for col in cursor.description]
        locations = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return JsonResponse({"locations": locations}, status=200)

@token_required
@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def get_university_ranking_agency(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, description, logo FROM university_ranking_agency")
        columns = [col[0] for col in cursor.description]
        agencies = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return JsonResponse({"Ranking Agencies": agencies}, status=200)

@token_required
@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def get_university_partner_agency(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM university_partner_agency")
        columns = [col[0] for col in cursor.description]
        agencies = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return JsonResponse({"Partner Agencies": agencies}, status=200)


@token_required
@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def paginated_universities(request):
    page = int(request.GET.get("page", 1))
    limit = 25
    offset = (page - 1) * limit

    filters = ["u.status = 'PUBLISH'"]
    params = {"limit": limit, "offset": offset}

    
    city_param = request.GET.get("city")
    state_param = request.GET.get("state")

    if city_param:
        cities = [c.strip() for c in city_param.split(",") if c.strip()]
        city_placeholders = ", ".join([f"%({f'city_{i}'})s" for i in range(len(cities))])
        filters.append(f"l.city ILIKE ANY (ARRAY[{city_placeholders}])")
        for i, city in enumerate(cities):
            params[f"city_{i}"] = f"%{city}%"

    if state_param:
        states = [s.strip() for s in state_param.split(",") if s.strip()]
        state_placeholders = ", ".join([f"%({f'state_{i}'})s" for i in range(len(states))])
        filters.append(f"l.state ILIKE ANY (ARRAY[{state_placeholders}])")
        for i, state in enumerate(states):
            params[f"state_{i}"] = f"%{state}%"

    where_clause = " AND ".join(filters)

    query = f"""
    SELECT u.id, u.cover_url, u.cover_origin, u.name, u.establish_year, 
           l.city || ', ' || l.state AS location,
           SUBSTR(u.about, 1, 1000) AS about
    FROM university_university u
    JOIN university_location l ON u.location_id = l.id
    LEFT JOIN (
        SELECT university_id,
               MAX(COALESCE("inPercentage", 0)) AS perc,
               MAX(COALESCE("inAmount", 0)) AS amt
        FROM university_commission
        GROUP BY university_id
    ) c ON c.university_id = u.id
    WHERE {where_clause}
    ORDER BY 
        CASE WHEN c.perc IS NOT NULL THEN c.perc ELSE -1 END DESC,
        CASE WHEN c.perc IS NULL AND c.amt IS NOT NULL THEN c.amt ELSE -1 END DESC
    LIMIT %(limit)s OFFSET %(offset)s;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    data = [
        {
            "cover_url": row[1],
            "cover_origin": row[2],
            "name": row[3],
            "establish_year": row[4],
            "location": row[5],
            "about": row[6],
        }
        for row in rows
    ]

    return JsonResponse({
        "results": data,
        "page": page,
        "count": len(data)
    })

@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["GET"])
def paginated_universities_employee(request):
    employee_id = request.user.id
    if not has_perms(employee_id, ["university_view"]):
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to perform this task'
        }, status=403)


    page = int(request.GET.get("page", 1))
    limit = 25
    offset = (page - 1) * limit

    filters = []  # No status filter this time
    params = {"limit": limit, "offset": offset}

    # Multiple city filter
    city_param = request.GET.get("city")
    state_param = request.GET.get("state")

    if city_param:
        cities = [c.strip() for c in city_param.split(",") if c.strip()]
        city_placeholders = ", ".join([f"%({f'city_{i}'})s" for i in range(len(cities))])
        filters.append(f"l.city ILIKE ANY (ARRAY[{city_placeholders}])")
        for i, city in enumerate(cities):
            params[f"city_{i}"] = f"%{city}%"

    if state_param:
        states = [s.strip() for s in state_param.split(",") if s.strip()]
        state_placeholders = ", ".join([f"%({f'state_{i}'})s" for i in range(len(states))])
        filters.append(f"l.state ILIKE ANY (ARRAY[{state_placeholders}])")
        for i, state in enumerate(states):
            params[f"state_{i}"] = f"%{state}%"

    where_clause = " AND ".join(filters) if filters else "TRUE"

    query = f"""
    SELECT u.id, u.cover_url, u.cover_origin, u.name, u.establish_year, 
           l.city || ', ' || l.state AS location,
           SUBSTR(u.about, 1, 1000) AS about,
           u.status
    FROM university_university u
    JOIN university_location l ON u.location_id = l.id
    LEFT JOIN (
        SELECT university_id,
               MAX(COALESCE("inPercentage", 0)) AS perc,
               MAX(COALESCE("inAmount", 0)) AS amt
        FROM university_commission
        GROUP BY university_id
    ) c ON c.university_id = u.id
    WHERE {where_clause}
    ORDER BY 
        CASE WHEN c.perc IS NOT NULL THEN c.perc ELSE -1 END DESC,
        CASE WHEN c.perc IS NULL AND c.amt IS NOT NULL THEN c.amt ELSE -1 END DESC
    LIMIT %(limit)s OFFSET %(offset)s;
    """

    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()

    data = [
        {
            "cover_url": row[1],
            "cover_origin": row[2],
            "name": row[3],
            "establish_year": row[4],
            "location": row[5],
            "about": row[6],
            "status": row[7],
        }
        for row in rows
    ]

    return JsonResponse({
        "results": data,
        "page": page,
        "count": len(data)
    })