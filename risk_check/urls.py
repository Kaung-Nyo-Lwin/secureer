from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("check", views.check, name="check"),
    path("<int:result_id>/", views.detail, name="detail")
    
]