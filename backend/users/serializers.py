from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()
from .models import UserPreferences


class UserSerializer(serializers.ModelSerializer):
    def validate_email(self, value):
        if User.objects.exclude(pk=self.instance.pk if self.instance else None).filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este e-mail já está em uso.")
        return value

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "date_joined", "last_login")
        read_only_fields = ("id", "date_joined", "last_login")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("A senha atual está incorreta.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "As senhas não coincidem."})
        validate_password(attrs["new_password"], self.context["request"].user)
        return attrs


class DeleteAccountSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    confirmation = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("A senha atual está incorreta.")
        return value

    def validate_confirmation(self, value):
        if value != "EXCLUIR MINHA CONTA":
            raise serializers.ValidationError('Digite "EXCLUIR MINHA CONTA" para confirmar.')
        return value


class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = ("theme", "language", "daily_study_goal_minutes")

    def validate_daily_study_goal_minutes(self, value):
        if not 1 <= value <= 1440:
            raise serializers.ValidationError("Informe uma meta entre 1 e 1440 minutos.")
        return value
