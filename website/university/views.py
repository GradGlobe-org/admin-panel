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

    if not has_perms(employee.id, ["university_create"]):
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to perform this task'
        }, status=403)

    try:
        location_obj = location.objects.get(id=data['location_id'])
    except location.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid location_id'
        }, status=400)

    try:
        with transaction.atomic():
            # Create university
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

            # Rankings
            for ranking in data.get('rankings', []):
                if isinstance(ranking, list) and len(ranking) == 2:
                    ranking_agency.objects.get(id=ranking[0])  # Ensure FK exists
                    university_ranking.objects.create(
                        university=university_obj,
                        ranking_agency_id=ranking[0],
                        rank=ranking[1]
                    )

            # FAQs
            for faq in data.get('faqs', []):
                if isinstance(faq, list) and len(faq) == 2:
                    faqs.objects.create(
                        university=university_obj,
                        question=faq[0],
                        answer=faq[1]
                    )

            # Stats
            for stat in data.get('stats', []):
                if isinstance(stat, list) and len(stat) >= 2:
                    stats.objects.create(
                        university=university_obj,
                        name=stat[0],
                        value=stat[1]
                    )

            # Videos
            for video_url in data.get('video', []):
                videos_links.objects.create(
                    university=university_obj,
                    url=video_url
                )

            # Contacts
            for contact in data.get('contacts', []):
                if isinstance(contact, list) and len(contact) == 4:
                    Uni_contact.objects.create(
                        university=university_obj,
                        name=contact[0],
                        email=contact[1],
                        phone=contact[2],
                        designation=contact[3]
                    )

    except ranking_agency.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid ranking_agency_id in rankings'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Error while creating university or related data',
            'error': str(e)
        }, status=500)

    return JsonResponse({
        'status': 'success',
        'message': f'University \"{university_obj.name}\" created successfully by {employee.name}',
        'universityId': university_obj.id,
        'authorName': employee.name
    }, status=201)


@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["PUT"])
def edit_university(request, university_id):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    employee = request.user
    if not has_perms(employee.id, ["university_update"]):
        return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)

    try:
        university_obj = university.objects.get(id=university_id)
    except university.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'University not found'}, status=404)

    try:
        with transaction.atomic():
            # Update required and optional university fields
            updatable_fields = [
                'cover_url', 'cover_origin', 'name', 'type',
                'establish_year', 'about', 'admission_requirements',
                'location_map_link', 'status'
            ]

            for field in updatable_fields:
                if field in data:
                    setattr(university_obj, field, data[field])

            # Update location if provided
            if 'location_id' in data:
                try:
                    location_obj = location.objects.get(id=data['location_id'])
                    university_obj.location = location_obj
                except location.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Invalid location_id'}, status=400)

            university_obj.save()

            # ----- Optional field replacements -----

            # Rankings
            if 'rankings' in data:
                university_ranking.objects.filter(university=university_obj).delete()
                for ranking in data['rankings']:
                    if isinstance(ranking, list) and len(ranking) == 2:
                        ranking_agency.objects.get(id=ranking[0])  # ensure valid FK
                        university_ranking.objects.create(
                            university=university_obj,
                            ranking_agency_id=ranking[0],
                            rank=ranking[1]
                        )

            # FAQs
            if 'faqs' in data:
                faqs.objects.filter(university=university_obj).delete()
                for faq in data['faqs']:
                    if isinstance(faq, list) and len(faq) == 2:
                        faqs.objects.create(
                            university=university_obj,
                            question=faq[0],
                            answer=faq[1]
                        )

            # Stats
            if 'stats' in data:
                stats.objects.filter(university=university_obj).delete()
                for stat in data['stats']:
                    if isinstance(stat, list) and len(stat) >= 2:
                        stats.objects.create(
                            university=university_obj,
                            name=stat[0],
                            value=stat[1]
                        )

            # Videos
            if 'video' in data:
                videos_links.objects.filter(university=university_obj).delete()
                for video_url in data['video']:
                    videos_links.objects.create(
                        university=university_obj,
                        url=video_url
                    )

            # Contacts
            if 'contacts' in data:
                Uni_contact.objects.filter(university=university_obj).delete()
                for contact in data['contacts']:
                    if isinstance(contact, list) and len(contact) == 4:
                        Uni_contact.objects.create(
                            university=university_obj,
                            name=contact[0],
                            email=contact[1],
                            phone=contact[2],
                            designation=contact[3]
                        )

    except ranking_agency.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid ranking_agency_id in rankings'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Error while updating university',
            'error': str(e)
        }, status=500)

    return JsonResponse({
        'status': 'success',
        'message': f'University "{university_obj.name}" updated successfully by {employee.name}',
        'universityId': university_obj.id
    }, status=200)



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
        cursor.execute("SELECT id, name, description, logo FROM university_ranking_agency")
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
            "id": row[0],
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
            "id": row[0],
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


