from django.contrib import admin

from .models import UserNotificationSettings


@admin.register(UserNotificationSettings)
class UserNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "enabled",
        "reminder_time",
        "timezone",
    )

    list_filter = (
        "enabled",
        "timezone",
    )

    search_fields = (
        "user__username",
        "user__email",
    )