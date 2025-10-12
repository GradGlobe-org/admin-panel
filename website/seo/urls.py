from django.urls import path
from .views import (
    meta_keywords,
    extract_keywords,
    get_active_instagram_embeds,
    get_seo_sitemap_data,
)


urlpatterns = [
    path("meta_keywords/", meta_keywords),
    path("extract-keywords/", extract_keywords),
    path("instagram-posts/", get_active_instagram_embeds, name="instagram-posts"),
    path("get_seo_data/", get_seo_sitemap_data),
]

