from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (Assignment, Child, Classroom, ClassroomMembership, DiagnosticAssessment, EducationLevel,
                     EducationProfile, Exercise, ExerciseAttempt, Grade, Lesson, LessonProgress,
                     StudentAssignment, Subject, Topic, TopicProgress, Unit)
from .permissions import IsStaffOrReadOnly, education_role
from .serializers import (AssignmentAnswerSerializer, AssignmentSerializer, ChildSerializer, ClassroomActivitySerializer,
                          ClassroomSerializer, DiagnosticAnswerSerializer, DiagnosticAssessmentSerializer,
                          EducationLevelSerializer, EducationProfileSerializer, ExerciseAnswerSerializer, ExerciseSerializer,
                          GradeSerializer, GradeSubjectSerializer, LessonProgressSerializer,
                          JoinClassroomSerializer, LessonSerializer, SubjectSerializer, TopicProgressSerializer,
                          ErrorNotebookSerializer, QuestionBankExerciseSerializer, ReviewQueueSerializer,
                          RecommendationSerializer, StudentAssignmentSerializer, TopicSerializer, UnitSerializer)
from .review_services import error_notebook, review_queue
from .recommendation_service import lesson_plan_for_topic, recommendations_for_user
from .services import (answer_diagnostic, answer_student_assignment, complete_lesson,
                       diagnostic_result, finish_diagnostic, record_attempt,
                       start_diagnostic, start_student_assignment, submit_student_assignment)


def child_for_request(request):
    child_id = request.data.get("child") if hasattr(request, "data") else None
    child_id = child_id or request.query_params.get("child")
    return get_object_or_404(Child, id=child_id, parent=request.user, active=True) if child_id else None


class CurriculumViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated, IsStaffOrReadOnly)


class EducationLevelViewSet(CurriculumViewSet):
    queryset = EducationLevel.objects.all()
    serializer_class = EducationLevelSerializer


class GradeViewSet(CurriculumViewSet):
    queryset = Grade.objects.select_related("education_level")
    serializer_class = GradeSerializer

    @action(detail=True, methods=("get",))
    def subjects(self, request, pk=None):
        links = self.get_object().grade_subjects.select_related("subject").filter(subject__active=True)
        return Response(GradeSubjectSerializer(links, many=True).data)


class ChildViewSet(viewsets.ModelViewSet):
    serializer_class = ChildSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Child.objects.none()
        return Child.objects.filter(parent=self.request.user).select_related("education_level", "grade")

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user)

    @action(detail=True, methods=("get",))
    def subjects(self, request, pk=None):
        child = self.get_object()
        if not child.education_level_id or not child.grade_id:
            return Response({"detail": "Complete o perfil escolar do filho."}, status=status.HTTP_409_CONFLICT)
        links = child.grade.grade_subjects.select_related("subject").filter(subject__active=True)
        return Response(GradeSubjectSerializer(links, many=True).data)

    @action(detail=True, methods=("get",))
    def progress(self, request, pk=None):
        child = self.get_object()
        if not child.grade_id:
            return Response({"detail": "Complete o perfil escolar do filho."}, status=status.HTTP_409_CONFLICT)
        topic_ids = Topic.objects.filter(unit__grade_subject__grade=child.grade).values_list("id", flat=True)
        lesson_ids = Lesson.objects.filter(topic_id__in=topic_ids).values_list("id", flat=True)
        exercise_ids = Exercise.objects.filter(topic_id__in=topic_ids).values_list("id", flat=True)
        progress = TopicProgress.objects.filter(user=request.user, child=child, topic_id__in=topic_ids)
        attempts = ExerciseAttempt.objects.filter(user=request.user, child=child, exercise_id__in=exercise_ids)
        return Response({
            "topics_started": progress.count(),
            "topics_completed": progress.filter(completed=True).count(),
            "lessons_completed": LessonProgress.objects.filter(user=request.user, child=child, lesson_id__in=lesson_ids, completed=True).count(),
            "exercises_attempted": attempts.count(),
            "exercises_correct": attempts.filter(is_correct=True).count(),
            "recent_attempts": [{
                "exercise": item.exercise.statement,
                "topic": item.exercise.topic_id,
                "topic_title": item.exercise.topic.title,
                "correct": item.is_correct,
                "attempted_at": item.attempted_at,
            } for item in attempts.select_related("exercise__topic")[:10]],
        })


