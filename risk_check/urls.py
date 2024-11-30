from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("check", views.check, name="check"),
    path("result/<int:result_id>/", views.detail, name="result")

    #path("result", views.detail, name="result"),
    #path("result", views.result, name="result"),
    #path('detail/<int:result_id>/', views.detail, name="result"),
    
]