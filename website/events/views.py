import json
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from authentication.models import Employee
from .models import Event
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


@method_decorator(csrf_exempt, name="dispatch")
class CreateEventView(View):
    def post(self, request):
        auth_token = request.headers.get("Authorization")
        if not auth_token:
            return JsonResponse({"error": "Authorization header missing"}, status=401)

        try:
            employee = Employee.objects.get(authToken=auth_token)
        except Employee.DoesNotExist:
            return JsonResponse({"error": "Invalid authToken"}, status=401)

        try:
            data = json.loads(request.body)
            name = data["name"]
            description = data.get("description", "")
            event_datetime = data["event_datetime"]
            link = data.get("link")
            image_url = data.get("image_url")
        except (KeyError, json.JSONDecodeError) as e:
            return JsonResponse({"error": f"Invalid request: {str(e)}"}, status=400)

        event = Event.objects.create(
            name=name,
            description=description,
            event_datetime=event_datetime,
            link=link,
            image_url=image_url,
            created_by=employee,
            created_on=timezone.now(),
        )

        return JsonResponse(
            {
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "event_datetime": event.event_datetime,
                "link": event.link,
                "image_url": event.image_url,
                "created_by": employee.username,
                "created_on": event.created_on,
            },
            status=201,
        )


def get_all_events(request):
    if request.method != "GET":
        return JsonResponse({"error": "Only GET allowed"}, status=405)

    events = (
        Event.objects.select_related("created_by").all().order_by("-event_datetime")
    )
    result = []

    for event in events:
        result.append(
            {
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "event_datetime": event.event_datetime,
                "link": event.link,
                "image_url": event.image_url,
                "created_by": {
                    "id": event.created_by.id if event.created_by else None,
                    "username": event.created_by.username if event.created_by else None,
                    "name": event.created_by.name if event.created_by else None,
                },
                "created_on": event.created_on,
            }
        )

    return JsonResponse(result, safe=False)


@csrf_exempt
def delete_event(request, event_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "Only DELETE allowed"}, status=405)

    auth_token = request.headers.get("Authorization")
    if not auth_token:
        return JsonResponse({"error": "Authorization header missing"}, status=401)

    try:
        employee = Employee.objects.get(authToken=auth_token)
    except Employee.DoesNotExist:
        return JsonResponse({"error": "Invalid authToken"}, status=401)

    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return JsonResponse({"error": "Event not found"}, status=404)

    event.delete()

    return JsonResponse({"success": f"Event {event_id} deleted by {employee.username}"})
