from django.urls import path
from .views import *
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("google-signin/", GoogleSignInView.as_view(), name="google_signin"),  # Added Google Sign-In endpoint
    path("add_to_shortlist_university/", add_to_shortlist_university),
    path("add_to_shortlist_course/", add_to_shortlist_course),
    path("get_shortlistings/", get_shortlisted_items),
    path("student_details/", get_student_details),
    path("update/", update_student_profile),
    path("choices_in_db/", get_all_choices),
]