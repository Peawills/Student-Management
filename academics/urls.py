# academics/urls.py

from django.urls import path
from . import views

app_name = "academics"

urlpatterns = [
    # Dashboard
    path("dashboard/", views.academics_dashboard, name="dashboard"),
    # Publication Center
    path("publications/", views.publication_center, name="publication_center"),
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
    path(
        "assessments/<int:pk>/publish/",
        views.publish_assessment,
        name="publish_assessment",
    ),
    path(
        "assessments/<int:pk>/unpublish/",
        views.unpublish_assessment,
        name="unpublish_assessment",
    ),
    # === Score Locking System ===
    path(
        "assessments/<int:pk>/lock/",
        views.lock_assessment_scores,
        name="lock_assessment_scores",
    ),
    path(
        "assessments/<int:pk>/unlock/",
        views.unlock_assessment_scores,
        name="unlock_assessment_scores",
    ),
    path(
        "assessments/<int:pk>/validate/",
        views.validate_assessment_constraints,
        name="validate_assessment_constraints",
    ),
    path(
        "assessments/lock-management/",
        views.lock_management_dashboard,
        name="lock_management_dashboard",
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
    path("report-cards/<int:pk>/", views.report_card_detail, name="report_card_detail"),
    path(
        "report-cards/<int:pk>/interactive/",
        views.report_card_detail_interactive,
        name="report_card_detail_interactive",
    ),
    path(
        "report-cards/<int:pk>/publish/",
        views.publish_report_card,
        name="publish_report_card",
    ),
    path(
        "report-cards/<int:pk>/change-status/",
        views.change_report_card_status,
        name="change_report_card_status",
    ),
    path(
        "report-cards/bulk/publish/",
        views.bulk_publish_report_cards,
        name="bulk_publish_report_cards",
    ),
    path(
        "report-cards/<int:pk>/unpublish/",
        views.unpublish_report_card,
        name="unpublish_report_card",
    ),
    path(
        "report-cards/generate/",
        views.generate_report_cards,
        name="generate_report_cards",
    ),
    # --- New Report Card Generation Workflow ---
    path(
        "report-cards/prepare/",
        views.prepare_report_cards,
        name="prepare_report_cards",
    ),
    path(
        "report-cards/ajax/save-data/",
        views.ajax_save_report_card_data,
        name="ajax_save_report_card_data",
    ),
    path(
        "report-cards/finalize/",
        views.finalize_report_cards,
        name="finalize_report_cards",
    ),
    # Analytics
    path(
        "analytics/",
        views.PerformanceAnalyticsView.as_view(),
        name="performance_analytics",
    ),
    path(
        "analytics/export/subjects/",
        views.export_subject_performance_csv,
        name="export_subject_performance_csv",
    ),
    path(
        "analytics/export/classes/",
        views.export_class_performance_csv,
        name="export_class_performance_csv",
    ),
    path(
        "analytics/recalculate/",
        views.recalculate_term_results,
        name="recalculate_term_results",
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
    # Timetable
    path("timetables/", views.timetable_list, name="timetable_list"),
    path("timetables/create/", views.timetable_create, name="timetable_create"),
    path(
        "timetables/<int:pk>/update/", views.timetable_update, name="timetable_update"
    ),
    path(
        "timetables/<int:pk>/delete/", views.timetable_delete, name="timetable_delete"
    ),
]
