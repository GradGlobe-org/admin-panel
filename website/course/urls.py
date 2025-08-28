from django.urls import path
from .views import search_course, compare_course_search, filter_search
urlpatterns = [

    # Perfect No Need For Optimization
    path('search-course/', search_course, name='search-course'),
    path('compare_course_search/', compare_course_search),
    path('filter_get/', filter_search)
]
