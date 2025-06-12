from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView


urlpatterns = [
    path('', RedirectView.as_view(url='/admin/', permanent=False)),  # ← redirect root to /admin/
    path('admin/', admin.site.urls),
    path('auth/', include("authentication.urls")),
    path('blog/', include("blogs.urls")),
    path('seo/', include("seo.urls")),
]
