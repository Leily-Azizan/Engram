from django.urls import path

from . import views

urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("<slug:course_slug>/", views.course_detail, name="course_detail"),
    path("<slug:course_slug>/<slug:chapter_slug>/", views.chapter_detail, name="chapter_detail"),
    path(
        "<slug:course_slug>/<slug:chapter_slug>/<slug:lesson_slug>/",
        views.lesson_detail,
        name="lesson_detail",
    ),
]
