from django.urls import path
from .views import search_course

urlpatterns = [

    # Perfect No Need For Optimization
    path('search-course/', search_course, name='search-course'),

    
]