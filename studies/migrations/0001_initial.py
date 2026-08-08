from django.conf import settings
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.CreateModel(name="Study", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("date", models.DateField(db_index=True)), ("duration_minutes", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)])),
        ("subject", models.CharField(db_index=True, max_length=255)), ("notes", models.TextField(blank=True)),
        ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
        ("user", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="studies", to=settings.AUTH_USER_MODEL)),
    ], options={"ordering": ("-date", "-created_at")})]
