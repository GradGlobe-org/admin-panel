from django.contrib import admin
from django.urls import path, include
from .views import scholarship_details

urlpatterns = [
    path('scholarship_details/', scholarship_details)
]