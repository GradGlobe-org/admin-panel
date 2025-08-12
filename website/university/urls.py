from django.contrib import admin
from django.urls import path, include
from .views import *
from .test_views import *

urlpatterns = [
    # to be removed
    path('add_university/', add_university),
    path('edit_university/<int:university_id>/', edit_university),
    path('get_universities/<int:university_id>/', university_detail),
    
    # Perfect (Muuah)
    path('get_university_by_name/', get_university_by_name),
    path('universities/', paginated_universities),
    
    # To be Modified
    path('get_universities_employee/<int:university_id>/', university_detail_employee),
    
    path('universities_employee/', universities_employee),
    path('get_university_locations/', get_university_location),
    path('get_university_ranking_agencies/', get_university_ranking_agency),
    path('get_university_partner_agencies/', get_university_partner_agency),
    path('destination/', destination_page, name='destination_page'),
]

urlpatterns += [
    path("api/update-cost-of-living/", UpdateCostOfLivingView.as_view(), name="update_cost_of_living"),
]