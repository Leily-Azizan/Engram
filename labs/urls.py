from django.urls import path

from . import views

urlpatterns = [
    path("", views.lab_list, name="lab_list"),
    path("<slug:slug>/", views.lab_detail, name="lab_detail"),
    path("<slug:slug>/save/", views.lab_save, name="lab_save"),
]
