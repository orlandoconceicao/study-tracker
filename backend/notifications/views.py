from rest_framework import generics
from .models import UserNotificationSettings
from .serializers import UserNotificationSettingsSerializer


class NotificationSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserNotificationSettingsSerializer

    def get_object(self):
        instance, _ = UserNotificationSettings.objects.get_or_create(user=self.request.user)
        return instance
