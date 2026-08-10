from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Study(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="studies")
    child = models.ForeignKey("education.Child", on_delete=models.SET_NULL, related_name="studies", blank=True, null=True)
    date = models.DateField(db_index=True)
    duration_minutes = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    subject = models.CharField(max_length=255, db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-date", "-created_at")
        indexes = [models.Index(fields=("user", "date"))]
