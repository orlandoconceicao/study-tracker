from rest_framework import serializers
from .models import Study


class StudySerializer(serializers.ModelSerializer):
    child_name = serializers.CharField(source="child.name", read_only=True)

    class Meta:
        model = Study
        fields = ("id", "child", "child_name", "date", "duration_minutes", "subject", "notes", "created_at", "updated_at")
        read_only_fields = ("id", "child_name", "created_at", "updated_at")

    def validate_child(self, value):
        request = self.context.get("request")
        if value and request and value.parent_id != request.user.id:
            raise serializers.ValidationError("Filho não encontrado.")
        return value
