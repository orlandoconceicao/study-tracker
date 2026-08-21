from rest_framework.routers import DefaultRouter
from django.urls import path

from .views import (AssignmentViewSet, ClassroomViewSet, DiagnosticAssessmentViewSet,
                    EducationLevelViewSet, EducationProfileViewSet, QuestionBankViewSet,
                    StudentAssignmentViewSet,
                    ExerciseViewSet, GradeViewSet, LessonViewSet, ProgressViewSet,
                    SubjectViewSet, TopicViewSet)

router = DefaultRouter()
router.register("levels", EducationLevelViewSet, basename="education-level")
router.register("grades", GradeViewSet, basename="education-grade")
router.register("subjects", SubjectViewSet, basename="education-subject")
router.register("topics", TopicViewSet, basename="education-topic")
router.register("lessons", LessonViewSet, basename="education-lesson")
router.register("exercises", ExerciseViewSet, basename="education-exercise")
router.register("progress", ProgressViewSet, basename="education-progress")
router.register("classrooms", ClassroomViewSet, basename="education-classroom")
router.register("diagnostics", DiagnosticAssessmentViewSet, basename="education-diagnostic")
router.register("questions", QuestionBankViewSet, basename="education-question-bank")
router.register("assignments", AssignmentViewSet, basename="education-assignment")
router.register("student-assignments", StudentAssignmentViewSet, basename="education-student-assignment")

profile_view = EducationProfileViewSet.as_view({"get": "list", "patch": "partial_update"})
urlpatterns = [path("profile/", profile_view, name="education-profile")] + router.urls
