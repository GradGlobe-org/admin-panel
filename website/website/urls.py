from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.views.decorators.csrf import csrf_exempt
from strawberry.django.views import GraphQLView
import os
from .GlobalSchema import schema

IS_PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"

urlpatterns = [
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
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

urlpatterns += [
    path("graphql/", csrf_exempt(GraphQLView.as_view(schema=schema)))
    #     The only fucking endpoint we need to care for
]

if not IS_PRODUCTION:
    urlpatterns += [
        path("schema-viewer/", include("schema_viewer.urls")),
    ]
