from django.contrib import admin
from django.urls import path, include
from .views import *
from .test_views import *

urlpatterns = [
    
    # Perfect (Muuah)
    path('get_university_by_name/', get_university_by_name),
    path('universities/', paginated_universities),
    path('get_university_locations/', get_university_location),
    path('get_university_ranking_agencies/', get_university_ranking_agency),
    path('get_university_partner_agencies/', get_university_partner_agency),
    # To be Modified
   
    path('destination/', destination_page, name='destination_page'),
]


# Temp Urls Either for testing or Updates in the DB via MCP llm.
urlpatterns += [


    # path("api/update-cost-of-living/", UpdateCostOfLivingView.as_view(), name="update_cost_of_living"),
    # path("api/update-university_admission_stats/", update_admission_stats, name="update_admission_stats"),
]