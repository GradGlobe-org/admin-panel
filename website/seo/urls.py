from django.urls import path
from .views import meta_keywords, extract_keywords


urlpatterns = [
    path("meta_keywords/", meta_keywords),
    path("extract-keywords/", extract_keywords)
]