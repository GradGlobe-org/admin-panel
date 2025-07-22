from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path('add_university/', add_university),
    path('edit_university/<int:university_id>/', edit_university),
    path('get_universities/<int:university_id>/', university_detail),
    path('get_universities_employee/<int:university_id>/', university_detail_employee),
    path('universities/', paginated_universities),
    path('universities_employee/', universities_employee),
    path('get_university_locations/', get_university_location),
    path('get_university_ranking_agencies/', get_university_ranking_agency),
    path('get_university_partner_agencies/', get_university_partner_agency),
    path('destination/', destination_page, name='destination_page'),
]