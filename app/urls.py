from django.urls import path
from . import views

urlpatterns = [
    path("", views.builder, name="builder"),
    path("builder/", views.builder, name="builder"),
    path("ai-describe/", views.ai_describe, name="ai_describe"),
    path("r/<uuid:share_id>/", views.public_resume, name="public_resume"),
    path("r/<uuid:share_id>/pdf/", views.resume_pdf, name="resume_pdf"),

]
