from django.conf import settings
from django.core.mail import send_mail


def send_study_reminder(user):
    """Send the daily reminder to the e-mail currently stored on the user."""
    subject = "Study Tracker — Hora de estudar"
    message = (
        f"Olá, {user.username}!\n\n"
        "Está na hora do seu estudo de hoje.\n\n"
        "Reserve alguns minutos para manter sua sequência e continuar evoluindo.\n\n"
        "Bons estudos!\n\nStudy Tracker"
    )
    html_message = (
        f"<p>Olá, {user.username}!</p>"
        "<p>Está na hora do seu estudo de hoje.</p>"
        "<p>Reserve alguns minutos para manter sua sequência e continuar evoluindo.</p>"
        "<p>Bons estudos!<br>Study Tracker</p>"
    )
    return send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )
