from django.contrib import admin

from .models import Study


@admin.register(Study)
class StudyAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "date",
        "duration_minutes",
        "subject",
        "created_at",
    )

    list_filter = (
        "date",
    )

    search_fields = (
        "subject",
        "notes",
        "user__username",
        "user__email",
    )

    ordering = (
        "-date",
        "-created_at",
    )