class SubjectViewSet(CurriculumViewSet):
    serializer_class = SubjectSerializer

    def get_queryset(self):
        queryset = Subject.objects.all()
        return queryset if self.request.user.is_staff else queryset.filter(active=True)

    @action(detail=True, methods=("get",))
    def units(self, request, pk=None):
        units = Unit.objects.filter(grade_subject__subject=self.get_object()).select_related("grade_subject")
        grade = request.query_params.get("grade")
        if grade:
            units = units.filter(grade_subject__grade_id=grade)
        return Response(UnitSerializer(units, many=True).data)


class TopicViewSet(CurriculumViewSet):
    queryset = Topic.objects.select_related("unit")
    serializer_class = TopicSerializer

    @action(detail=True, methods=("get",))
    def lessons(self, request, pk=None):
        # Progress is observational only: every registered lesson stays available.
        return Response(LessonSerializer(self.get_object().lessons.all(), many=True).data)

    @action(detail=True, methods=("get",))
    def exercises(self, request, pk=None):
        # Attempts and diagnostics never gate practice material.
        exercises = self.get_object().exercises.prefetch_related("choices")
        return Response(ExerciseSerializer(exercises, many=True, context={"request": request}).data)

    @action(detail=True, methods=("post",), url_path="diagnostic/start", permission_classes=(permissions.IsAuthenticated,))
    def diagnostic_start(self, request, pk=None):
        assessment = start_diagnostic(request.user, self.get_object(), child_for_request(request))
        return Response(DiagnosticAssessmentSerializer(assessment, context={"request": request}).data, status=status.HTTP_201_CREATED)


class LessonViewSet(CurriculumViewSet):
    queryset = Lesson.objects.select_related("topic")
    serializer_class = LessonSerializer

    @action(detail=True, methods=("post",), permission_classes=(permissions.IsAuthenticated,))
    def complete(self, request, pk=None):
        progress = complete_lesson(request.user, self.get_object(), child_for_request(request))
        return Response(LessonProgressSerializer(progress).data)


class ExerciseViewSet(CurriculumViewSet):
    queryset = Exercise.objects.select_related("topic", "lesson").prefetch_related("choices")
    serializer_class = ExerciseSerializer

    @extend_schema(request=ExerciseAnswerSerializer)
    @action(detail=True, methods=("post",), permission_classes=(permissions.IsAuthenticated,))
    def answer(self, request, pk=None):
        serializer = ExerciseAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attempt, correct_answer = record_attempt(request.user, self.get_object(), serializer.validated_data["answer"], child_for_request(request))
        return Response({"correct": attempt.is_correct, "correct_answer": correct_answer, "explanation": attempt.exercise.explanation}, status=status.HTTP_201_CREATED)


class ProgressViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = TopicProgressSerializer
    queryset = TopicProgress.objects.none()

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset
        return TopicProgress.objects.filter(user=self.request.user, child=child_for_request(self.request)).select_related("topic")


class EducationProfileViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = EducationProfileSerializer

    def list(self, request):
        profile, _ = EducationProfile.objects.get_or_create(user=request.user)
        return Response(EducationProfileSerializer(profile).data)

    def partial_update(self, request, pk=None):
        profile, _ = EducationProfile.objects.get_or_create(user=request.user)
        serializer = EducationProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ClassroomViewSet(viewsets.ModelViewSet):
    serializer_class = ClassroomSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Classroom.objects.none()
        return Classroom.objects.filter(Q(teacher=self.request.user) | Q(memberships__student=self.request.user)).select_related("teacher", "grade").prefetch_related("students", "activities").annotate(student_count=Count("memberships", distinct=True)).distinct()

    def perform_create(self, serializer):
        if education_role(self.request.user) != EducationProfile.Role.TEACHER:
            self.permission_denied(self.request, message="Apenas professores podem criar turmas.")
        serializer.save(teacher=self.request.user)

    def check_owner(self, classroom):
        if classroom.teacher_id != self.request.user.id:
            self.permission_denied(self.request, message="Somente o professor da turma pode alterá-la.")

    def perform_update(self, serializer):
        self.check_owner(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self.check_owner(instance)
        instance.delete()

    @extend_schema(operation_id="education_classrooms_join_by_code", request=JoinClassroomSerializer)
    @action(detail=False, methods=("post",), url_path="join")
    def join_by_code(self, request):
        serializer = JoinClassroomSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        classroom = get_object_or_404(Classroom, code=serializer.validated_data["code"], active=True)
        return self._join(request, classroom)

    @extend_schema(operation_id="education_classroom_join")
    @action(detail=True, methods=("post",))
    def join(self, request, pk=None):
        classroom = get_object_or_404(Classroom, pk=pk, active=True)
        return self._join(request, classroom)

    def _join(self, request, classroom):
        if education_role(request.user) != EducationProfile.Role.STUDENT:
            return Response({"detail": "Somente alunos podem entrar em turmas."}, status=status.HTTP_403_FORBIDDEN)
        membership, created = ClassroomMembership.objects.get_or_create(classroom=classroom, student=request.user)
        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(ClassroomSerializer(membership.classroom, context={"request": request}).data, status=response_status)

    @action(detail=True, methods=("post",))
    def leave(self, request, pk=None):
        classroom = self.get_object()
        deleted, _ = ClassroomMembership.objects.filter(classroom=classroom, student=request.user).delete()
        if not deleted:
            return Response({"detail": "Você não participa desta turma."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=("get", "post"))
    def activities(self, request, pk=None):
        classroom = self.get_object()
        if request.method == "GET":
            return Response(ClassroomActivitySerializer(classroom.activities.all(), many=True).data)
        self.check_owner(classroom)
        serializer = ClassroomActivitySerializer(data=request.data, context={"classroom": classroom})
        serializer.is_valid(raise_exception=True)
        serializer.save(classroom=classroom)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("get",))
    def performance(self, request, pk=None):
        classroom = self.get_object()
        self.check_owner(classroom)
        topic_ids = Topic.objects.filter(unit__grade_subject__grade=classroom.grade).values_list("id", flat=True)
        lesson_ids = Lesson.objects.filter(topic_id__in=topic_ids).values_list("id", flat=True)
        exercise_ids = Exercise.objects.filter(topic_id__in=topic_ids).values_list("id", flat=True)
        data = []
        for student in classroom.students.all():
            progress = TopicProgress.objects.filter(user=student, topic_id__in=topic_ids)
            attempts = ExerciseAttempt.objects.filter(user=student, exercise_id__in=exercise_ids)
            data.append({"student": {"id": student.id, "username": student.username, "email": student.email}, "topics_started": progress.count(), "topics_completed": progress.filter(completed=True).count(), "lessons_completed": LessonProgress.objects.filter(user=student, lesson_id__in=lesson_ids, completed=True).count(), "exercises_attempted": attempts.values("exercise_id").distinct().count(), "exercises_correct": attempts.filter(is_correct=True).values("exercise_id").distinct().count()})
        return Response(data)


class DiagnosticAssessmentViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = DiagnosticAssessmentSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return DiagnosticAssessment.objects.none()
        return DiagnosticAssessment.objects.filter(user=self.request.user).select_related("topic").prefetch_related("responses__exercise__choices")

    @extend_schema(request=DiagnosticAnswerSerializer, responses=DiagnosticAssessmentSerializer)
    @action(detail=True, methods=("post",))
    def answer(self, request, pk=None):
        serializer = DiagnosticAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assessment = self.get_object()
        answer_diagnostic(request.user, assessment, serializer.validated_data["exercise"], serializer.validated_data["answer"])
        assessment.refresh_from_db()
        return Response(DiagnosticAssessmentSerializer(assessment, context={"request": request}).data)

    @action(detail=True, methods=("post",))
    def finish(self, request, pk=None):
        assessment = finish_diagnostic(request.user, self.get_object())
        return Response(diagnostic_result(assessment))


# Final declaration intentionally keeps the review router limited to read-only
# collection endpoints.
class ReviewViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewQueueSerializer

    @extend_schema(responses=ReviewQueueSerializer(many=True))
    def list(self, request):
        return Response(ReviewQueueSerializer(review_queue(request.user, child=child_for_request(request)), many=True).data)

    @extend_schema(responses=ErrorNotebookSerializer(many=True))
    @action(detail=False, methods=("get",))
    def errors(self, request):
        return Response(ErrorNotebookSerializer(error_notebook(request.user, child=child_for_request(request)), many=True).data)


class RecommendationViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RecommendationSerializer

    @extend_schema(responses=RecommendationSerializer(many=True))
    def list(self, request):
        target = request.user
        child_id = request.query_params.get("child")
        if child_id:
            child = get_object_or_404(Child, id=child_id, parent=request.user, active=True)
            topics = Topic.objects.filter(unit__grade_subject__grade=child.grade)
            data = recommendations_for_user(target, topic_queryset=topics, child=child)
            return Response(RecommendationSerializer(data, many=True).data)
        classroom_id = request.query_params.get("classroom")
        student_id = request.query_params.get("student")
        topic_queryset = None
        if classroom_id or student_id:
            if not classroom_id or not student_id or education_role(request.user) != EducationProfile.Role.TEACHER:
                return Response({"detail": "Informe uma turma própria e um aluno autorizado."}, status=status.HTTP_403_FORBIDDEN)
            classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
            membership = get_object_or_404(ClassroomMembership.objects.select_related("student"), classroom=classroom, student_id=student_id)
            target = membership.student
            topic_queryset = Topic.objects.filter(unit__grade_subject__grade=classroom.grade)
        data = recommendations_for_user(target, topic_queryset=topic_queryset)
        return Response(RecommendationSerializer(data, many=True).data)

    @extend_schema(responses=dict)
    @action(detail=False, methods=("get",), url_path="lesson-plan")
    def lesson_plan(self, request):
        topic = get_object_or_404(Topic, id=request.query_params.get("topic"))
        child_id = request.query_params.get("child")
        if child_id:
            child = get_object_or_404(Child, id=child_id, parent=request.user, active=True)
            if topic.unit.grade_subject.grade_id != child.grade_id:
                return Response({"detail": "O conteúdo não pertence à série do filho."}, status=status.HTTP_400_BAD_REQUEST)
            return Response(lesson_plan_for_topic(topic))
        if education_role(request.user) != EducationProfile.Role.TEACHER:
            return Response({"detail": "Selecione um filho para preparar a aula de apoio."}, status=status.HTTP_403_FORBIDDEN)
        classroom_id = request.query_params.get("classroom")
        if classroom_id:
            classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
            if topic.unit.grade_subject.grade_id != classroom.grade_id:
                return Response({"detail": "O conteúdo não pertence à série da turma."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(lesson_plan_for_topic(topic))

    @action(detail=True, methods=("get",))
    def result(self, request, pk=None):
        assessment = self.get_object()
        if not assessment.completed_at:
            return Response({"detail": "Finalize a avaliação para visualizar o resultado."}, status=status.HTTP_409_CONFLICT)
        return Response(diagnostic_result(assessment))


class QuestionBankViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = QuestionBankExerciseSerializer
    queryset = Exercise.objects.select_related("topic__unit__grade_subject__grade__education_level", "topic__unit__grade_subject__subject").prefetch_related("choices")

    def get_queryset(self):
        queryset = self.queryset
        mappings = {
            "level": "topic__unit__grade_subject__grade__education_level_id",
            "grade": "topic__unit__grade_subject__grade_id",
            "subject": "topic__unit__grade_subject__subject_id",
            "unit": "topic__unit_id",
            "topic": "topic_id",
            "difficulty": "difficulty",
            "type": "exercise_type",
        }
        for parameter, field in mappings.items():
            value = self.request.query_params.get(parameter)
            if value:
                queryset = queryset.filter(**{field: value})
        return queryset


class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Assignment.objects.none()
        return Assignment.objects.filter(Q(teacher=self.request.user) | Q(classroom__memberships__student=self.request.user)).select_related("teacher", "classroom").prefetch_related("assignment_exercises").distinct()

    def perform_create(self, serializer):
        if education_role(self.request.user) != EducationProfile.Role.TEACHER:
            self.permission_denied(self.request, message="Apenas professores podem criar atividades.")
        serializer.save()

    def perform_update(self, serializer):
        if serializer.instance.teacher_id != self.request.user.id:
            self.permission_denied(self.request, message="Somente o professor da atividade pode alterá-la.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.teacher_id != self.request.user.id:
            self.permission_denied(self.request, message="Somente o professor da atividade pode removê-la.")
        instance.delete()

    @action(detail=True, methods=("post",))
    def start(self, request, pk=None):
        submission = start_student_assignment(request.user, self.get_object())
        return Response(StudentAssignmentSerializer(submission).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=("get",))
    def results(self, request, pk=None):
        assignment = self.get_object()
        if assignment.teacher_id != request.user.id:
            self.permission_denied(request, message="Somente o professor pode visualizar os resultados.")
        submissions = assignment.student_assignments.filter(submitted_at__isnull=False).select_related("student", "assignment__classroom")
        data = StudentAssignmentSerializer(submissions, many=True).data
        for item, submission in zip(data, submissions):
            item["student"] = {"id": submission.student_id, "username": submission.student.username, "email": submission.student.email}
        return Response(data)


class StudentAssignmentViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = StudentAssignmentSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return StudentAssignment.objects.none()
        return StudentAssignment.objects.filter(student=self.request.user).select_related("assignment__classroom").prefetch_related("responses__exercise__choices")

    def retrieve(self, request, pk=None):
        submission = self.get_object()
        return Response(StudentAssignmentSerializer(submission).data)

    @extend_schema(request=AssignmentAnswerSerializer, responses=StudentAssignmentSerializer)
    @action(detail=True, methods=("post",))
    def answer(self, request, pk=None):
        serializer = AssignmentAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = self.get_object()
        answer_student_assignment(request.user, submission, serializer.validated_data["exercise"], serializer.validated_data["answer"])
        submission._prefetched_objects_cache = {}
        return Response(StudentAssignmentSerializer(submission).data)

    @action(detail=True, methods=("post",))
    def submit(self, request, pk=None):
        submission = submit_student_assignment(request.user, self.get_object())
        submission._prefetched_objects_cache = {}
        return Response(StudentAssignmentSerializer(submission).data)


class LegacyReviewViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ReviewQueueSerializer

    @extend_schema(responses=ReviewQueueSerializer(many=True))
    def list(self, request):
        return Response(ReviewQueueSerializer(review_queue(request.user), many=True).data)

    @extend_schema(responses=ErrorNotebookSerializer(many=True))
    @action(detail=False, methods=("get",))
    def errors(self, request):
        return Response(ErrorNotebookSerializer(error_notebook(request.user), many=True).data)

    @extend_schema(request=AssignmentAnswerSerializer, responses=StudentAssignmentSerializer)
    @action(detail=True, methods=("post",))
    def answer(self, request, pk=None):
        serializer = AssignmentAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = self.get_object()
        answer_student_assignment(request.user, submission, serializer.validated_data["exercise"], serializer.validated_data["answer"])
        submission._prefetched_objects_cache = {}
        return Response(StudentAssignmentSerializer(submission).data)

    @action(detail=True, methods=("post",))
    def submit(self, request, pk=None):
        submission = submit_student_assignment(request.user, self.get_object())
        submission._prefetched_objects_cache = {}
        return Response(StudentAssignmentSerializer(submission).data)

    @action(detail=True, methods=("get",))
    def result(self, request, pk=None):
        assessment = self.get_object()
        if not assessment.completed_at:
            return Response({"detail": "Finalize a avaliação para visualizar o resultado."}, status=status.HTTP_409_CONFLICT)
        return Response(diagnostic_result(assessment))
