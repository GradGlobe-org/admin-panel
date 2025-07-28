from django.urls import path
from .views import RegisterView, LoginView, add_to_shortlist, get_student_details, update_student_profile, get_all_choices, GoogleSignInView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("google-signin/", GoogleSignInView.as_view(), name="google_signin"),  # Added Google Sign-In endpoint
    path("add_to_shortlist/", add_to_shortlist),
    path("student_details/", get_student_details),
    path("update/", update_student_profile),
    path("choices_in_db/", get_all_choices),
]