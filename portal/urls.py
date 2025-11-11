from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    # ============================================
    # MAIN DASHBOARD (Redirects users)
    # ============================================
    path("", views.portal_dashboard, name="dashboard"),
    # ============================================
    # PARENT INVITATION
    # ============================================
    path(
        "invitation/accept/<uuid:token>/", views.accept_invitation, name="accept_invitation"
    ),
    # ============================================
    # PARENT PORTAL
    # ============================================
    path("parent/dashboard/", views.parent_dashboard, name="parent_dashboard"),
    path(
        "parent/student/<int:student_id>/",
        views.parent_student_detail,
        name="parent_student_detail",
    ),
    path(
        "parent/student/<int:student_id>/scores/",
        views.parent_student_scores,
        name="parent_student_scores",
    ),
    path(
        "parent/student/<int:student_id>/attendance/",
        views.parent_student_attendance,
        name="parent_student_attendance",
    ),
    path(
        "parent/student/<int:student_id>/report-cards/",
        views.parent_student_reports,
        name="parent_student_reports",
    ),
    path(
        "parent/student/<int:student_id>/timetable/",
        views.parent_timetable,
        name="parent_timetable",
    ),
    path("parent/fees/", views.parent_fees, name="parent_fees"),
    # ============================================
    # STUDENT PORTAL
    # ============================================
    # ============================================
    # TEACHER PORTAL
    # ============================================
    path("teacher/dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("student/scores/", views.student_scores, name="student_scores"),
    path("student/attendance/", views.student_attendance, name="student_attendance"),
    path("student/timetable/", views.student_timetable, name="student_timetable"),
    path("student/report-cards/", views.student_reports, name="student_reports"),
    # ============================================
    # ANNOUNCEMENTS
    # ============================================
    path("announcements/", views.announcements_list, name="announcements_list"),
    path(
        "announcements/<int:pk>/", views.announcement_detail, name="announcement_detail"
    ),
    # ============================================
    # MESSAGES
    # ============================================
    path("messages/", views.messages_inbox, name="messages_inbox"),
    path("messages/compose/", views.compose_message, name="compose_message"),
    path("messages/<int:pk>/", views.message_detail, name="message_detail"),
    path("messages/<int:pk>/reply/", views.reply_message, name="reply_message"),
    # ============================================
    # PROFILE
    # ============================================
    path("profile/", views.portal_profile, name="profile"),
    path("profile/update/", views.update_profile, name="update_profile"),
    path("profile/change-password/", views.change_password, name="change_password"),
]
