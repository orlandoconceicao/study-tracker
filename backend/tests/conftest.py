from datetime import date

import factory
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from studies.models import Study


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Sequence(lambda number: f"user{number}")
    email = factory.LazyAttribute(lambda user: f"{user.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "password123")


class StudyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Study

    user = factory.SubFactory(UserFactory)
    date = date(2026, 8, 8)
    duration_minutes = 60
    subject = factory.Sequence(lambda number: f"Subject {number}")
    notes = ""


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def other_user(db):
    return UserFactory()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user)
    return api_client
