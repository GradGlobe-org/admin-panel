from django.urls import path, include
from .views import blog_post_summary_view


urlpatterns = [
    path('get_all_blogs/', blog_post_summary_view),
    
]