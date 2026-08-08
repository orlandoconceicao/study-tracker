from datetime import date
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from .models import Study


class StudyApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("alice", "alice@example.com", "password123")
        self.other = get_user_model().objects.create_user("bob", "bob@example.com", "password123")
        self.client.force_authenticate(self.user)

    def test_create_filter_and_calendar(self):
        response = self.client.post("/api/studies/", {"date": "2026-08-02", "duration_minutes": 60, "subject": "Python", "notes": "API"})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.client.get("/api/studies/?subject=python").status_code, 200)
        calendar = self.client.get("/api/studies/calendar/?month=8&year=2026").json()
        self.assertEqual(calendar["2026-08-02"]["total_minutes"], 60)

    def test_cannot_access_another_users_study(self):
        study = Study.objects.create(user=self.other, date=date.today(), duration_minutes=20, subject="Math")
        self.assertEqual(self.client.get(f"/api/studies/{study.id}/").status_code, 404)

    def test_statistics(self):
        Study.objects.create(user=self.user, date=date.today(), duration_minutes=90, subject="Math")
        data = self.client.get("/api/studies/statistics/").json()
        self.assertEqual(data["total_hours"], 1.5)
