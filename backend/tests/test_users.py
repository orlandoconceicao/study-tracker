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
    assert set(response.data) == {"id", "username", "email", "date_joined"}
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
