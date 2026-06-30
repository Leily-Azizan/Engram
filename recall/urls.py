from django.urls import path

from . import views

urlpatterns = [
    path("", views.review, name="review"),
    path("answer/", views.review_answer, name="review_answer"),
    path("feynman/", views.feynman, name="feynman"),
    path("feynman/save/", views.feynman_save, name="feynman_save"),
]
