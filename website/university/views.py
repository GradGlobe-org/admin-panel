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

    return JsonResponse(row[0], safe=False, status=200)






@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def destination_page(request):
    # Get country from query parameters
    country_name = request.GET.get("country")

    # Validate country parameter
    if not country_name:
        return JsonResponse({"error": "Country parameter is required"}, status=400)

    # === Top 5 Universities by Rank ===
    top_universities = (
        university.objects.filter(location__country=country_name)  # This uses CharField
        .annotate(best_rank=Min("rankings__rank"))
        .select_related("location")
        .prefetch_related("rankings", "faqs")
        .order_by("best_rank")[:5]
    )

    top_universities_data = []
    for uni in top_universities:
        qs_rank = next((r.rank for r in uni.rankings.all()), None)
        top_universities_data.append(
            {
                "name": uni.name,
                "location": f"{uni.location.city}, {uni.location.state}, {uni.location.country}",
                "type": uni.type,
                "acceptance_rate": uni.avg_acceptance_rate,
                "tuition_fee": uni.avg_tution_fee,
                "qs_ranking": qs_rank,
                "cover": uni.cover_url,
            }
        )

    # === Average Admission Stats ===
    stats_qs = AdmissionStats.objects.filter(university__location__country=country_name)
    if stats_qs.exists():
        avg_stats_raw = stats_qs.aggregate(
            GPA_min=Avg("GPA_min"),
            GPA_max=Avg("GPA_max"),
            SAT_min=Avg("SAT_min"),
            SAT_max=Avg("SAT_max"),
            ACT_min=Avg("ACT_min"),
            ACT_max=Avg("ACT_max"),
            IELTS_min=Avg("IELTS_min"),
            IELTS_max=Avg("IELTS_max"),
            application_fee=Avg("application_fee"),
        )
        avg_stats = {
            k: float(v) if v is not None else None for k, v in avg_stats_raw.items()
        }
    else:
        avg_stats = {}

    # === Unique Visas ===
    visa_qs = Visa.objects.filter(university__location__country=country_name).order_by(
        "name", "id"
    )
    visa_map = {}
    for visa in visa_qs:
        if visa.name not in visa_map:
            visa_map[visa.name] = {
                "name": visa.name,
                "cost": visa.cost,
                "type_of_visa": visa.type_of_visa,
                "describe": visa.describe,
            }
    visa_data = list(visa_map.values())

    # === Cost of Living ===
    try:
        cost = CostOfLiving.objects.get(
            country__name=country_name
        )  # Fixed: use country__name
        cost_of_living = {
            "rent_min": float(cost.rent_min),
            "rent_max": float(cost.rent_max),
            "food_min": float(cost.food_min),
            "food_max": float(cost.food_max),
            "transport_min": float(cost.transport_min),
            "transport_max": float(cost.transport_max),
            "miscellaneous_min": float(cost.miscellaneous_min),
            "miscellaneous_max": float(cost.miscellaneous_max),
            "total_min": float(cost.total_min),
            "total_max": float(cost.total_max),
        }
    except CostOfLiving.DoesNotExist:
        cost_of_living = {}

    # === Top 10 Work Opportunities ===
    work_qs = (
        WorkOpportunity.objects.filter(university__location__country=country_name)
        .values("name")
        .annotate(count=Count("name"))
        .order_by("-count")[:10]
    )
    work_opportunities = [item["name"] for item in work_qs]

    # === One FAQ from Top Universities ===
    faqs_data = []
    for uni in top_universities:
        faq = uni.faqs.first()
        if faq:
            faqs_data.append(
                {
                    "question": faq.question,
                    "answer": faq.answer,
                    "university": uni.name,
                }
            )

    # === Popular Universities (Top 5 by rating + rank) ===
    popular_universities = (
        university.objects.filter(location__country=country_name)
        .annotate(avg_rank=Min("rankings__rank"))
        .select_related("location")
        .prefetch_related("rankings")
        .order_by("-review_rating", "avg_rank")[:5]
    )

    popular_unis_data = []
    for uni in popular_universities:
        rank = next((r.rank for r in uni.rankings.all()), None)
        popular_unis_data.append(
            {
                "name": uni.name,
                "location": f"{uni.location.city}, {uni.location.state}, {uni.location.country}",
                "review_rating": float(uni.review_rating),
                "qs_ranking": rank,
            }
        )

    # === Why Study In Section ===
    try:
        why_study = WhyStudyInSection.objects.get(
            country__name=country_name
        )  # Fixed: use country__name
        why_study_points = [
            point.strip() for point in why_study.content.split(",") if point.strip()
        ]
    except WhyStudyInSection.DoesNotExist:
        why_study_points = []

    # === Final Response ===
    return JsonResponse(
        {
            "top_universities": top_universities_data,
            "average_admission_stats": avg_stats,
            "visa_data": visa_data,
            "cost_of_living": cost_of_living,
            "work_opportunities": work_opportunities,
            "faqs": faqs_data,
            "popular_universities": popular_unis_data,
            "why_study_in_country": why_study_points,
        }
    )