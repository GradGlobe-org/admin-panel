from os import name

from django.urls import path

from .call_requests import *
from .views import *
from .views_employee import *

# for students
urlpatterns = [
    path("register_user/", register_and_send_otp),
    path("login_user/", send_otp),
    path("verify_otp/", verify_otp_view),
    path("add_to_shortlist_university/", add_to_shortlist_university),
    path("add_to_shortlist_course/", add_to_shortlist_course),
    path("get_shortlistings/", get_shortlisted_items),
    path("delete_shortlistings/", remove_from_shortlist_view),
    path("student_details/", get_student_details),
    path("choices_in_db/", get_all_choices),
    path("update/", update_student_profile),
    path("upload_document/", upload_document),
    path("get_user_documents_list/", get_student_documents_list),
    path(
        "download_document/", download_document
    ),  # this is valid both for student and employee
    path("student_dashboard/", student_dashboard_view),
    path("apply_to_course/", apply_to_university_view),
    path("student_applications/", student_applied_view),
    path("upload_profile_picture/", upload_image_to_drive),
    path("profile_picture/", get_profile_pic),
    # path("test_error/",test_error)
    path("get_application_status/", get_application_status_view),
]

# for employees
urlpatterns += [
    path("get_calls/", EmployeeCallRequestsView.as_view(), name="get_calls"),
    path("get_calls_students/", StudentCallRequestsView.as_view()),
    path("request_call/", RequestCallWithCounsellorView.as_view()),
    path("call_completed/", CompleteCallRequestView.as_view()),
    path("students_list/", get_all_students),
    path("logs/<int:student_id>/", get_student_logs, name="student-logs"),
    path("summarize_interest/", summarize_student_interest),
    path(
        "student_details_employee/",
        get_student_details_with_student_id,
        name="complete_student_details",
    ),
    path("get_all_buckets/", bucket_list),
    path("add_student_to_bucket/", set_student_bucket),
    path("get_assigned_students/", get_assigned_students),
    path("total_student_applications/", total_student_applications),
    path("ask_for_documents/", ask_for_documents),
    path("get_student_application_details/", get_student_application_details),
    path("update_document_status/", update_document_status),
    path("get_available_documents_list/", get_available_documents_list),
    path("update_milestone/", employee_update_milestone),
    path("student_profile_picture/", get_student_profile_pic),
]
