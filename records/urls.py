from django.urls import path
from . import views

app_name = "records"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("studentlist/", views.student_list, name="student_list"),
    path("student/<int:pk>/", views.student_detail, name="student_detail"),
    path("student/new/", views.student_create, name="student_create"),
    path(
        "student/new/success/<int:pk>/",
        views.student_creation_success,
        name="student_creation_success",
    ),
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
    path("alumni/", views.alumni_list, name="alumni_list"),
    path(
        "student/<int:pk>/toggle-status/",
        views.toggle_student_status,
        name="toggle_student_status",
    ),
]
