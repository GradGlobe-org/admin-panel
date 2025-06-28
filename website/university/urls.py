from django.contrib import admin
from django.urls import path, include
from .views import add_university, get_university_location, get_university_ranking_agency, get_university_partner_agency, paginated_universities, paginated_universities_employee

urlpatterns = [
    path('add_university/', add_university),
    path('universities/', paginated_universities),
    path('universities_employee/', paginated_universities_employee),
    path('get_university_locations/', get_university_location),
    path('get_university_ranking_agencies/', get_university_ranking_agency),
    path('get_university_partner_agencies/', get_university_partner_agency)
]