@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["GET"])
def universities_employee(request):
    employee_id = request.user.id
    if not has_perms(employee_id, ["university_view"]):
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to perform this task'
        }, status=403)

    query = """
    SELECT 
        u.id,
        u.cover_url,
        u.name,
        l.city || ', ' || l.state AS location,
        COALESCE(
            (SELECT json_agg(
                json_build_object(
                    'partner_agency', pa.name,
                    'partner_type', pa.partner_type,
                    'commission_percentage', c."inPercentage",
                    'commission_amount', c."inAmount"
                )
            )
            FROM university_commission c
            LEFT JOIN university_partner_agency pa ON c.partner_agency_id = pa.id
            WHERE c.university_id = u.id),
            '[]'::json
        ) AS partners,
        COALESCE(
            (SELECT json_agg(json_build_object('name', s.name, 'value', s.value))
             FROM university_stats s
             WHERE s.university_id = u.id),
            '[]'::json
        ) AS statistics,
        COALESCE(
            (SELECT MAX(c."inPercentage")
             FROM university_commission c
             WHERE c.university_id = u.id),
            -1
        ) AS max_percentage,
        COALESCE(
            (SELECT MAX(c."inAmount")
             FROM university_commission c
             WHERE c.university_id = u.id),
            -1
        ) AS max_amount
    FROM university_university u
    JOIN university_location l ON u.location_id = l.id
    ORDER BY 
        max_percentage DESC,
        max_amount DESC;
    """

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    data = [
        {
            "id": row[0],
            "cover_url": row[1],
            "name": row[2],
            "location": row[3],
            "partners": row[4],  # Array of objects with partner_agency, partner_type, commission_percentage, commission_amount
            "statistics": row[5]  # Array of objects with name, value
        }
        for row in rows
    ]

    return JsonResponse({
        "results": data,
        "count": len(data)
    })

