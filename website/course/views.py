from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from website.utils import api_key_required
from .models import *
import json

# Uses The Supabase Function SELECT * FROM search_course('New York University', 'Applied Physics');
@require_GET
@api_key_required
def search_course(request):
    # Get and validate parameters
    university_name = request.GET.get('university', '').strip()
    course_name = request.GET.get('course', '').strip()
    
    if not university_name or not course_name:
        return JsonResponse(
            {'error': 'Both university and course parameters are required'},
            status=400
        )
    
    try:
        with connection.cursor() as cursor:
            # Execute the function call
            cursor.execute("SELECT * FROM search_course(%s, %s)", [university_name, course_name])
            result = cursor.fetchone()
            
            if not result:
                return JsonResponse(
                    {'error': 'Course not found'}, 
                    status=404
                )
            
            # The function returns a single JSON column which becomes the first item in the tuple
            response_data = result[0]
            
            # If the response already contains an error, return it with appropriate status
            if isinstance(response_data, dict) and 'error' in response_data:
                status_code = 404 if response_data['error'] == 'Course not found' else 400
                return JsonResponse(response_data, status=status_code)
            
            # Otherwise return the successful response
            return JsonResponse(response_data)
    
    except Exception as e:
        return JsonResponse(
            {'error': f'Database error: {str(e)}'},
            status=500
        )
    

# Uses The Supabase Function SELECT * FROM compare_course_search();
@require_GET
@api_key_required
def compare_course_search(request):
    # Get query parameters
    course_name = request.GET.get('course_name', None)
    program_level = request.GET.get('program_level', None)

    # Validate program_level if provided
    valid_program_levels = [choice[0] for choice in Course.PROGRAM_LEVEL_CHOICES]
    if program_level and program_level not in valid_program_levels:
        return JsonResponse(
            {
                "error": f"Invalid program_level. Must be one of: {', '.join(valid_program_levels)}"
            },
            status=400
        )

    # SQL query to call the course_search function
    query = "SELECT course_search(%s, %s) AS result"
    params = [course_name, program_level]

    # Execute the query
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        result = cursor.fetchone()[0]  # Fetch the JSONB result

    # Parse the JSONB result (string) into a Python object
    try:
        parsed_result = json.loads(result) if isinstance(result, str) else result
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "Invalid JSON response from database"},
            status=500
        )

    # Handle error case from the function
    if isinstance(parsed_result, dict) and "error" in parsed_result:
        return JsonResponse(parsed_result, status=400)

    # Return the result as JSON
    return JsonResponse(parsed_result, safe=False)

