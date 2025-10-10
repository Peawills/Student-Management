from django.contrib import admin
from django.utils.html import format_html
from .models import Student, StudentDocument


class StudentDocumentInline(admin.TabularInline):
    model = StudentDocument
    extra = 1
    fields = ('document_type', 'name', 'file', 'notes', 'preview')
    readonly_fields = ('preview', 'uploaded_at')

    def preview(self, obj):
        """Display image preview in admin"""
        if obj.file and obj.is_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 50px; max-width: 100px;" /></a>',
                obj.file.url,
                obj.file.url
            )
        elif obj.file and obj.is_pdf:
            return format_html(
                '<a href="{}" target="_blank">📄 View PDF</a>',
                obj.file.url
            )
        elif obj.file:
            return format_html(
                '<a href="{}" target="_blank">📎 Download File</a>',
                obj.file.url
            )
        return "No file"
    preview.short_description = "Preview"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_no', 'full_name', 'class_at_present', 'age', 'sex', 'date_of_entry')
    list_filter = ('sex', 'class_at_present', 'nationality', 'state_of_origin')
    search_fields = ('surname', 'other_name', 'admission_no', 'nin_no')
    readonly_fields = ('age', 'created_at', 'updated_at', 'student_image_preview')
    inlines = [StudentDocumentInline]

    fieldsets = (
        ('Personal Information', {
            'fields': (
                ('surname', 'other_name'),
                ('date_of_birth', 'age'),
                ('place_of_birth', 'sex'),
                ('nationality', 'state_of_origin', 'lga'),
                ('religion', 'denomination'),
            )
        }),
        ('Contact Information', {
            'fields': (
                'residential_address',
                'permanent_home_address',
            )
        }),
        ('Admission Details', {
            'fields': (
                ('admission_no', 'nin_no'),
                ('class_on_entry', 'date_of_entry'),
                'class_at_present',
                ('student_image', 'student_image_preview'),
            )
        }),
        ('Father Information', {
            'fields': (
                'father_name',
                'father_address',
                ('father_occupation', 'father_educational_level'),
                'father_mobile',
            ),
            'classes': ('collapse',)
        }),
        ('Mother Information', {
            'fields': (
                'mother_name',
                'mother_address',
                ('mother_occupation', 'mother_educational_level'),
                'mother_mobile',
            ),
            'classes': ('collapse',)
        }),
        ('Guardian Information', {
            'fields': (
                'guardian_name',
                'guardian_address',
                'guardian_occupation',
                'guardian_mobile',
            ),
            'classes': ('collapse',)
        }),
        ('Academic History', {
            'fields': ('prev_schools',),
            'classes': ('collapse',)
        }),
        ('Special Health Status', {
            'fields': (
                'visually_impaired',
                'deaf',
                'physically_disabled',
                'mentally_impaired',
                'others',
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def student_image_preview(self, obj):
        """Display student image preview"""
        if obj.student_image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.student_image.url
            )
        return "No image uploaded"
    student_image_preview.short_description = "Image Preview"


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'student', 'document_type', 'file_size_mb', 'uploaded_at', 'preview')
    list_filter = ('document_type', 'uploaded_at')
    search_fields = ('name', 'student__surname', 'student__admission_no')
    readonly_fields = ('uploaded_at', 'file_size_mb', 'is_image', 'is_pdf', 'preview')

    def preview(self, obj):
        """Display preview in list view"""
        if obj.is_image:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="max-height: 50px;" /></a>',
                obj.file.url,
                obj.file.url
            )
        elif obj.is_pdf:
            return format_html('<a href="{}" target="_blank">📄 PDF</a>', obj.file.url)
        return format_html('<a href="{}" target="_blank">📎 File</a>', obj.file.url)
    preview.short_description = "Preview"