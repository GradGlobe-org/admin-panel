from django.shortcuts import render
import json
from django.http import JsonResponse
from website.utils import api_key_required, has_perms, token_required
from .models import university, location, ranking_agency, Partner_Agency
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import location
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
    locations = location.objects.all().values()
    return JsonResponse({
        "locations" : list(locations),
    }, status=200)

@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def get_university_ranking_agency(request):
    agencies = ranking_agency.objects.all().values()
    return JsonResponse({
        "Ranking Agencies" : list(agencies)
    }, status=200)

@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def get_university_partner_agency(request):
    agencies = Partner_Agency.objects.all().values()
    return JsonResponse({
        "Partner Agencies" : list(agencies)
    }, status=200)
