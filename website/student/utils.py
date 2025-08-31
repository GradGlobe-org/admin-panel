from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from .models import Student, StudentLogs

def create_student_log(request, log_text = "Empty Action"):
    # Get authToken from headers (using 'X-Auth-Token' as header name)
    auth_token = request.headers.get('X-Auth-Token')
    
    if not auth_token:
        return False
    
    try:
        # Find student by authToken
        student = Student.objects.get(authToken=auth_token)
        
        # Create new log entry
        StudentLogs.objects.create(
            student=student,
            logs=log_text
        )
        return HttpResponse("Log created successfully", status=201)
    
    except ObjectDoesNotExist:
        return HttpResponse("Invalid auth token", status=401)
    except Exception as e:
        return HttpResponse(f"Error creating log: {str(e)}", status=500)
