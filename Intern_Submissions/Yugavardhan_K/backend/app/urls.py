from django.urls import path
from .import views

urlpatterns = [
    path("", views.upload_audio, name="upload_audio"),

    # ✅ Use <str:job_id> to match string UUIDs
    path("progress/<str:job_id>/", views.pipeline_progress, name="pipeline_progress"),

    path("result/<str:job_id>/", views.pipeline_result, name="pipeline_result"),

    path("download/pdf/<str:job_id>/", views.download_pdf, name="download_pdf"),
    path("download/docx/<str:job_id>/", views.download_docx, name="download_docx"),
    path(
        "download/text/<str:job_id>/<str:filename>/",
        views.download_text,
        name="download_text",
    ),
]