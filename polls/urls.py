from django.urls import include, path

from . import views

app_name = "polls"

question_patterns = [
    path("", views.detail, name="detail"),
    path("results/", views.results, name="results"),
    path("vote/", views.vote, name="vote"),
]

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:question_id>/", include(question_patterns)),
]
