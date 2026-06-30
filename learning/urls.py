from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("session/", views.session, name="session"),
    path("search/", views.search, name="search"),
    path("notes/", views.notes_all, name="notes_all"),
    path("notes/save/", views.note_save, name="note_save"),
    path("progress/update/", views.progress_update, name="progress_update"),
]
