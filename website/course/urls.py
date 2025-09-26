from django.urls import path
from .views import (
    search_course,
    compare_course_search,
    FilterSuggest,
    FilterSearchView,
    UserFilterSearchView,
    ChatSuggest,
)

urlpatterns = [
    # Perfect No Need For Optimization
    path("search-course/", search_course, name="search-course"),
    path("compare_course_search/", compare_course_search),
    path("filter_get/", FilterSearchView.as_view()),
    path("suggest_get/", FilterSuggest.as_view()),
    path("user_suggestion/", UserFilterSearchView.as_view()),
    path("chat/", ChatSuggest.as_view()),
]
