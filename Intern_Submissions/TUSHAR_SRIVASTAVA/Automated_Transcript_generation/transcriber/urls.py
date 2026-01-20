from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_podcast, name='upload_podcast'),
    path('transcript/<int:pk>/', views.transcript_detail, name='transcript_detail'),
    path('transcript/<int:pk>/pdf/', views.download_pdf, name='download_pdf'),
]