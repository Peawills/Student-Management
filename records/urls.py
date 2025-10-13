from django.urls import path
from . import views

app_name = "records"

urlpatterns = [
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("", views.student_list, name="student_list"),
    path("student/<int:pk>/", views.student_detail, name="student_detail"),
    path("student/new/", views.student_create, name="student_create"),
    path("student/<int:pk>/edit/", views.student_update, name="student_update"),
    path("student/<int:pk>/delete/", views.student_delete, name="student_delete"),
    path(
        "student/<int:student_id>/upload/",
        views.upload_document,
        name="upload_document",
    ),
    path(
        "student/<int:student_id>/bulk-upload/",
        views.bulk_upload_documents,
        name="bulk_upload_documents",
    ),
    path(
        "student/<int:student_id>/document/<int:doc_id>/delete/",
        views.delete_document,
        name="delete_document",
    ),
]
