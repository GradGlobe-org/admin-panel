from django.urls import path
from .views import meta_keywords


urlpatterns = [
    path("meta_keywords/", meta_keywords)
]