from django.urls import path
from .views import RegisterView, LoginView, add_to_shortlist, get_student_details, update_student_profile

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("add_to_shortlist/", add_to_shortlist),
    path("student_details/", get_student_details),
    path("update/",update_student_profile)
]