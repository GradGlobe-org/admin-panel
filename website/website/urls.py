from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
import os

IS_PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    path("", include("django_prometheus.urls")),
    path("", include("core.urls")),
    path("admin/", admin.site.urls),
    path("auth/", include("authentication.urls")),
    path("blog/", include("blogs.urls")),
    path("seo/", include("seo.urls")),
    path("university/", include("university.urls")),
    path("scholarships/", include("scholarship.urls")),
    path("user/", include("student.urls")),
    path("course/", include("course.urls")),
    path("search/", include("search.urls")),
    path("exams/", include("exams.urls")),
    path("events/", include("events.urls")),
    path("tasks/", include("tasks.urls")),
]

if not IS_PRODUCTION:
    urlpatterns += [
        path("schema-viewer/", include("schema_viewer.urls")),
    ]