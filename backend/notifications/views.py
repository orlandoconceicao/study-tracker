from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import UserNotificationSettings
from .serializers import UserNotificationSettingsSerializer
from .services import send_study_reminder


class NotificationSettingsView(generics.RetrieveUpdateAPIView):
    serializer_class = UserNotificationSettingsSerializer

    def get_object(self):
        instance, _ = UserNotificationSettings.objects.get_or_create(user=self.request.user)
        return instance


class TestReminderView(APIView):
    def post(self, request):
        if not request.user.email:
            return Response({"detail": "Cadastre um e-mail na sua conta antes de testar."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            sent = send_study_reminder(request.user)
        except Exception:
            return Response({"detail": "Não foi possível enviar o e-mail. Verifique a configuração SMTP."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if not sent:
            return Response({"detail": "O servidor de e-mail não confirmou o envio."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"detail": "E-mail de teste enviado com sucesso."})
