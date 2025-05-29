from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
import json
from website.utils import api_key_required

@api_key_required
def blog_post_summary_view(request):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                title,
                slug,
                viewCount,
                featured_image,
                SUBSTR(content, 1, 1000) as content_snippet
            FROM 
                blogs_post
            ORDER BY
                created_at DESC
        """)
        columns = [col[0] for col in cursor.description]
        results = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
    return JsonResponse(results, safe=False)




