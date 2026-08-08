from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import status

from studies.models import Study
from studies.permissions import IsStudyOwner
from studies.serializers import StudySerializer
from studies.services import calendar_summary, study_statistics
from tests.conftest import StudyFactory


pytestmark = pytest.mark.django_db


def test_model_orders_newest_studies_first(user):
    older = StudyFactory(user=user, date=date(2026, 8, 1))
    newer = StudyFactory(user=user, date=date(2026, 8, 2))
    assert list(Study.objects.values_list("id", flat=True)) == [newer.id, older.id]


def test_model_rejects_zero_duration_when_validated(user):
    study = StudyFactory.build(user=user, duration_minutes=0)
    with pytest.raises(DjangoValidationError):
        study.full_clean()


def test_serializer_rejects_zero_duration_and_missing_subject():
    serializer = StudySerializer(data={"date": "2026-08-08", "duration_minutes": 0, "subject": ""})
    assert not serializer.is_valid()
    assert {"duration_minutes", "subject"} <= serializer.errors.keys()


def test_create_assigns_authenticated_owner(authenticated_client, user):
    response = authenticated_client.post(
        "/api/studies/",
        {"date": "2026-08-08", "duration_minutes": 45, "subject": "Django", "notes": "API"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert Study.objects.get(pk=response.data["id"]).user == user
    assert "user" not in response.data


def test_crud_and_filters_are_scoped_to_current_user(authenticated_client, user, other_user):
    own = StudyFactory(user=user, subject="Python", date=date(2026, 8, 8))
    StudyFactory(user=user, subject="Math", date=date(2026, 7, 1))
    foreign = StudyFactory(user=other_user, subject="Python", date=date(2026, 8, 8))

    response = authenticated_client.get("/api/studies/?subject=py&start_date=2026-08-01&end_date=2026-08-31")
    assert [item["id"] for item in response.data] == [own.id]
    assert authenticated_client.get(f"/api/studies/{foreign.id}/").status_code == status.HTTP_404_NOT_FOUND
    assert authenticated_client.patch(f"/api/studies/{foreign.id}/", {"subject": "Hacked"}).status_code == status.HTTP_404_NOT_FOUND
    assert authenticated_client.delete(f"/api/studies/{foreign.id}/").status_code == status.HTTP_404_NOT_FOUND


def test_owner_can_update_and_delete_study(authenticated_client, user):
    study = StudyFactory(user=user)
    updated = authenticated_client.patch(f"/api/studies/{study.id}/", {"subject": "Updated"})
    assert updated.status_code == status.HTTP_200_OK
    assert updated.data["subject"] == "Updated"
    assert authenticated_client.delete(f"/api/studies/{study.id}/").status_code == status.HTTP_204_NO_CONTENT
    assert not Study.objects.filter(pk=study.id).exists()


@pytest.mark.parametrize("query", ["month=0&year=2026", "month=13&year=2026", "month=x&year=2026", "month=8&year=x"])
def test_calendar_rejects_invalid_parameters(authenticated_client, query):
    response = authenticated_client.get(f"/api/studies/calendar/?{query}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_calendar_summary_fills_every_day_and_sums_sessions(user, other_user):
    StudyFactory(user=user, date=date(2024, 2, 10), duration_minutes=30)
    StudyFactory(user=user, date=date(2024, 2, 10), duration_minutes=45)
    StudyFactory(user=other_user, date=date(2024, 2, 10), duration_minutes=999)
    summary = calendar_summary(user, 2, 2024)
    assert len(summary) == 29
    assert summary["2024-02-10"] == {"studied": True, "total_minutes": 75}
    assert summary["2024-02-11"] == {"studied": False, "total_minutes": 0}


def test_statistics_calculates_totals_streaks_week_and_month(user, other_user, monkeypatch):
    today = date(2026, 8, 8)
    monkeypatch.setattr(timezone, "localdate", lambda: today)
    for day, minutes in [(today - timedelta(days=3), 30), (today - timedelta(days=2), 60), (today - timedelta(days=1), 90), (today, 120)]:
        StudyFactory(user=user, date=day, duration_minutes=minutes)
    StudyFactory(user=other_user, date=today, duration_minutes=999)
    result = study_statistics(user)
    assert result == {
        "total_hours": 5.0,
        "total_studied_days": 4,
        "average_minutes_per_day": 75,
        "week_minutes": 300,
        "month_minutes": 300,
        "current_streak": 4,
        "best_streak": 4,
    }


def test_statistics_for_empty_user_returns_zeroes(user):
    assert study_statistics(user) == {
        "total_hours": 0.0,
        "total_studied_days": 0,
        "average_minutes_per_day": 0,
        "week_minutes": 0,
        "month_minutes": 0,
        "current_streak": 0,
        "best_streak": 0,
    }


def test_permission_allows_only_owner(user, other_user):
    permission = IsStudyOwner()
    request = type("Request", (), {"user": user})()
    assert permission.has_object_permission(request, None, StudyFactory.build(user=user))
    assert not permission.has_object_permission(request, None, StudyFactory.build(user=other_user))
