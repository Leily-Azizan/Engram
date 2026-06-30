from django.urls import path

from . import views

urlpatterns = [
    path("", views.quiz_list, name="quiz_list"),
    path("attempt/<int:attempt_id>/", views.attempt_detail, name="attempt_detail"),
    path("<slug:slug>/", views.quiz_detail, name="quiz_detail"),
    path("<slug:slug>/take/", views.quiz_take, name="quiz_take"),
    path("<slug:slug>/submit/", views.quiz_submit, name="quiz_submit"),
]
