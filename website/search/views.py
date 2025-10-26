from django.shortcuts import render

# from .models import UnsanitizedSearch, SanitizedSearch
from django.views.decorators.http import require_http_methods
from django.db import connection
from django.views import View
from django.http import JsonResponse
from django.db import connection, transaction
# Create your views here.


# @require_http_methods(["GET"])
class SearchSuggestionsView(View):
    def get(self, request):
        user_query = request.GET.get("q", "").strip()

        if len(user_query) < 3:
            return JsonResponse([], safe=False)

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM fetch_search_suggestions(%s)", [user_query])
            rows = cursor.fetchall()

        results = [row[0] for row in rows]
        return JsonResponse(results, safe=False)


# class SaveUnsanitizedSearchView(View):
#     def get(self, request):
#         query = request.GET.get("q", "").strip()
#
#         if len(query) < 3:
#             return JsonResponse(
#                 {"status": "error", "message": "Query must be at least 3 characters"},
#                 status=400,
#             )
#
#         try:
#             with transaction.atomic():
#                 with connection.cursor() as cursor:
#                     # Try to update count if exists
#                     cursor.execute(
#                         """
#                         UPDATE unsanitized_searches
#                         SET count = count + 1
#                         WHERE query = %s
#                         RETURNING id, count
#                         """,
#                         [query],
#                     )
#                     row = cursor.fetchone()
#
#                     if row:
#                         obj_id, count = row
#                     else:
#                         # Insert new query if it does not exist
#                         cursor.execute(
#                             """
#                             INSERT INTO unsanitized_searches (query, count)
#                             VALUES (%s, 1)
#                             RETURNING id, count
#                             """,
#                             [query],
#                         )
#                         obj_id, count = cursor.fetchone()
#
#         except Exception as e:
#             return JsonResponse({"status": "error", "message": str(e)}, status=500)
#
#         return JsonResponse({"status": "success", "query": query, "count": count})
