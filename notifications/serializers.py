from rest_framework import serializers
from .models import UserNotificationSettings


class UserNotificationSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserNotificationSettings
        fields = ("enabled", "reminder_time", "timezone")

    def validate(self, attrs):
        if attrs.get("enabled", self.instance.enabled if self.instance else False) and not attrs.get("reminder_time", self.instance.reminder_time if self.instance else None):
            raise serializers.ValidationError({"reminder_time": "Required when enabled."})
        return attrs
