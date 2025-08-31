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
    
    except ObjectDoesNotExist:
        return False
    except Exception as e:
        return False
