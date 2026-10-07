from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("example/", views.example, name="example"),
    path("check", views.check, name="check"),
    path("result/<int:result_id>/", views.detail, name="result"),
    path("result/<int:result_id>/delete/", views.delete_result, name="delete_result"),
    path("health/", views.health, name="health"),
]
