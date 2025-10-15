from django.urls import path
from .views import *

urlpatterns = [
    # path("create_test/", create_test_view),
    # path("get_all_tests/", get_all_tests_view),
    # path("get_my_tests/", get_employee_tests_view),
    # path("add_test_to_course/", add_test_to_course_view),
    # path("assign_course_to_student/", assign_course_to_student_view),
    # path("create_new_course/", create_course_view),
    # path("get_all_courses/", get_all_courses_view),
    path("student/get_courses_list/", get_student_courses_with_test_status_view),
    path("student/get_test_details/", get_test_rules_view ),
    path("student/start_test/",start_or_resume_test_view),
    path("student/save_answer/", save_student_answer_view),
    path("student/confirm_submit/", confirm_before_submit_view),
    path("student/submit_test/", submit_test_view),
    path("result/", evaluate_subjective_answers),
]