from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from users.views import PreferencesView

urlpatterns = [path("admin/", admin.site.urls), path("api/auth/", include("users.urls")), path("api/users/preferences/", PreferencesView.as_view()), path("api/studies/", include("studies.urls")), path("api/notifications/", include("notifications.urls")), path("api/education/", include("education.urls")), path("api/schema/", SpectacularAPIView.as_view(), name="schema"), path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"))]
