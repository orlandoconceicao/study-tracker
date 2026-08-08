from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase


class AuthenticationTests(APITestCase):
    def test_register_login_and_me(self):
        response = self.client.post("/api/auth/register/", {"username": "ana", "email": "ana@example.com", "password": "password123"})
        self.assertEqual(response.status_code, 201)
        token = self.client.post("/api/auth/login/", {"username": "ana", "password": "password123"}).json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)

    def test_authenticated_user_can_update_only_own_profile(self):
        user = get_user_model().objects.create_user("ana", "ana@example.com", "password123")
        self.client.force_authenticate(user)
        response = self.client.patch("/api/auth/me/", {"username": "ana_nova", "email": "nova@example.com"})
        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.assertEqual(user.username, "ana_nova")
        self.assertEqual(user.email, "nova@example.com")

    def test_profile_rejects_duplicate_email(self):
        get_user_model().objects.create_user("ana", "ana@example.com", "password123")
        user = get_user_model().objects.create_user("bia", "bia@example.com", "password123")
        self.client.force_authenticate(user)
        response = self.client.patch("/api/auth/me/", {"email": "ana@example.com"})
        self.assertEqual(response.status_code, 400)
