from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import UserPreferences
from .serializers import ChangePasswordSerializer, DeleteAccountSerializer, RegisterSerializer, UserPreferencesSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def get(self, request):
        return Response(self.get_serializer(request.user).data)

    def patch(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])
        return Response({"detail": "Senha alterada com sucesso."})


class PreferencesView(generics.RetrieveUpdateAPIView):
    serializer_class = UserPreferencesSerializer

    def get_object(self):
        preferences, _ = UserPreferences.objects.get_or_create(user=self.request.user)
        return preferences


class AccountView(generics.GenericAPIView):
    serializer_class = DeleteAccountSerializer

    def delete(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.is_active = False
        request.user.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)
