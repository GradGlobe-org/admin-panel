from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from website.utils import api_key_required



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
    
