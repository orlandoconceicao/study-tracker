from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("notifications", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="usernotificationsettings",
            name="last_reminder_sent",
            field=models.DateField(blank=True, null=True),
        ),
    ]
