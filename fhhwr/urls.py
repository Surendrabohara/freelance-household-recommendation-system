from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from users import views

urlpatterns = [
    path("", views.base_view, name="home"),
    path("admin/", admin.site.urls),
    path("users/", include("users.urls", namespace="users")),
    path("tasks/", include("tasks.urls", namespace="tasks")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
