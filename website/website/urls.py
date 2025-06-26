from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView


urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False)),  # ← redirect root to /admin/
    # path('schema-viewer/', include('schema_viewer.urls')),
    path('', include('django_prometheus.urls')),
    path('admin/', admin.site.urls),
    path('auth/', include("authentication.urls")),
    path('blog/', include("blogs.urls")),
    path('seo/', include("seo.urls")),
    path('university/', include("university.urls"))
]