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