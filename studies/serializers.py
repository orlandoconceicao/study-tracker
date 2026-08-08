from rest_framework import serializers
from .models import Study


class StudySerializer(serializers.ModelSerializer):
    class Meta:
        model = Study
        fields = ("id", "date", "duration_minutes", "subject", "notes", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
