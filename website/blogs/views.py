from django.shortcuts import render
from django.http import JsonResponse
from django.db import connection
import json
from website.utils import api_key_required, has_perms, token_required
from .models import Post
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from authentication.models import Employee
from slugify import slugify  # using `python-slugify`
from django.views.decorators.csrf import csrf_exempt
import uuid

STREAM_IMAGE_URL = "admin.gradglobe.org/blog/images"

@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def blog_post_summary_view(request):
    auth_token = request.headers.get("Authorization")

    try:
        with connection.cursor() as cursor:
            if not auth_token:
                cursor.execute("""
                    SELECT p.id, p.title, p.slug, p.view_count, p.featured_image, p.image_uuid, p.google_file_id,
                           SUBSTR(p.content,1,1000) AS content_snippet, e.name AS author_name
                    FROM blogs_post p
                    JOIN authentication_employee e ON p.author_id = e.id
                    WHERE p.status='PUBLISHED'
                    ORDER BY p.created_at DESC
                """)
            else:
                try:
                    uuid_token = uuid.UUID(auth_token)
                    request.user = Employee.objects.get(authToken=uuid_token)
                except (ValueError, Employee.DoesNotExist):
                    return JsonResponse({"error": "Invalid or expired token"}, status=403)

                cursor.execute("""
                    SELECT p.id, p.title, p.slug, p.view_count, p.featured_image, p.image_uuid, p.google_file_id, p.status,
                           SUBSTR(p.content,1,1000) AS content_snippet, e.name AS author_name
                    FROM blogs_post p
                    JOIN authentication_employee e ON p.author_id = e.id
                    ORDER BY p.created_at DESC
                """)

            columns = [col[0] for col in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

        results = []
        for row in rows:
            # Determine featured_image link
            if row.get("featured_image"):
                featured_link = row["featured_image"]
            elif row.get("google_file_id") and row.get("image_uuid"):
                featured_link = f"{STREAM_IMAGE_URL}?uuid={row['image_uuid']}&w=1200&h=1200"
            else:
                featured_link = ""

            # Only keep the fields you want to expose
            results.append({
                "id": row["id"],
                "title": row["title"],
                "slug": row["slug"],
                "view_count": row["view_count"],
                "featured_image": featured_link,
                "content_snippet": row["content_snippet"],
                "author_name": row["author_name"],
                "status": row.get("status", "PUBLISHED")
            })

        return JsonResponse(results, safe=False)

    except Exception:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": "An unexpected error occurred."}, status=500)
        

@api_key_required
def blog_post_detail_view(request, identifier):
    try:
        # Try to get by ID first (if identifier is numeric)
        if identifier.isdigit():
            post = get_object_or_404(Post.objects.select_related('author'), id=int(identifier))
        else:
            post = get_object_or_404(Post.objects.select_related('author'), slug=identifier)
        
        # Increment view count
        post.view_count += 1
        post.save()
        
        data = {
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'content': post.content,
            'featured_image': post.featured_image,
            'author': {
                'id': post.author.id,
                'username': post.author.username,
                'name': post.author.name,
                'email': post.author.email
            },
            'created_at': post.created_at,
            'modified_at': post.modified_at,
            'status': post.status,
            'meta_keyword': post.meta_keyword,
            'meta_description': post.meta_description,
            'view_count': post.view_count
        }
        return JsonResponse({'status': 'success', 'data': data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["POST"])
def blog_post_create_view(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON'
        }, status=400)

    # Required fields (excluding author_id because it comes from token)
    required_fields = ['title', 'content']
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return JsonResponse({
            'status': 'error',
            'message': f"Missing required fields: {', '.join(missing_fields)}"
        }, status=400)

    author = request.user  # comes from @token_required

    # Permission check
    if not has_perms(author.id, ["Blog_create"]):
        return JsonResponse({
            'status': 'error',
            'message': 'You do not have permission to perform this task'
        }, status=403)

    try:
        # Create Post
        post = Post(
            title=data['title'],
            content=data['content'],
            author=author,
            status=data.get('status', 'DRAFT'),
            featured_image=data.get('featured_image', 'no image'),
            meta_keyword=data.get('meta_keyword', ''),
            meta_description=data.get('meta_description', '')
        )

        # Handle slug
        slug_source = data.get('slug') or data['title']
        post.slug = slugify(slug_source)

        # Validate and save
        post.full_clean()
        post.save()

        return JsonResponse({
            'status': 'success',
            'data': {
                'id': post.id,
                'slug': post.slug,
                'title': post.title,
                'author': author.username
            }
        }, status=201)

    except ValidationError as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Validation failed',
            'errors': e.message_dict  # Use .message_dict for structured validation error output
        }, status=400)

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["PUT", "PATCH"])
def blog_post_update_view(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        author = request.user
        
        # Verify requesting user is the author
        # if 'author_id' not in data:
        #     return JsonResponse({
        #         'status': 'error',
        #         'message': 'author_id is required'
        #     }, status=400)

        author_id = author.id
        
        # Verify author exists        
        if not has_perms(int(author_id), ["Blog_update"]):
            return JsonResponse({
                    'status': 'error',
                    'message': f'Employee does not have permissions to perform this task'
                }, status=400)
        
        if post.author.id != int(author_id):
            return JsonResponse({
                'status': 'error',
                'message': 'Only the post author can update this post'
            }, status=403)
        
        # Update fields if they exist in the request
        if 'title' in data:
            post.title = data['title']
            # Only auto-generate slug if title changes and no custom slug provided
            if 'slug' not in data:
                post.slug = slugify(data['title'])
        
        # Handle custom slug if provided
        if 'slug' in data and data['slug']:
            post.slug = slugify(data['slug'])
        
        updatable_fields = [
            'content', 'status', 'featured_image',
            'meta_keyword', 'meta_description'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(post, field, data[field])
        
        post.full_clean()
        post.save()
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'id': post.id,
                'slug': post.slug,
                'title': post.title,
                'status': post.status,
                'author_id': post.author.id
            }
        })
        
    except ValidationError as e:
        return JsonResponse({
            'status': 'error',
            'message': 'Validation failed',
            'errors': dict(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)    


@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["DELETE"])
def blog_post_delete_view(request, post_id):
    try:
        # Get the post and verify existence
        post = get_object_or_404(Post, id=post_id)
        # data = json.loads(request.body)
        author = request.user
        author_id = author.id
        
        # Parse request body to get the requesting user's ID
        # try:
        #     data = json.loads(request.body)
        #     requesting_user_id = data.get('author_id')
        #     if not requesting_user_id:
        #         raise ValueError("Requesting user ID is required")
        # except json.JSONDecodeError:
        #     return JsonResponse({
        #         'status': 'error',
        #         'message': 'Invalid JSON payload'
        #     }, status=400)
        
        # Verify author exists        
        if not has_perms(int(author_id), ["Blog_delete"]):
            return JsonResponse({
                    'status': 'error',
                    'message': f'Employee does not have permissions to perform this task'
                }, status=400)
        
        # Verify the requesting user is the author
        if post.author.id != int(author_id):
            return JsonResponse({
                'status': 'error',
                'message': 'Only the post author can delete this post'
            }, status=403)
        
        # Delete the post
        post.delete()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Post deleted successfully',
            'deleted_post': {
                'id': post_id,
                'title': post.title
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

@csrf_exempt
@api_key_required
@token_required
@require_http_methods(["GET"])  
def posts_by_author_view(request):
    try:
        # data = json.loads(request.body)
        author = request.user
        author_id = author.id
        
        # Validate author_id is provided
        # if 'author_id' not in data:
        #     return JsonResponse({
        #         'status': 'error',
        #         'message': 'author_id is required in request body'
        #     }, status=400)
        
        # Verify author exists        
        if not has_perms(int(author_id), ["Blog_view"]):
            return JsonResponse({
                    'status': 'error',
                    'message': f'Employee does not have permissions to perform this task'
                }, status=400)
        
        posts = Post.objects.filter(author_id=author_id).order_by('-created_at')
        
        posts_data = []
        for post in posts:
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'content_snippet': post.content[:500],  # First 500 chars
                'status': post.status,
                'created_at': post.created_at,
                'view_count': post.view_count,
                'featured_image': post.featured_image
            })
        
        return JsonResponse({
            'status': 'success',
            'data': {
                'author_id': author_id,
                'posts': posts_data,
                'count': len(posts_data)
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON payload'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
    

from django.http import HttpResponse
from .models import Post
from .utils import stream_google_drive_image

def stream_post_image(request):
    file_id = request.GET.get("id")
    uuid_val = request.GET.get("uuid")

    width = request.GET.get("w")
    height = request.GET.get("h")

    # resolve uuid → google_file_id
    if uuid_val:
        try:
            post = Post.objects.get(image_uuid=uuid_val)
            file_id = post.google_file_id
        except Post.DoesNotExist:
            return HttpResponse("Image not found", status=404)

    # convert width/height safely
    width = int(width) if width else None
    height = int(height) if height else None

    return stream_google_drive_image(file_id, width, height)