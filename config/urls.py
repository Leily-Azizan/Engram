from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("learning.urls")),
    path("courses/", include("catalog.urls")),
    path("review/", include("recall.urls")),
    path("exams/", include("exams.urls")),
    path("labs/", include("labs.urls")),
    path("roadmap/", include("roadmap.urls")),
]
