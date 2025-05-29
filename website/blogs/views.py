from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
import json

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

""" def createPost(request):
    if request.method != "POST":
        return JsonResponse({
            "error": "Method not allowed"
        }, status=405)
    
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({
            "error": "Invalid JSON request"
        }, status=400)
    
    title = data.title
    content = data.content
    featured_image = data.featured_image
    status = data.current_status
    meta_keyword = data.metaKeyword
    meta_description = data.metaDescription
    slug = data.slug
    
    if not title or not content or not status:
        return JsonResponse({
            "error": "Missing required fields"
        }, status=400) """