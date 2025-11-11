from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import ParentProfile, StudentProfile, Announcement


# Inlines to show profiles directly on the User page
class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = "Student Profile"
    fk_name = "user"


class ParentProfileInline(admin.StackedInline):
    model = ParentProfile
    can_delete = False
    verbose_name_plural = "Parent Profile"
    fk_name = "user"


# Extend the default User admin
class CustomUserAdmin(BaseUserAdmin):
    inlines = (StudentProfileInline, ParentProfileInline)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)


# Re-register UserAdmin if it's not already done
if User in admin.site._registry:
    admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(ParentProfile)
class ParentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "relationship")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone_number")
    # Use a filter_horizontal for a better UI for ManyToMany fields
    filter_horizontal = ("students",)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "target_audience", "created_by", "created_at", "is_active")
    list_filter = ("category", "target_audience", "is_active", "is_urgent")
    search_fields = ("title", "content")
    raw_id_fields = ("created_by",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
