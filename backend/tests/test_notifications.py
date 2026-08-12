from datetime import datetime, time, timezone as datetime_timezone
from unittest.mock import patch

import pytest
from django.core import mail
from rest_framework import status

from notifications.models import UserNotificationSettings
from notifications.serializers import UserNotificationSettingsSerializer
from notifications.services import send_study_reminder
from notifications.tasks import check_study_reminders


pytestmark = pytest.mark.django_db


def test_settings_get_creates_one_record_and_is_user_scoped(authenticated_client, user, other_user):
    foreign = UserNotificationSettings.objects.create(user=other_user, enabled=True, reminder_time=time(9))
    first = authenticated_client.get("/api/notifications/settings/")
    second = authenticated_client.get("/api/notifications/settings/")
    assert first.status_code == second.status_code == status.HTTP_200_OK
    assert UserNotificationSettings.objects.filter(user=user).count() == 1
    assert first.data["enabled"] is False
    foreign.refresh_from_db()
    assert foreign.enabled is True


def test_enabling_reminder_requires_time(authenticated_client):
    response = authenticated_client.patch(
        "/api/notifications/settings/",
        {"enabled": True, "reminder_time": None},
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "reminder_time" in response.data


def test_disabling_reminder_does_not_require_time(authenticated_client):
    response = authenticated_client.patch(
        "/api/notifications/settings/",
        {"enabled": False, "reminder_time": None},
        format="json",
    )
    assert response.status_code == status.HTTP_200_OK


def test_serializer_does_not_expose_internal_delivery_state(user):
    setting = UserNotificationSettings.objects.create(user=user)
    assert set(UserNotificationSettingsSerializer(setting).data) == {"enabled", "reminder_time", "timezone"}


def test_send_reminder_uses_current_email_and_html(user):
    assert send_study_reminder(user) == 1
    message = mail.outbox[0]
    assert message.to == [user.email]
    assert message.from_email == "tests@example.com"
    assert message.alternatives[0][1] == "text/html"


@patch("notifications.tasks.send_study_reminder")
@patch("notifications.tasks.timezone.now")
def test_task_obeys_user_timezone(mock_now, mock_send, user):
    mock_now.return_value = datetime(2026, 8, 8, 23, 0, tzinfo=datetime_timezone.utc)
    setting = UserNotificationSettings.objects.create(
        user=user, enabled=True, reminder_time=time(19), timezone="America/Cuiaba"
    )
    check_study_reminders()
    setting.refresh_from_db()
    mock_send.assert_called_once_with(user)
    assert setting.last_reminder_sent.isoformat() == "2026-08-08"


@patch("notifications.tasks.send_study_reminder")
@patch("notifications.tasks.timezone.now")
def test_task_skips_future_time_and_invalid_timezone(mock_now, mock_send, user, other_user):
    mock_now.return_value = datetime(2026, 8, 8, 20, 0, tzinfo=datetime_timezone.utc)
    UserNotificationSettings.objects.create(user=user, enabled=True, reminder_time=time(21), timezone="UTC")
    UserNotificationSettings.objects.create(user=other_user, enabled=True, reminder_time=time(20), timezone="Invalid/Zone")
    check_study_reminders()
    mock_send.assert_not_called()


@patch("notifications.tasks.send_study_reminder")
@patch("notifications.tasks.timezone.now")
def test_task_sends_missed_reminder_when_scheduler_returns_later(mock_now, mock_send, user):
    mock_now.return_value = datetime(2026, 8, 8, 20, 30, tzinfo=datetime_timezone.utc)
    setting = UserNotificationSettings.objects.create(user=user, enabled=True, reminder_time=time(19), timezone="UTC")
    check_study_reminders()
    setting.refresh_from_db()
    mock_send.assert_called_once_with(user)
    assert setting.last_reminder_sent.isoformat() == "2026-08-08"


@patch("notifications.views.send_study_reminder", return_value=1)
def test_authenticated_user_can_send_test_email(mock_send, authenticated_client, user):
    response = authenticated_client.post("/api/notifications/test/")
    assert response.status_code == status.HTTP_200_OK
    mock_send.assert_called_once_with(user)


@patch("notifications.tasks.send_study_reminder", side_effect=RuntimeError("SMTP unavailable"))
@patch("notifications.tasks.timezone.now")
def test_task_does_not_mark_failed_delivery_as_sent(mock_now, mock_send, user):
    mock_now.return_value = datetime(2026, 8, 8, 20, 0, tzinfo=datetime_timezone.utc)
    setting = UserNotificationSettings.objects.create(user=user, enabled=True, reminder_time=time(20), timezone="UTC")
    check_study_reminders()
    setting.refresh_from_db()
    assert setting.last_reminder_sent is None
