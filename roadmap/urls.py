from django.urls import path

from . import views

urlpatterns = [
    path("", views.roadmap, name="roadmap"),
    path("stage/update/", views.stage_update, name="stage_update"),
]
