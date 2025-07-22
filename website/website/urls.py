from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
import os

IS_PRODUCTION = os.getenv("PRODUCTION", "False").lower() == "true"

urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False)),  # ← redirect root to /admin/
    path('', include('django_prometheus.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include("authentication.urls")),
    path('blog/', include("blogs.urls")),
    path('seo/', include("seo.urls")),
    path('university/', include("university.urls")),
    path('scholarships/', include("scholarship.urls"))
]


if not IS_PRODUCTION:
    urlpatterns += [
        path('schema-viewer/', include('schema_viewer.urls')),
    ]