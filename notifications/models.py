from django.conf import settings
from django.db import models


class UserNotificationSettings(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_settings")
    enabled = models.BooleanField(default=False)
    reminder_time = models.TimeField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="America/Cuiaba")
    last_reminder_sent = models.DateField(null=True, blank=True)
