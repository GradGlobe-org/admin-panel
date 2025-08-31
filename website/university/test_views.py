from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
import json

from .models import *

@method_decorator(csrf_exempt, name="dispatch")
class UpdateCostOfLivingView(View):

    @transaction.atomic
    def post(self, request):
        try:
            data = json.loads(request.body.decode("utf-8"))

            # Extract country
            country_name = data.get("country_name")
            if not country_name:
                return JsonResponse({"error": "country_name is required"}, status=400)

            try:
                country = Country.objects.get(name__iexact=country_name)
            except Country.DoesNotExist:
                return JsonResponse({"error": f"Country '{country_name}' not found"}, status=404)

            # Either update or create cost of living record
            col, _ = CostOfLiving.objects.update_or_create(
                country=country,
                defaults={
                    "rent_min": data.get("rent_min"),
                    "rent_max": data.get("rent_max"),
                    "food_min": data.get("food_min"),
                    "food_max": data.get("food_max"),
                    "transport_min": data.get("transport_min"),
                    "transport_max": data.get("transport_max"),
                    "miscellaneous_min": data.get("miscellaneous_min"),
                    "miscellaneous_max": data.get("miscellaneous_max"),
                    "total_min": data.get("total_min"),
                    "total_max": data.get("total_max"),
                }
            )

            return JsonResponse({
                "message": "Cost of Living updated successfully",
                "country": country.name
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
        




@csrf_exempt
def update_admission_stats(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        uni_name = data.get("university_name")
        stats_data = data.get("stats", {})

        if not uni_name or not stats_data:
            return JsonResponse({"error": "university_name and stats are required"}, status=400)

        try:
            uni = university.objects.get(name=uni_name)
        except university.DoesNotExist:
            return JsonResponse({"error": "University not found"}, status=404)

        for admission_type in ["UNDERGRADUATE", "GRADUATE"]:
            stat_values = stats_data.get(admission_type)
            if not stat_values:
                continue  # Skip if not provided

            AdmissionStats.objects.update_or_create(
                university=uni,
                admission_type=admission_type,
                defaults={
                    "application_fee": stat_values.get("application_fee", 0),
                    "GPA_min": stat_values.get("GPA_min", 0),
                    "GPA_max": stat_values.get("GPA_max", 0),
                    "SAT_min": stat_values.get("SAT_min", 0),
                    "SAT_max": stat_values.get("SAT_max", 0),
                    "ACT_min": stat_values.get("ACT_min", 0),
                    "ACT_max": stat_values.get("ACT_max", 0),
                    "IELTS_min": stat_values.get("IELTS_min", 0),
                    "IELTS_max": stat_values.get("IELTS_max", 0),
                }
            )

        return JsonResponse({"status": "success"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def update_admission_stats(request):
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
        uni_name = data.get("university_name")
        stats_data = data.get("stats", {})

        if not uni_name or not stats_data:
            return JsonResponse({"error": "university_name and stats are required"}, status=400)

        try:
            uni = university.objects.get(name=uni_name)
        except university.DoesNotExist:
            return JsonResponse({"error": "University not found"}, status=404)

        for admission_type in ["UNDERGRADUATE", "GRADUATE"]:
            stat_values = stats_data.get(admission_type)
            if not stat_values:
                continue  # Skip if not provided

            AdmissionStats.objects.update_or_create(
                university=uni,
                admission_type=admission_type,
                defaults={
                    "application_fee": stat_values.get("application_fee", 0),
                    "GPA_min": stat_values.get("GPA_min", 0),
                    "GPA_max": stat_values.get("GPA_max", 0),
                    "SAT_min": stat_values.get("SAT_min", 0),
                    "SAT_max": stat_values.get("SAT_max", 0),
                    "ACT_min": stat_values.get("ACT_min", 0),
                    "ACT_max": stat_values.get("ACT_max", 0),
                    "IELTS_min": stat_values.get("IELTS_min", 0),
                    "IELTS_max": stat_values.get("IELTS_max", 0),
                }
            )

        return JsonResponse({"status": "success"})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)