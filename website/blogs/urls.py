from django.urls import path, include
from .views import blog_post_summary_view, blog_post_detail_view, blog_post_create_view, blog_post_update_view, blog_post_delete_view, posts_by_author_view, stream_post_image, upload_featured_image_for_post


urlpatterns = [
    path('get_all_blogs/', blog_post_summary_view),
    path('by_id_or_slug/<identifier>/', blog_post_detail_view),
    path('create/', blog_post_create_view),
    path('update/<int:post_id>/', blog_post_update_view),
    path('delete/<int:post_id>/', blog_post_delete_view),
    path('by_author/', posts_by_author_view),
    path("images/", stream_post_image, name="stream_google_image"),
    path("upload-featured-image/", upload_featured_image_for_post)
]