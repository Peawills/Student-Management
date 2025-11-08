# academics/urls.py

from django.urls import path
from . import views

app_name = "academics"

urlpatterns = [
    # ============================================
    # DASHBOARD
    # ============================================
    path("", views.academics_dashboard, name="dashboard"),
    # ============================================
    # ACADEMIC SESSION
    # ============================================
    path("sessions/", views.session_list, name="session_list"),
    path("sessions/create/", views.session_create, name="session_create"),
    path("sessions/<int:pk>/update/", views.session_update, name="session_update"),
    path("sessions/<int:pk>/delete/", views.session_delete, name="session_delete"),
    # ============================================
    # TERMS
    # ============================================
    path("terms/", views.term_list, name="term_list"),
    path("terms/create/", views.term_create, name="term_create"),
    path("terms/<int:pk>/update/", views.term_update, name="term_update"),
    # ============================================
    # SUBJECTS
    # ============================================
    path("subjects/", views.subject_list, name="subject_list"),
    path("subjects/create/", views.subject_create, name="subject_create"),
    path("subjects/<int:pk>/update/", views.subject_update, name="subject_update"),
    path("subjects/<int:pk>/delete/", views.subject_delete, name="subject_delete"),
    # ============================================
    # CLASSROOMS
    # ============================================
    path("classrooms/", views.classroom_list, name="classroom_list"),
    path("classrooms/create/", views.classroom_create, name="classroom_create"),
    path("classrooms/<int:pk>/", views.classroom_detail, name="classroom_detail"),
    path(
        "classrooms/<int:pk>/update/", views.classroom_update, name="classroom_update"
    ),
    # ============================================
    # SUBJECT ASSIGNMENTS
    # ============================================
    path("assignments/", views.assignment_list, name="assignment_list"),
    path("assignments/create/", views.assignment_create, name="assignment_create"),
    path(
        "assignments/<int:pk>/update/",
        views.assignment_update,
        name="assignment_update",
    ),
    # ============================================
    # ASSESSMENT TYPES
    # ============================================
    path("assessment-types/", views.assessment_type_list, name="assessment_type_list"),
    path(
        "assessment-types/create/",
        views.assessment_type_create,
        name="assessment_type_create",
    ),
    path(
        "assessment-types/<int:pk>/update/",
        views.assessment_type_update,
        name="assessment_type_update",
    ),
    # ============================================
    # ASSESSMENTS
    # ============================================
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
    # ============================================
    # SCORE ENTRY
    # ============================================
    path(
        "assessments/<int:assessment_id>/scores/",
        views.bulk_score_entry,
        name="bulk_score_entry",
    ),
    path("scores/import/", views.import_scores, name="import_scores"),
    # ============================================
    # TERM RESULTS
    # ============================================
    path(
        "calculate-results/<int:term_id>/<int:classroom_id>/",
        views.calculate_term_results,
        name="calculate_term_results",
    ),
    # ============================================
    # REPORT CARDS
    # ============================================
    path("report-cards/", views.report_card_list, name="report_card_list"),
    path("report-cards/<int:pk>/", views.report_card_detail, name="report_card_detail"),
    path(
        "report-cards/generate/",
        views.generate_report_cards,
        name="generate_report_cards",
    ),
    path(
        "report-cards/<int:pk>/pdf/",
        views.generate_report_card_pdf,
        name="report_card_pdf",
    ),
    # ============================================
    # ANALYTICS
    # ============================================
    path("analytics/", views.performance_analytics, name="performance_analytics"),
    path(
        "student/<int:student_id>/performance/",
        views.student_performance,
        name="student_performance",
    ),
    path("teacher/performance/", views.teacher_performance, name="teacher_performance"),
    # ============================================
    # EXPORTS
    # ============================================
    path(
        "assessments/<int:assessment_id>/export-template/",
        views.export_assessment_template,
        name="export_assessment_template",
    ),
    path(
        "classrooms/<int:classroom_id>/terms/<int:term_id>/export/",
        views.export_class_results,
        name="export_class_results",
    ),
    path(
        "terms/<int:term_id>/export-report-cards/",
        views.export_report_cards,
        name="export_report_cards",
    ),
    # ============================================
    # AJAX/API ENDPOINTS
    # ============================================
    path(
        "api/subjects-by-class/",
        views.get_subjects_by_class,
        name="get_subjects_by_class",
    ),
    path(
        "api/students-by-class/",
        views.get_students_by_class,
        name="get_students_by_class",
    ),
    path("api/save-score/", views.ajax_save_score, name="ajax_save_score"),
    # ============================================
    # PERFORMANCE COMMENTS
    # ============================================
    path("comments/", views.comment_list, name="comment_list"),
    path("comments/create/", views.comment_create, name="comment_create"),
    path("comments/<int:pk>/update/", views.comment_update, name="comment_update"),
]
