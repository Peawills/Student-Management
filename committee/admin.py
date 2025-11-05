from django.contrib import admin
from .models import StudentOffense, TeacherReport

@admin.register(StudentOffense)
class StudentOffenseAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'offense_date', 'event_type', 'sanction')
    search_fields = ('student_name', 'offense_description')

@admin.register(TeacherReport)
class TeacherReportAdmin(admin.ModelAdmin):
    list_display = ('teacher_name', 'offense', 'report_date')
    search_fields = ('teacher_name',)

