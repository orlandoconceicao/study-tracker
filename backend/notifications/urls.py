from django.urls import path
from .views import NotificationSettingsView, TestReminderView

urlpatterns = [
    path("settings/", NotificationSettingsView.as_view()),
    path("test/", TestReminderView.as_view()),
]
