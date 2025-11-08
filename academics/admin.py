# academics/admin.py

from django.contrib import admin
from django.db.models import Avg, Count
from .models import (
    AcademicSession,
    Term,
    Subject,
    ClassRoom,
    SubjectAssignment,
    AssessmentType,
    Assessment,
    StudentScore,
    TermResult,
    ReportCard,
    PerformanceComment,
)


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date", "is_current"]
    list_filter = ["is_current"]
    search_fields = ["name"]
    ordering = ["-start_date"]

    def save_model(self, request, obj, form, change):
        # If setting this as current, unset all others
        if obj.is_current:
            AcademicSession.objects.filter(is_current=True).update(is_current=False)
        super().save_model(request, obj, form, change)


@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ["name", "session", "start_date", "end_date", "is_current"]
    list_filter = ["session", "name", "is_current"]
    search_fields = ["name", "session__name"]
    ordering = ["-session__start_date", "name"]

    def save_model(self, request, obj, form, change):
        # If setting this as current, unset all others in same session
        if obj.is_current:
            Term.objects.filter(session=obj.session, is_current=True).update(
                is_current=False
            )
        super().save_model(request, obj, form, change)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "is_core"]
    list_filter = ["is_core"]
    search_fields = ["name", "code"]
    ordering = ["name"]


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ["__str__", "session", "class_teacher", "get_student_count"]
    list_filter = ["session", "level", "arm"]
    search_fields = ["level", "arm", "class_teacher__username"]
    ordering = ["session", "level", "arm"]

    def get_student_count(self, obj):
        from records.models import Student

        return Student.objects.filter(class_at_present=str(obj)).count()

    get_student_count.short_description = "Students"


@admin.register(SubjectAssignment)
class SubjectAssignmentAdmin(admin.ModelAdmin):
    list_display = ["classroom", "subject", "teacher", "term"]
    list_filter = ["term", "classroom", "subject"]
    search_fields = ["classroom__level", "subject__name", "teacher__username"]
    ordering = ["-term__session__start_date", "classroom__level"]
    raw_id_fields = ["teacher"]


@admin.register(AssessmentType)
class AssessmentTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "weight", "max_score"]
    search_fields = ["name", "code"]
    ordering = ["weight"]


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "get_subject",
        "get_class",
        "assessment_type",
        "date",
        "max_score",
        "created_by",
    ]
    list_filter = ["assessment_type", "date", "assignment__term"]
    search_fields = [
        "title",
        "assignment__subject__name",
        "assignment__classroom__level",
    ]
    ordering = ["-date"]
    raw_id_fields = ["assignment", "created_by"]

    def get_subject(self, obj):
        return obj.assignment.subject.name

    get_subject.short_description = "Subject"

    def get_class(self, obj):
        return str(obj.assignment.classroom)

    get_class.short_description = "Class"


@admin.register(StudentScore)
class StudentScoreAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "get_assessment",
        "score",
        "percentage",
        "grade",
        "submitted_by",
        "submitted_at",
    ]
    list_filter = ["assessment__assessment_type", "submitted_at"]
    search_fields = ["student__surname", "student__other_name", "assessment__title"]
    ordering = ["-submitted_at"]
    raw_id_fields = ["assessment", "student", "submitted_by"]
    readonly_fields = ["submitted_at", "updated_at"]

    def get_assessment(self, obj):
        return obj.assessment.title

    get_assessment.short_description = "Assessment"


@admin.register(TermResult)
class TermResultAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "subject",
        "term",
        "classroom",
        "ca_total",
        "exam_score",
        "total_score",
        "grade",
        "position",
    ]
    list_filter = ["term", "classroom", "subject", "grade"]
    search_fields = ["student__surname", "student__other_name", "subject__name"]
    ordering = ["-term__session__start_date", "classroom__level", "-total_score"]
    raw_id_fields = ["student", "subject", "classroom"]
    readonly_fields = ["total_score", "grade"]

    fieldsets = (
        ("Basic Information", {"fields": ("student", "subject", "term", "classroom")}),
        (
            "Scores",
            {"fields": ("ca_total", "exam_score", "total_score", "grade", "position")},
        ),
        ("Statistics", {"fields": ("class_average", "highest_score", "lowest_score")}),
        ("Remarks", {"fields": ("teacher_remarks",)}),
    )


@admin.register(ReportCard)
class ReportCardAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "term",
        "classroom",
        "average_score",
        "position",
        "out_of",
        "is_published",
        "published_at",
    ]
    list_filter = ["term", "classroom", "is_published"]
    search_fields = ["student__surname", "student__other_name"]
    ordering = ["-term__session__start_date", "position"]
    raw_id_fields = ["student", "classroom"]
    readonly_fields = ["generated_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("student", "term", "classroom")}),
        (
            "Performance",
            {"fields": ("total_score", "average_score", "position", "out_of")},
        ),
        ("Attendance", {"fields": ("days_present", "days_absent")}),
        ("Remarks", {"fields": ("class_teacher_remarks", "principal_remarks")}),
        ("Publishing", {"fields": ("is_published", "published_at", "generated_at")}),
    )

    actions = ["publish_report_cards", "unpublish_report_cards"]

    def publish_report_cards(self, request, queryset):
        from django.utils import timezone

        count = queryset.update(is_published=True, published_at=timezone.now())
        self.message_user(request, f"{count} report cards published successfully.")

    publish_report_cards.short_description = "Publish selected report cards"

    def unpublish_report_cards(self, request, queryset):
        count = queryset.update(is_published=False, published_at=None)
        self.message_user(request, f"{count} report cards unpublished successfully.")

    unpublish_report_cards.short_description = "Unpublish selected report cards"


@admin.register(PerformanceComment)
class PerformanceCommentAdmin(admin.ModelAdmin):
    list_display = ["get_short_text", "category", "is_active"]
    list_filter = ["category", "is_active"]
    search_fields = ["text"]
    ordering = ["category", "text"]

    def get_short_text(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text

    get_short_text.short_description = "Comment"


# Inline admin classes for better management
class SubjectAssignmentInline(admin.TabularInline):
    model = SubjectAssignment
    extra = 1
    raw_id_fields = ["teacher"]


class StudentScoreInline(admin.TabularInline):
    model = StudentScore
    extra = 0
    readonly_fields = ["percentage", "grade"]
    fields = ["student", "score", "percentage", "grade", "remarks"]


# Register inline with Assessment
class AssessmentWithScoresAdmin(AssessmentAdmin):
    inlines = [StudentScoreInline]


# Unregister and re-register with inlines
admin.site.unregister(Assessment)
admin.site.register(Assessment, AssessmentWithScoresAdmin)
