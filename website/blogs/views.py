from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
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
from django.core.files.uploadedfile import UploadedFile
from website.utils import upload_file_to_drive_public
import math

STREAM_IMAGE_URL = "https://admin.gradglobe.org/blog/images"

def normalize_blog_posts(rows):
    """Convert raw DB rows (dicts) into normalized response payload"""
    results = []
    for row in rows:
        # Priority: image_uuid → featured_image → empty
        if row.get("image_uuid"):
            featured_link = f"{STREAM_IMAGE_URL}?uuid={row['image_uuid']}&w=1200&h=1200"
        elif row.get("featured_image"):
            featured_link = row["featured_image"]
        else:
            featured_link = ""

        results.append({
            "id": row["id"],
            "title": row["title"],
            "slug": row["slug"],
            "view_count": row["view_count"],
            "featured_image": featured_link,
            "content_snippet": row["content_snippet"],
            "author_name": row["author_name"],
            "status": row.get("status", "PUBLISHED"),
            "modified_at": row["modified_at"]
        })
    return results

@csrf_exempt
@api_key_required
@require_http_methods(["GET"])
def blog_post_summary_view(request):
    auth_token = request.headers.get("Authorization")

    try:
        with connection.cursor() as cursor:
            if not auth_token:
                cursor.execute("SELECT supabase_blog_posts(NULL)")
            else:
                try:
                    uuid_token = uuid.UUID(auth_token)
                    request.user = Employee.objects.get(authToken=uuid_token)
                    cursor.execute("SELECT supabase_blog_posts(%s)", [str(uuid_token)])
                except (ValueError, Employee.DoesNotExist):
                    return JsonResponse({"error": "Invalid or expired token"}, status=403)

            supabase_result = cursor.fetchone()[0]  # JSON from Supabase function
            rows = json.loads(supabase_result) if supabase_result else []

        results = normalize_blog_posts(rows)
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
            'featured_image': 'https://admin.gradglobe.org' + post.featured_image,
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

MAX_FILE_SIZE_MB = 5

@require_http_methods(['POST'])
@csrf_exempt
@token_required
def upload_image_to_drive(request):
    """
    Upload an image to Google Drive and return its public URL.
    No post or author validation.
    """
    upload_file = request.FILES.get("image")

    if not upload_file:
        return JsonResponse({"error": "No image provided."}, status=400)

    if upload_file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        return JsonResponse({
            "error": f"Image size must be under {MAX_FILE_SIZE_MB} MB."
        }, status=400)

    try:
        # Upload file to Google Drive (assuming this function handles all)
        drive_file_id, generated_uuid = upload_file_to_drive_public(upload_file)

        # Generate the same-style public URL
        featured_image_url = f"/blog/images?id={drive_file_id}"

        return JsonResponse({
            "success": True,
            "featured_image": featured_image_url,
            "google_file_id": drive_file_id,
            "image_uuid": generated_uuid
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)

@require_http_methods(["GET"])
@api_key_required
@token_required
def blog_gallery(request):
    """
    API Endpoint: /blog/image-gallery/
    Supports ?search, ?limit, ?page
    Example: /blog/image-gallery/?search=django&limit=10&page=2
    """

    search = request.GET.get("search")
    limit = request.GET.get("limit", 10)
    page = request.GET.get("page", 1)

    # Validate limit
    try:
        limit = int(limit)
    except (ValueError, TypeError):
        limit = 10
    limit = max(1, min(limit, 20))  # enforce 1 ≤ limit ≤ 20

    # Validate page
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    page = max(1, page)

    offset = (page - 1) * limit

    # Base SQL (safe placeholders)
    base_query = """
        FROM blogs_post
        WHERE (%s IS NULL OR title ILIKE '%%' || %s || '%%')
    """

    try:
        with connection.cursor() as cursor:
            # Total count
            cursor.execute("SELECT COUNT(*) " + base_query, [search, search])
            total = cursor.fetchone()[0]

            # Compute total pages
            total_pages = math.ceil(total / limit) if total > 0 else 1

            # Paginated data
            cursor.execute(
                """
                SELECT id, title, featured_image
                """ + base_query + """
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                [search, search, limit, offset],
            )

            columns = [col[0] for col in cursor.description]
            posts = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return JsonResponse({
            "status": "success",
            "count": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "results": posts
        }, status=200, safe=False)

    except Exception as e:
        # In production, log error details using logging or sentry
        return JsonResponse({
            "status": "error",
            "message": "Something went wrong while fetching images.",
            # "m":str(e)
        }, status=500)