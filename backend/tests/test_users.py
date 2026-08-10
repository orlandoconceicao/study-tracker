import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken

from users.serializers import RegisterSerializer, UserSerializer


pytestmark = pytest.mark.django_db


def test_register_hashes_password_and_never_returns_it(api_client):
    response = api_client.post(
        "/api/auth/register/",
        {"username": "ana", "email": "ana@example.com", "password": "password123"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert "password" not in response.data
    assert get_user_model().objects.get(username="ana").check_password("password123")


@pytest.mark.parametrize(
    "payload,field",
    [
        ({"username": "ana", "email": "ana@example.com", "password": "short"}, "password"),
        ({"username": "ana", "email": "invalid", "password": "password123"}, "email"),
    ],
)
def test_register_rejects_invalid_payloads(api_client, payload, field):
    response = api_client.post("/api/auth/register/", payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert field in response.data


def test_register_rejects_duplicate_email(api_client, user):
    response = api_client.post(
        "/api/auth/register/",
        {"username": "other", "email": user.email, "password": "password123"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_and_refresh_return_valid_tokens(api_client, user):
    login = api_client.post(
        "/api/auth/login/", {"username": user.username, "password": "password123"}
    )
    assert login.status_code == status.HTTP_200_OK
    AccessToken(login.data["access"])
    refreshed = api_client.post("/api/auth/refresh/", {"refresh": login.data["refresh"]})
    assert refreshed.status_code == status.HTTP_200_OK
    AccessToken(refreshed.data["access"])


def test_login_rejects_wrong_password(api_client, user):
    response = api_client.post(
        "/api/auth/login/", {"username": user.username, "password": "wrong"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("path", ["/api/auth/me/", "/api/studies/", "/api/notifications/settings/"])
def test_private_endpoints_reject_anonymous_requests(api_client, path):
    assert api_client.get(path).status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_token_is_rejected(api_client):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
    assert api_client.get("/api/auth/me/").status_code == status.HTTP_401_UNAUTHORIZED


def test_me_returns_only_public_profile_fields(authenticated_client, user):
    response = authenticated_client.get("/api/auth/me/")
    assert response.status_code == status.HTTP_200_OK
    assert set(response.data) == {"id", "username", "email", "first_name", "last_name", "date_joined", "last_login"}
    assert response.data["id"] == user.id


def test_me_update_is_case_insensitive_for_duplicate_email(authenticated_client, other_user):
    response = authenticated_client.patch("/api/auth/me/", {"email": other_user.email.upper()})
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email" in response.data


def test_serializers_enforce_password_and_email_rules(user):
    assert not RegisterSerializer(data={"username": "x", "email": "x@example.com", "password": "123"}).is_valid()
    serializer = UserSerializer(user, data={"email": user.email.upper()}, partial=True)
    assert serializer.is_valid(), serializer.errors


def test_named_routes_resolve():
    assert reverse("schema") == "/api/schema/"


def test_me_updates_names_and_rejects_administrative_fields(authenticated_client, user):
    response = authenticated_client.patch("/api/auth/me/", {"username": "ana_atualizada", "email": "ana.nova@example.com", "first_name": "Ana", "last_name": "Silva", "is_staff": True})
    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert (user.username, user.email, user.first_name, user.last_name, user.is_staff) == ("ana_atualizada", "ana.nova@example.com", "Ana", "Silva", False)


def test_change_password_checks_current_password(authenticated_client, user):
    wrong = authenticated_client.post("/api/auth/change-password/", {"current_password": "errada", "new_password": "nova-senha-123", "confirm_password": "nova-senha-123"})
    assert wrong.status_code == status.HTTP_400_BAD_REQUEST
    valid = authenticated_client.post("/api/auth/change-password/", {"current_password": "password123", "new_password": "nova-senha-123", "confirm_password": "nova-senha-123"})
    assert valid.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.check_password("nova-senha-123")


def test_preferences_are_persistent_and_isolated(authenticated_client, api_client, user, other_user):
    response = authenticated_client.patch("/api/users/preferences/", {"theme": "dark", "daily_study_goal_minutes": 90})
    assert response.status_code == status.HTTP_200_OK
    assert response.data["daily_study_goal_minutes"] == 90
    api_client.force_authenticate(other_user)
    assert api_client.get("/api/users/preferences/").data["theme"] == "system"


def test_account_deletion_requires_password_and_confirmation(authenticated_client, user):
    invalid = authenticated_client.delete("/api/auth/account/", {"current_password": "password123", "confirmation": "excluir"}, format="json")
    assert invalid.status_code == status.HTTP_400_BAD_REQUEST
    valid = authenticated_client.delete("/api/auth/account/", {"current_password": "password123", "confirmation": "EXCLUIR MINHA CONTA"}, format="json")
    assert valid.status_code == status.HTTP_204_NO_CONTENT
    user.refresh_from_db()
    assert user.is_active is False
