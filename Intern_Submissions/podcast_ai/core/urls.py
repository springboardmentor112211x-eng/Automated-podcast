from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload, name="upload"),
    path('result/<int:id>/', views.result, name="result"),
    path('review/', views.review, name="review"),
]
