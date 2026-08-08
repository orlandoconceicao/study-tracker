from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="UserNotificationSettings", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("enabled", models.BooleanField(default=False)), ("reminder_time", models.TimeField(blank=True, null=True)), ("timezone", models.CharField(default="America/Cuiaba", max_length=64)),
        ("user", models.OneToOneField(on_delete=models.deletion.CASCADE, related_name="notification_settings", to=settings.AUTH_USER_MODEL)),
    ])]
