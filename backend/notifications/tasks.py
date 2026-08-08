import logging
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from celery import shared_task
from django.utils import timezone

from .models import UserNotificationSettings
from .services import send_study_reminder

logger = logging.getLogger(__name__)


@shared_task
def check_study_reminders():
    """Send at most one reminder per local day for each enabled setting."""
    for setting in UserNotificationSettings.objects.select_related("user").filter(
        enabled=True,
        reminder_time__isnull=False,
    ):
        if not setting.user.email:
            continue
        try:
            local_now = timezone.now().astimezone(ZoneInfo(setting.timezone))
        except ZoneInfoNotFoundError:
            logger.warning("Fuso horário inválido para o usuário %s", setting.user_id)
            continue
        if (local_now.hour, local_now.minute) != (setting.reminder_time.hour, setting.reminder_time.minute):
            continue
        if setting.last_reminder_sent == local_now.date():
            continue
        try:
            send_study_reminder(setting.user)
        except Exception:
            logger.exception("Não foi possível enviar lembrete para o usuário %s", setting.user_id)
            continue
        setting.last_reminder_sent = local_now.date()
        setting.save(update_fields=("last_reminder_sent",))
