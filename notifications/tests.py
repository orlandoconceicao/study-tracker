from django.contrib.auth import get_user_model
from datetime import datetime, time, timezone as datetime_timezone
from unittest.mock import patch

from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import UserNotificationSettings
from .services import send_study_reminder
from .tasks import check_study_reminders


class NotificationSettingsTests(APITestCase):
    def test_get_and_patch_settings(self):
        user = get_user_model().objects.create_user("ana", "ana@example.com", "password123")
        self.client.force_authenticate(user)
        self.assertEqual(self.client.get("/api/notifications/settings/").status_code, 200)
        response = self.client.patch("/api/notifications/settings/", {"enabled": True, "reminder_time": "20:00", "timezone": "America/Campo_Grande"})
        self.assertEqual(response.status_code, 200)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEFAULT_FROM_EMAIL="noreply@example.com")
    def test_manual_reminder_is_sent_to_current_user_email(self):
        user = get_user_model().objects.create_user("ana", "ana@example.com", "password123")
        self.assertEqual(send_study_reminder(user), 1)
        self.assertEqual(mail.outbox[0].to, ["ana@example.com"])

    @patch("notifications.tasks.send_study_reminder")
    @patch("notifications.tasks.timezone.now")
    def test_task_sends_once_per_day(self, mocked_now, mocked_send):
        mocked_now.return_value = datetime(2026, 8, 8, 20, 0, tzinfo=datetime_timezone.utc)
        user = get_user_model().objects.create_user("ana", "ana@example.com", "password123")
        setting = UserNotificationSettings.objects.create(user=user, enabled=True, reminder_time=time(20, 0), timezone="UTC")
        check_study_reminders()
        setting.refresh_from_db()
        self.assertTrue(mocked_send.called)
        self.assertEqual(setting.last_reminder_sent.isoformat(), "2026-08-08")
        check_study_reminders()
        self.assertEqual(mocked_send.call_count, 1)

    @patch("notifications.tasks.send_study_reminder")
    @patch("notifications.tasks.timezone.now")
    def test_disabled_or_missing_email_never_sends(self, mocked_now, mocked_send):
        mocked_now.return_value = datetime(2026, 8, 8, 20, 0, tzinfo=datetime_timezone.utc)
        disabled_user = get_user_model().objects.create_user("ana", "ana@example.com", "password123")
        no_email_user = get_user_model().objects.create_user("bia", "bia@example.com", "password123")
        no_email_user.email = ""
        no_email_user.save()
        UserNotificationSettings.objects.create(user=disabled_user, enabled=False, reminder_time=time(20, 0), timezone="UTC")
        UserNotificationSettings.objects.create(user=no_email_user, enabled=True, reminder_time=time(20, 0), timezone="UTC")
        check_study_reminders()
        mocked_send.assert_not_called()