@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def university_detail(request, university_id):
    try:
        # Execute raw SQL query with CTEs to prevent data duplication
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH stats_agg AS (
                    SELECT 
                        university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', s.id,
                                    'name', s.name,
                                    'value', s.value
                                )
                            ) FILTER (WHERE s.id IS NOT NULL),
                            '[]'
                        ) AS statistics
                    FROM university_stats s
                    GROUP BY university_id
                ),
                videos_agg AS (
                    SELECT 
                        university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', v.id,
                                    'url', v.url
                                )
                            ) FILTER (WHERE v.id IS NOT NULL),
                            '[]'
                        ) AS video_links
                    FROM university_videos_links v
                    GROUP BY university_id
                ),
                rankings_agg AS (
                    SELECT 
                        ur.university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', ur.id,
                                    'rank', ur.rank,
                                    'ranking_agency', json_build_object(
                                        'id', ra.id,
                                        'name', ra.name,
                                        'description', ra.description,
                                        'logo', ra.logo
                                    )
                                )
                            ) FILTER (WHERE ur.id IS NOT NULL),
                            '[]'
                        ) AS rankings
                    FROM university_university_ranking ur
                    LEFT JOIN university_ranking_agency ra ON ur.ranking_agency_id = ra.id
                    GROUP BY ur.university_id
                ),
                faqs_agg AS (
                    SELECT 
                        university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', f.id,
                                    'question', f.question,
                                    'answer', f.answer
                                )
                            ) FILTER (WHERE f.id IS NOT NULL),
                            '[]'
                        ) AS faqs
                    FROM university_faqs f
                    GROUP BY university_id
                )
                SELECT
                    u.id AS university_id,
                    u.cover_url,
                    u.cover_origin,
                    u.name AS university_name,
                    u.type,
                    u.establish_year,
                    u.about,
                    u.admission_requirements,
                    u.location_map_link,
                    u.status,
                    l.id AS location_id,
                    l.city,
                    l.state,
                    COALESCE(sa.statistics, '[]') AS statistics,
                    COALESCE(va.video_links, '[]') AS video_links,
                    COALESCE(ra.rankings, '[]') AS rankings,
                    COALESCE(fa.faqs, '[]') AS faqs
                FROM
                    university_university u
                    LEFT JOIN university_location l ON u.location_id = l.id
                    LEFT JOIN stats_agg sa ON u.id = sa.university_id
                    LEFT JOIN videos_agg va ON u.id = va.university_id
                    LEFT JOIN rankings_agg ra ON u.id = ra.university_id
                    LEFT JOIN faqs_agg fa ON u.id = fa.university_id
                WHERE
                    u.id = %s;
            """, [university_id])
            
            row = cursor.fetchone()
            
            if not row:
                return JsonResponse({"error": "University not found"}, status=404)
            
            # Map the query result to a dictionary
            result = {
                "id": row[0],
                "cover_url": row[1],
                "cover_origin": row[2],
                "name": row[3],
                "type": row[4],
                "establish_year": row[5],
                "about": row[6],
                "admission_requirements": row[7],
                "location_map_link": row[8],
                "status": row[9],
                "location": {
                    "id": row[10],
                    "city": row[11],
                    "state": row[12]
                },
                "statistics": row[13],  # JSON array from PostgreSQL
                "video_links": row[14],  # JSON array
                "rankings": row[15],     # JSON array
                "faqs": row[16]          # JSON array
            }
            
            return JsonResponse(result, status=200)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["GET"])
def university_detail_employee(request, university_id):
    employee_id = request.user.id
    if not has_perms(employee_id, ["university_view"]):
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to perform this task'
        }, status=403)

    try:
        # Execute raw SQL query with CTEs
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH commission_agg AS (
                    SELECT 
                        c.university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', c.id,
                                    'inPercentage', c."inPercentage",
                                    'inAmount', c."inAmount",
                                    'partner_agency', json_build_object(
                                        'id', pa.id,
                                        'name', pa.name
                                    )
                                )
                            ) FILTER (WHERE c.id IS NOT NULL),
                            '[]'
                        ) AS commissions
                    FROM university_commission c
                    LEFT JOIN university_partner_agency pa ON c.partner_agency_id = pa.id
                    GROUP BY c.university_id
                ),
                mou_agg AS (
                    SELECT 
                        university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', m.id,
                                    'mou_copy_link', m."MoU_copy_link",
                                    'signing_date', m."SigningDate",
                                    'expiry_date', m."ExpiryDate",
                                    'duration_in_years', m."Duration_in_years",
                                    'duration_in_months', m."Duration_in_Months"
                                )
                            ) FILTER (WHERE m.id IS NOT NULL),
                            '[]'
                        ) AS mous
                    FROM university_mou m
                    GROUP BY university_id
                ),
                contact_agg AS (
                    SELECT 
                        university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', uc.id,
                                    'name', uc.name,
                                    'designation', uc.designation,
                                    'email', uc.email,
                                    'phone', uc.phone
                                )
                            ) FILTER (WHERE uc.id IS NOT NULL),
                            '[]'
                        ) AS contacts
                    FROM university_uni_contact uc
                    GROUP BY university_id
                ),
                stats_agg AS (
                    SELECT 
                        university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', s.id,
                                    'name', s.name,
                                    'value', s.value
                                )
                            ) FILTER (WHERE s.id IS NOT NULL),
                            '[]'
                        ) AS statistics
                    FROM university_stats s
                    GROUP BY university_id
                ),
                videos_agg AS (
                    SELECT 
                        university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', v.id,
                                    'url', v.url
                                )
                            ) FILTER (WHERE v.id IS NOT NULL),
                            '[]'
                        ) AS video_links
                    FROM university_videos_links v
                    GROUP BY university_id
                ),
                rankings_agg AS (
                    SELECT 
                        ur.university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', ur.id,
                                    'rank', ur.rank,
                                    'ranking_agency', json_build_object(
                                        'id', ra.id,
                                        'name', ra.name,
                                        'description', ra.description,
                                        'logo', ra.logo
                                    )
                                )
                            ) FILTER (WHERE ur.id IS NOT NULL),
                            '[]'
                        ) AS rankings
                    FROM university_university_ranking ur
                    LEFT JOIN university_ranking_agency ra ON ur.ranking_agency_id = ra.id
                    GROUP BY ur.university_id
                ),
                faqs_agg AS (
                    SELECT 
                        university_id,
                        COALESCE(
                            json_agg(
                                json_build_object(
                                    'id', f.id,
                                    'question', f.question,
                                    'answer', f.answer
                                )
                            ) FILTER (WHERE f.id IS NOT NULL),
                            '[]'
                        ) AS faqs
                    FROM university_faqs f
                    GROUP BY university_id
                )
                SELECT
                    u.id AS university_id,
                    u.cover_url,
                    u.cover_origin,
                    u.name AS university_name,
                    u.type,
                    u.establish_year,
                    u.about,
                    u.admission_requirements,
                    u.location_map_link,
                    u.status,
                    l.id AS location_id,
                    l.city,
                    l.state,
                    COALESCE(ca.commissions, '[]') AS commissions,
                    COALESCE(ma.mous, '[]') AS mous,
                    COALESCE(coa.contacts, '[]') AS contacts,
                    COALESCE(sa.statistics, '[]') AS statistics,
                    COALESCE(va.video_links, '[]') AS video_links,
                    COALESCE(ra.rankings, '[]') AS rankings,
                    COALESCE(fa.faqs, '[]') AS faqs
                FROM
                    university_university u
                    LEFT JOIN university_location l ON u.location_id = l.id
                    LEFT JOIN commission_agg ca ON u.id = ca.university_id
                    LEFT JOIN mou_agg ma ON u.id = ma.university_id
                    LEFT JOIN contact_agg coa ON u.id = coa.university_id
                    LEFT JOIN stats_agg sa ON u.id = sa.university_id
                    LEFT JOIN videos_agg va ON u.id = va.university_id
                    LEFT JOIN rankings_agg ra ON u.id = ra.university_id
                    LEFT JOIN faqs_agg fa ON u.id = fa.university_id
                WHERE
                    u.id = %s;
            """, [university_id])
            
            row = cursor.fetchone()
            
            if not row:
                return JsonResponse({"error": "University not found"}, status=404)
            
            # Map the query result to a dictionary
            result = {
                "id": row[0],
                "cover_url": row[1],
                "cover_origin": row[2],
                "name": row[3],
                "type": row[4],
                "establish_year": row[5],
                "about": row[6],
                "admission_requirements": row[7],
                "location_map_link": row[8],
                "status": row[9],
                "location": {
                    "id": row[10],
                    "city": row[11],
                    "state": row[12]
                },
                "commissions": row[13],
                "mous": row[14],
                "contacts": row[15],
                "statistics": row[16],
                "video_links": row[17],
                "rankings": row[18],
                "faqs": row[19]
            }
            
            return JsonResponse(result, status=200)
            
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)