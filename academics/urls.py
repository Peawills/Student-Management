# academics/urls.py

from django.urls import path
from . import views

app_name = "academics"

urlpatterns = [
    # Dashboard
    path("dashboard/", views.academics_dashboard, name="dashboard"),
    # Sessions
    path("sessions/", views.session_list, name="session_list"),
    path("sessions/create/", views.session_create, name="session_create"),
    path("sessions/<int:pk>/update/", views.session_update, name="session_update"),
    path("sessions/<int:pk>/delete/", views.session_delete, name="session_delete"),
    # Terms
    path("terms/", views.term_list, name="term_list"),
    path("terms/create/", views.term_create, name="term_create"),
    path("terms/<int:pk>/update/", views.term_update, name="term_update"),
    # Subjects
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/create/", views.subject_create, name="subject_create"),
    path("subjects/<int:pk>/update/", views.subject_update, name="subject_update"),
    path("subjects/<int:pk>/delete/", views.subject_delete, name="subject_delete"),
    # Classrooms
    path("classrooms/", views.classroom_list, name="classroom_list"),
    path("classrooms/create/", views.classroom_create, name="classroom_create"),
    path("classrooms/<int:pk>/", views.classroom_detail, name="classroom_detail"),
    path(
        "classrooms/<int:pk>/update/", views.classroom_update, name="classroom_update"
    ),
    path(
        "classrooms/<int:pk>/add-students/",
        views.add_students_to_class,
        name="add_students_to_class",
    ),
    path(
        "classrooms/<int:classroom_pk>/remove-student/<int:student_pk>/",
        views.remove_student_from_class,
        name="remove_student_from_class",
    ),
    path(
        "classrooms/move-student/",
        views.move_student_to_class,
        name="move_student_to_class",
    ),
    # Assignments
    path("assignments/", views.assignment_list, name="assignment_list"),
    path("assignments/create/", views.assignment_create, name="assignment_create"),
    path(
        "assignments/<int:pk>/update/",
        views.assignment_update,
        name="assignment_update",
    ),
    # Assessments
    path("assessments/", views.assessment_list, name="assessment_list"),
    path("assessments/create/", views.assessment_create, name="assessment_create"),
    path("assessments/<int:pk>/", views.assessment_detail, name="assessment_detail"),
    path(
        "assessments/<int:pk>/update/",
        views.assessment_update,
        name="assessment_update",
    ),
    path(
        "assessments/<int:pk>/delete/",
        views.assessment_delete,
        name="assessment_delete",
    ),
    # Scores
    path(
        "assessments/<int:assessment_id>/scores/",
        views.bulk_score_entry,
        name="bulk_score_entry",
    ),
    path("scores/import/", views.import_scores, name="import_scores"),
    # Report Cards
    path("report-cards/", views.report_card_list, name="report_card_list"),
    # Analytics
    path(
        "analytics/",
        views.PerformanceAnalyticsView.as_view(),
        name="performance_analytics",
    ),
    # Comments
    path("comments/", views.comment_list, name="comment_list"),
    path("comments/create/", views.comment_create, name="comment_create"),
    path("comments/<int:pk>/update/", views.comment_update, name="comment_update"),
    # Assessment Types
    path("assessment-types/", views.assessment_type_list, name="assessment_type_list"),
    path(
        "assessment-types/create/",
        views.assessment_type_create,
        name="assessment_type_create",
    ),
    # Attendance
    path("attendance/take/", views.take_attendance, name="take_attendance"),
    path("attendance/report/", views.attendance_report, name="attendance_report"),
]
