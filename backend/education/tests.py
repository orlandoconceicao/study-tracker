from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from .models import (Assignment, Child, Classroom, ClassroomMembership, Curriculum, DiagnosticAssessment, EducationLevel, EducationProfile,
                     Example, Exercise, ExerciseAttempt, ExerciseChoice, Grade, GradeSubject, KnowledgeObject, Lesson,
                     LessonProgress, Skill, Subject, Topic, TopicProgress, Unit)
from .content_quality import missing_content_fields


@pytest.fixture
def curriculum(db):
    level, _ = EducationLevel.objects.get_or_create(name="Ensino Médio", slug="ensino-medio")
    grade, _ = Grade.objects.get_or_create(education_level=level, name="1º ano", slug="1-ano")
    subject = Subject.objects.create(name="Matemática", slug="matematica")
    grade_subject = GradeSubject.objects.create(grade=grade, subject=subject)
    unit = Unit.objects.create(grade_subject=grade_subject, title="Álgebra")
    topic = Topic.objects.create(unit=unit, title="Equações", slug="equacoes")
    lesson = Lesson.objects.create(topic=topic, title="Equações de primeiro grau", explanation="Conteúdo")
    exercise = Exercise.objects.create(topic=topic, lesson=lesson, statement="Quanto é 1 + 1?", exercise_type=Exercise.Type.MULTIPLE_CHOICE, explanation="Soma básica")
    wrong = ExerciseChoice.objects.create(exercise=exercise, text="3", order=1)
    correct = ExerciseChoice.objects.create(exercise=exercise, text="2", is_correct=True, order=2)
    return {"level": level, "grade": grade, "subject": subject, "topic": topic, "lesson": lesson, "exercise": exercise, "wrong": wrong, "correct": correct}


@pytest.fixture
def education_client(db):
    user = get_user_model().objects.create_user(username="student", email="student@example.com", password="password123")
    client = APIClient()
    client.force_authenticate(user)
    client.user = user
    return client


@pytest.mark.django_db
def test_student_can_browse_without_seeing_correct_answer(education_client, curriculum):
    response = education_client.get(f'/api/education/topics/{curriculum["topic"].id}/exercises/')
    assert response.status_code == 200
    assert "is_correct" not in response.data[0]["choices"][0]
    assert "explanation" not in response.data[0]


@pytest.mark.django_db
def test_any_series_content_can_be_started_without_progress_or_diagnostic(education_client, curriculum):
    child = Child.objects.create(
        parent=education_client.user,
        name="João",
        education_level=curriculum["level"],
        grade=curriculum["grade"],
    )
    later_lesson = Lesson.objects.create(topic=curriculum["topic"], title="Última aula", order=99, explanation="Livre")
    later_exercise = Exercise.objects.create(
        topic=curriculum["topic"], lesson=later_lesson, statement="Exercício final",
        exercise_type=Exercise.Type.MULTIPLE_CHOICE, order=99,
    )
    correct = ExerciseChoice.objects.create(exercise=later_exercise, text="Resposta", is_correct=True)

    assert not TopicProgress.objects.filter(user=education_client.user, child=child).exists()
    assert not DiagnosticAssessment.objects.filter(user=education_client.user, child=child).exists()
    lessons = education_client.get(f'/api/education/topics/{curriculum["topic"].id}/lessons/')
    exercises = education_client.get(f'/api/education/topics/{curriculum["topic"].id}/exercises/')
    assert lessons.status_code == 200
    assert [item["id"] for item in lessons.data] == [curriculum["lesson"].id, later_lesson.id]
    assert exercises.status_code == 200
    assert [item["id"] for item in exercises.data] == [curriculum["exercise"].id, later_exercise.id]

    # The last lesson and exercise can be used directly, with no previous completion.
    assert education_client.get(f"/api/education/lessons/{later_lesson.id}/").status_code == 200
    assert education_client.post(
        f"/api/education/exercises/{later_exercise.id}/answer/",
        {"answer": correct.id, "child": child.id}, format="json",
    ).status_code == 201


@pytest.mark.django_db
def test_open_curriculum_does_not_weaken_child_authorization(curriculum):
    owner = get_user_model().objects.create_user(username="content-owner", email="content-owner@example.com", password="password123")
    outsider = get_user_model().objects.create_user(username="content-outsider", email="content-outsider@example.com", password="password123")
    child = Child.objects.create(parent=owner, name="Maria", education_level=curriculum["level"], grade=curriculum["grade"])
    client = APIClient(); client.force_authenticate(outsider)

    response = client.post(
        f'/api/education/exercises/{curriculum["exercise"].id}/answer/',
        {"answer": curriculum["correct"].id, "child": child.id}, format="json",
    )

    assert response.status_code == 404
    assert not ExerciseAttempt.objects.filter(child=child).exists()


@pytest.mark.django_db
def test_parent_can_reveal_answer_and_view_topic_summary_only_for_own_child(curriculum):
    parent = get_user_model().objects.create_user(username="reveal-parent", email="reveal@example.com", password="password123")
    outsider = get_user_model().objects.create_user(username="reveal-outsider", email="reveal-outsider@example.com", password="password123")
    child = Child.objects.create(parent=parent, name="João", education_level=curriculum["level"], grade=curriculum["grade"])
    client = APIClient(); client.force_authenticate(parent)

    revealed = client.post(f'/api/education/exercises/{curriculum["exercise"].id}/reveal/', {"child": child.id}, format="json")
    assert revealed.status_code == 200
    assert revealed.data == {"correct_answer": ["2"], "explanation": "Soma básica"}
    assert not ExerciseAttempt.objects.filter(child=child).exists()

    client.post(f'/api/education/exercises/{curriculum["exercise"].id}/answer/', {"child": child.id, "answer": curriculum["wrong"].id}, format="json")
    summary = client.get(f'/api/education/topics/{curriculum["topic"].id}/progress/', {"child": child.id})
    assert summary.status_code == 200
    assert summary.data == {"total_exercises": 1, "exercises_attempted": 1, "attempts": 1, "correct": 0, "errors": 1, "accuracy_percentage": 0}

    client.force_authenticate(outsider)
    assert client.post(f'/api/education/exercises/{curriculum["exercise"].id}/reveal/', {"child": child.id}, format="json").status_code == 404
    assert client.get(f'/api/education/topics/{curriculum["topic"].id}/progress/', {"child": child.id}).status_code == 404


@pytest.mark.django_db
def test_answer_reveals_result_and_updates_progress(education_client, curriculum):
    exercise = curriculum["exercise"]
    response = education_client.post(f"/api/education/exercises/{exercise.id}/answer/", {"answer": curriculum["correct"].id}, format="json")
    assert response.status_code == 201
    assert response.data == {"correct": True, "correct_answer": [curriculum["correct"].id], "explanation": "Soma básica"}
    progress = TopicProgress.objects.get(user=education_client.user, topic=curriculum["topic"])
    assert progress.completion_percentage == Decimal("66.67")


@pytest.mark.django_db
def test_completing_lesson_finishes_topic_after_correct_exercise(education_client, curriculum):
    education_client.post(f'/api/education/exercises/{curriculum["exercise"].id}/answer/', {"answer": curriculum["correct"].id}, format="json")
    response = education_client.post(f'/api/education/lessons/{curriculum["lesson"].id}/complete/')
    assert response.status_code == 200
    progress = TopicProgress.objects.get(user=education_client.user, topic=curriculum["topic"])
    assert progress.completed is True
    assert progress.completion_percentage == 100


@pytest.mark.django_db
def test_student_cannot_change_curriculum(education_client, curriculum):
    response = education_client.post("/api/education/subjects/", {"name": "Física", "slug": "fisica"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_progress_is_private(education_client, curriculum):
    other = get_user_model().objects.create_user(username="other", email="other@example.com")
    TopicProgress.objects.create(user=other, topic=curriculum["topic"], completion_percentage=50)
    assert education_client.get("/api/education/progress/").data == []


@pytest.fixture
def classroom_users(db):
    User = get_user_model()
    teacher = User.objects.create_user(username="teacher", email="teacher@example.com")
    student = User.objects.create_user(username="class-student", email="class-student@example.com")
    outsider = User.objects.create_user(username="outsider", email="outsider@example.com")
    EducationProfile.objects.create(user=teacher, role=EducationProfile.Role.TEACHER)
    EducationProfile.objects.create(user=student, role=EducationProfile.Role.STUDENT)
    EducationProfile.objects.create(user=outsider, role=EducationProfile.Role.TEACHER)
    return teacher, student, outsider


@pytest.mark.django_db
def test_only_teacher_can_create_classroom(curriculum, classroom_users):
    teacher, student, _ = classroom_users
    client = APIClient()
    client.force_authenticate(student)
    assert client.post("/api/education/classrooms/", {"name": "7º A", "grade": curriculum["grade"].id}).status_code == 403
    client.force_authenticate(teacher)
    response = client.post("/api/education/classrooms/", {"name": "7º A", "grade": curriculum["grade"].id})
    assert response.status_code == 201
    assert len(response.data["code"]) == 6
    assert response.data["teacher"] == teacher.id


@pytest.mark.django_db
def test_student_joins_by_code_and_can_leave(curriculum, classroom_users):
    teacher, student, _ = classroom_users
    classroom = Classroom.objects.create(teacher=teacher, name="Turma", grade=curriculum["grade"])
    client = APIClient()
    client.force_authenticate(student)
    response = client.post("/api/education/classrooms/join/", {"code": classroom.code.lower()})
    assert response.status_code == 201
    assert ClassroomMembership.objects.filter(classroom=classroom, student=student).exists()
    assert client.post(f"/api/education/classrooms/{classroom.id}/leave/").status_code == 204


@pytest.mark.django_db
def test_classroom_data_is_isolated(curriculum, classroom_users):
    teacher, student, outsider = classroom_users
    classroom = Classroom.objects.create(teacher=teacher, name="Privada", grade=curriculum["grade"])
    ClassroomMembership.objects.create(classroom=classroom, student=student)
    client = APIClient()
    client.force_authenticate(outsider)
    assert client.get(f"/api/education/classrooms/{classroom.id}/").status_code == 404
    assert client.patch(f"/api/education/classrooms/{classroom.id}/", {"name": "Invadida"}).status_code == 404
    client.force_authenticate(student)
    response = client.get(f"/api/education/classrooms/{classroom.id}/")
    assert response.status_code == 200
    assert response.data["students"] == []


@pytest.mark.django_db
def test_only_owner_teacher_sees_performance(curriculum, classroom_users):
    teacher, student, outsider = classroom_users
    classroom = Classroom.objects.create(teacher=teacher, name="Turma", grade=curriculum["grade"])
    ClassroomMembership.objects.create(classroom=classroom, student=student)
    client = APIClient()
    client.force_authenticate(student)
    assert client.get(f"/api/education/classrooms/{classroom.id}/performance/").status_code == 403
    client.force_authenticate(teacher)
    response = client.get(f"/api/education/classrooms/{classroom.id}/performance/")
    assert response.status_code == 200
    assert response.data[0]["student"]["id"] == student.id


def add_diagnostic_exercises(curriculum, count=4):
    for index in range(count):
        exercise = Exercise.objects.create(topic=curriculum["topic"], lesson=curriculum["lesson"], statement=f"Questão {index}", exercise_type=Exercise.Type.TRUE_FALSE, order=index + 2)
        ExerciseChoice.objects.create(exercise=exercise, text="Verdadeiro", is_correct=True)
        ExerciseChoice.objects.create(exercise=exercise, text="Falso")


@pytest.mark.django_db
def test_diagnostic_uses_existing_exercises_without_revealing_answers(education_client, curriculum):
    add_diagnostic_exercises(curriculum)
    response = education_client.post(f'/api/education/topics/{curriculum["topic"].id}/diagnostic/start/')
    assert response.status_code == 201
    assert response.data["total_questions"] == 5
    assert "is_correct" not in response.data["questions"][0]["exercise"]["choices"][0]
    assert response.data["questions"][0]["exercise"]["id"] == curriculum["exercise"].id


@pytest.mark.django_db
def test_diagnostic_answers_finish_and_deterministic_result(education_client, curriculum):
    add_diagnostic_exercises(curriculum)
    started = education_client.post(f'/api/education/topics/{curriculum["topic"].id}/diagnostic/start/').data
    assessment_id = started["id"]
    assert education_client.post(f"/api/education/diagnostics/{assessment_id}/finish/").status_code == 400
    for question in started["questions"]:
        exercise = question["exercise"]
        answer = curriculum["correct"].id if exercise["exercise_type"] == "multiple_choice" else True
        response = education_client.post(f"/api/education/diagnostics/{assessment_id}/answer/", {"exercise": exercise["id"], "answer": answer}, format="json")
        assert response.status_code == 200
    result = education_client.post(f"/api/education/diagnostics/{assessment_id}/finish/")
    assert result.status_code == 200
    assert result.data["percentage"] == Decimal("100.00")
    assert result.data["level"] == "advanced"
    assert result.data["strengths"] == [curriculum["lesson"].title]
    assert result.data["recommendation"]["lesson_id"] == curriculum["lesson"].id


@pytest.mark.django_db
def test_diagnostic_is_private(education_client, curriculum):
    add_diagnostic_exercises(curriculum)
    started = education_client.post(f'/api/education/topics/{curriculum["topic"].id}/diagnostic/start/').data
    other = get_user_model().objects.create_user(username="diagnostic-other", email="diagnostic-other@example.com")
    client = APIClient()
    client.force_authenticate(other)
    assert client.get(f'/api/education/diagnostics/{started["id"]}/result/').status_code == 404


@pytest.mark.django_db
def test_question_bank_filters_existing_exercises(education_client, curriculum):
    response = education_client.get("/api/education/questions/", {"level": curriculum["level"].id, "grade": curriculum["grade"].id, "subject": curriculum["subject"].id, "topic": curriculum["topic"].id, "difficulty": "medium", "type": "multiple_choice"})
    assert response.status_code == 200
    assert response.data[0]["id"] == curriculum["exercise"].id
    assert response.data[0]["subject_name"] == curriculum["subject"].name
    assert "is_correct" not in response.data[0]["choices"][0]


@pytest.mark.django_db
def test_teacher_creates_assignment_with_selected_existing_exercises(curriculum, classroom_users):
    teacher, student, _ = classroom_users
    classroom = Classroom.objects.create(teacher=teacher, name="Atividades", grade=curriculum["grade"])
    client = APIClient(); client.force_authenticate(student)
    payload = {"classroom": classroom.id, "title": "Lista 1", "exercise_ids": [curriculum["exercise"].id]}
    assert client.post("/api/education/assignments/", payload, format="json").status_code == 403
    client.force_authenticate(teacher)
    response = client.post("/api/education/assignments/", payload, format="json")
    assert response.status_code == 201
    assert response.data["question_count"] == 1
    assert Assignment.objects.get().exercises.get() == curriculum["exercise"]


@pytest.mark.django_db
def test_student_assignment_flow_hides_correction_until_submission(curriculum, classroom_users):
    teacher, student, _ = classroom_users
    classroom = Classroom.objects.create(teacher=teacher, name="Atividades", grade=curriculum["grade"])
    ClassroomMembership.objects.create(classroom=classroom, student=student)
    assignment = Assignment.objects.create(teacher=teacher, classroom=classroom, title="Lista")
    assignment.exercises.add(curriculum["exercise"], through_defaults={"order": 1})
    client = APIClient(); client.force_authenticate(student)
    started = client.post(f"/api/education/assignments/{assignment.id}/start/")
    assert started.status_code == 201
    assert "is_correct" not in started.data["responses"][0]
    submission_id = started.data["id"]
    answered = client.post(f"/api/education/student-assignments/{submission_id}/answer/", {"exercise": curriculum["exercise"].id, "answer": curriculum["correct"].id}, format="json")
    assert answered.status_code == 200
    assert "is_correct" not in answered.data["responses"][0]
    result = client.post(f"/api/education/student-assignments/{submission_id}/submit/")
    assert result.status_code == 200
    assert result.data["correct"] == 1
    assert result.data["errors"] == 0
    assert result.data["percentage"] == "100.00"
    assert result.data["duration_seconds"] is not None


@pytest.mark.django_db
def test_only_assignment_teacher_can_view_student_results(curriculum, classroom_users):
    teacher, student, outsider = classroom_users
    classroom = Classroom.objects.create(teacher=teacher, name="Atividades", grade=curriculum["grade"])
    ClassroomMembership.objects.create(classroom=classroom, student=student)
    assignment = Assignment.objects.create(teacher=teacher, classroom=classroom, title="Lista")
    client = APIClient(); client.force_authenticate(outsider)
    assert client.get(f"/api/education/assignments/{assignment.id}/results/").status_code == 404
    client.force_authenticate(student)
    assert client.get(f"/api/education/assignments/{assignment.id}/results/").status_code == 403


@pytest.mark.django_db
def test_error_notebook_groups_errors_and_isolates_users(education_client, curriculum):
    ExerciseAttempt.objects.create(user=education_client.user, exercise=curriculum["exercise"], answer=curriculum["wrong"].id, is_correct=False)
    ExerciseAttempt.objects.create(user=education_client.user, exercise=curriculum["exercise"], answer=curriculum["wrong"].id, is_correct=False)
    other = get_user_model().objects.create_user(username="review-other", email="review-other@example.com")
    ExerciseAttempt.objects.create(user=other, exercise=curriculum["exercise"], answer=curriculum["wrong"].id, is_correct=False)
    response = education_client.get("/api/education/review/errors/")
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["error_count"] == 2
    assert response.data[0]["subject_name"] == curriculum["subject"].name


@pytest.mark.django_db
def test_review_queue_has_deterministic_priority(education_client, curriculum):
    for _ in range(3):
        ExerciseAttempt.objects.create(user=education_client.user, exercise=curriculum["exercise"], answer=curriculum["wrong"].id, is_correct=False)
    TopicProgress.objects.create(user=education_client.user, topic=curriculum["topic"], completion_percentage=20)
    response = education_client.get("/api/education/review/")
    assert response.status_code == 200
    assert response.data[0]["priority"] == "high"
    assert response.data[0]["priority_score"] == "77.00"
    assert response.data[0]["accuracy_percentage"] == "0.00"
    assert response.data[0]["reason"] == "3 respostas incorretas, baixo percentual de acerto, conteúdo ainda não concluído"


@pytest.mark.django_db
def test_retry_preserves_previous_attempts(education_client, curriculum):
    ExerciseAttempt.objects.create(user=education_client.user, exercise=curriculum["exercise"], answer=curriculum["wrong"].id, is_correct=False)
    response = education_client.post(f'/api/education/exercises/{curriculum["exercise"].id}/answer/', {"answer": curriculum["correct"].id}, format="json")
    assert response.status_code == 201
    attempts = ExerciseAttempt.objects.filter(user=education_client.user, exercise=curriculum["exercise"]).order_by("attempted_at")
    assert attempts.count() == 2
    assert [attempt.is_correct for attempt in attempts] == [False, True]


@pytest.mark.django_db
def test_recommendations_prioritize_many_errors_over_mastered_content(education_client, curriculum):
    weak = curriculum["topic"]
    mastered = Topic.objects.create(unit=weak.unit, title="Conteúdo dominado", slug="dominado", order=2)
    mastered_exercise = Exercise.objects.create(topic=mastered, statement="Dominada", exercise_type=Exercise.Type.TRUE_FALSE)
    ExerciseChoice.objects.create(exercise=mastered_exercise, text="Verdadeiro", is_correct=True)
    for _ in range(4):
        ExerciseAttempt.objects.create(user=education_client.user, exercise=curriculum["exercise"], answer=curriculum["wrong"].id, is_correct=False)
    for _ in range(6):
        ExerciseAttempt.objects.create(user=education_client.user, exercise=mastered_exercise, answer=True, is_correct=True)
    TopicProgress.objects.create(user=education_client.user, topic=weak, completion_percentage=20)
    TopicProgress.objects.create(user=education_client.user, topic=mastered, completion_percentage=100, completed=True)
    response = education_client.get("/api/education/recommendations/")
    assert response.status_code == 200
    assert response.data[0]["topic"] == weak.id
    assert response.data[0]["priority"] == "high"
    mastered_result = next(item for item in response.data if item["topic"] == mastered.id)
    assert Decimal(response.data[0]["priority_score"]) > Decimal(mastered_result["priority_score"])
    assert mastered_result["priority"] == "low"


@pytest.mark.django_db
def test_recommendations_do_not_mix_users(education_client, curriculum):
    other = get_user_model().objects.create_user(username="recommend-other", email="recommend-other@example.com")
    ExerciseAttempt.objects.create(user=other, exercise=curriculum["exercise"], answer=curriculum["wrong"].id, is_correct=False)
    assert education_client.get("/api/education/recommendations/").data == []


@pytest.mark.django_db
def test_teacher_only_sees_authorized_student_recommendations(curriculum, classroom_users):
    teacher, student, outsider = classroom_users
    classroom = Classroom.objects.create(teacher=teacher, name="Recomendação", grade=curriculum["grade"])
    ClassroomMembership.objects.create(classroom=classroom, student=student)
    ExerciseAttempt.objects.create(user=student, exercise=curriculum["exercise"], answer=curriculum["wrong"].id, is_correct=False)
    client = APIClient(); client.force_authenticate(teacher)
    response = client.get("/api/education/recommendations/", {"classroom": classroom.id, "student": student.id})
    assert response.status_code == 200
    assert response.data[0]["topic"] == curriculum["topic"].id
    client.force_authenticate(outsider)
    assert client.get("/api/education/recommendations/", {"classroom": classroom.id, "student": student.id}).status_code == 404


@pytest.mark.django_db
def test_teacher_lesson_plan_uses_only_registered_material(curriculum, classroom_users):
    teacher, _, _ = classroom_users
    classroom = Classroom.objects.create(teacher=teacher, name="Roteiro", grade=curriculum["grade"])
    client = APIClient(); client.force_authenticate(teacher)
    response = client.get("/api/education/recommendations/lesson-plan/", {"topic": curriculum["topic"].id, "classroom": classroom.id})
    assert response.status_code == 200
    explanation = next(step for step in response.data["steps"] if step["key"] == "explanation")
    assert explanation["content"] == curriculum["lesson"].explanation
    unavailable = [step for step in response.data["steps"] if not step["available"]]
    assert unavailable
    assert all(step["message"] == "Não há material cadastrado para esta etapa." for step in unavailable)


@pytest.mark.django_db
def test_parent_can_prepare_and_finish_support_lesson_for_own_child(curriculum):
    parent = get_user_model().objects.create_user(username="support-parent", email="support@example.com", password="password123")
    child = Child.objects.create(parent=parent, name="João", education_level=curriculum["level"], grade=curriculum["grade"])
    client = APIClient(); client.force_authenticate(parent)

    response = client.get("/api/education/recommendations/lesson-plan/", {"topic": curriculum["topic"].id, "child": child.id})

    assert response.status_code == 200
    assert response.data["lesson"] == curriculum["lesson"].id
    assert [step["title"] for step in response.data["steps"]] == [
        "O que ensinar", "Explicação", "Como explicar para seu filho", "Exemplo",
        "Faça junto", "Agora deixe ele tentar", "Correção", "Resumo",
    ]
    assert response.data["sufficient_material"] is False
    assert not LessonProgress.objects.filter(user=parent, child=child).exists()

    finished = client.post(f'/api/education/lessons/{curriculum["lesson"].id}/complete/', {"child": child.id}, format="json")

    assert finished.status_code == 200
    assert LessonProgress.objects.filter(user=parent, child=child, lesson=curriculum["lesson"], completed=True).exists()


@pytest.mark.django_db
def test_parent_cannot_prepare_support_lesson_with_another_parents_child(curriculum):
    owner = get_user_model().objects.create_user(username="support-owner", email="support-owner@example.com", password="password123")
    outsider = get_user_model().objects.create_user(username="support-outsider", email="support-outsider@example.com", password="password123")
    child = Child.objects.create(parent=owner, name="Maria", education_level=curriculum["level"], grade=curriculum["grade"])
    client = APIClient(); client.force_authenticate(outsider)

    response = client.get("/api/education/recommendations/lesson-plan/", {"topic": curriculum["topic"].id, "child": child.id})

    assert response.status_code == 404


@pytest.mark.django_db
def test_children_crud_and_isolation(curriculum):
    parent = get_user_model().objects.create_user(username="parent", email="parent@example.com", password="password123")
    outsider = get_user_model().objects.create_user(username="outsider-parent", email="outsider-parent@example.com", password="password123")
    client = APIClient(); client.force_authenticate(parent)
    created = client.post("/api/education/children/", {"name": "João", "education_level": curriculum["level"].id, "grade": curriculum["grade"].id}, format="json")
    assert created.status_code == 201
    child_id = created.data["id"]
    assert Child.objects.get(id=child_id).parent == parent
    assert client.patch(f"/api/education/children/{child_id}/", {"name": "João Silva"}, format="json").status_code == 200
    client.force_authenticate(outsider)
    assert client.get(f"/api/education/children/{child_id}/").status_code == 404
    assert client.patch(f"/api/education/children/{child_id}/", {"name": "Invadido"}, format="json").status_code == 404
    assert client.delete(f"/api/education/children/{child_id}/").status_code == 404
    assert client.get(f"/api/education/children/{child_id}/progress/").status_code == 404


@pytest.mark.django_db
def test_child_grade_must_match_education_level(curriculum):
    other_level = EducationLevel.objects.create(name="Fundamental", slug="fundamental")
    parent = get_user_model().objects.create_user(username="responsavel", email="responsavel@example.com", password="password123")
    client = APIClient(); client.force_authenticate(parent)
    response = client.post("/api/education/children/", {"name": "Maria", "education_level": other_level.id, "grade": curriculum["grade"].id}, format="json")
    assert response.status_code == 400
    assert "grade" in response.data


@pytest.mark.django_db
def test_changing_child_grade_preserves_learning_history(curriculum):
    parent = get_user_model().objects.create_user(username="history-parent", password="password123")
    child = Child.objects.create(parent=parent, name="João", education_level=curriculum["level"], grade=curriculum["grade"])
    TopicProgress.objects.create(user=parent, child=child, topic=curriculum["topic"], completion_percentage=50)
    LessonProgress.objects.create(user=parent, child=child, lesson=curriculum["lesson"], completed=True)
    ExerciseAttempt.objects.create(user=parent, child=child, exercise=curriculum["exercise"], answer={"answer": "x"}, is_correct=False)
    next_grade = Grade.objects.create(education_level=curriculum["level"], name="2º ano", slug="2-ano-history")
    client = APIClient(); client.force_authenticate(parent)

    response = client.patch(f"/api/education/children/{child.id}/", {"grade": next_grade.id}, format="json")

    assert response.status_code == 200
    child.refresh_from_db()
    assert child.grade == next_grade
    assert TopicProgress.objects.filter(child=child, topic=curriculum["topic"]).exists()
    assert LessonProgress.objects.filter(child=child, lesson=curriculum["lesson"]).exists()
    assert ExerciseAttempt.objects.filter(child=child, exercise=curriculum["exercise"]).exists()


@pytest.mark.django_db
def test_seed_education_populates_first_grade_curriculum_idempotently():
    call_command("seed_education")
    grade = Grade.objects.get(education_level__slug="ensino-fundamental-i", slug="1-ano")
    math_link = GradeSubject.objects.get(grade=grade, subject__slug="matematica")

    assert grade.grade_subjects.count() == 8
    assert Topic.objects.filter(unit__grade_subject=math_link).count() == 17
    assert Topic.objects.filter(unit__grade_subject__grade=grade).count() == 50
    assert Lesson.objects.filter(topic__unit__grade_subject__grade=grade).count() == 50
    assert Exercise.objects.filter(topic__unit__grade_subject__grade=grade).count() == 100
    assert Curriculum.objects.filter(name="BNCC", version="2018", region="Brasil").count() == 1
    assert Skill.objects.filter(grade=grade).count() == 93
    assert KnowledgeObject.objects.filter(unit__grade_subject__grade=grade).count() == 51
    assert Example.objects.filter(lesson__topic__unit__grade_subject__grade=grade).count() == 100
    assert not Topic.objects.filter(unit__grade_subject__grade=grade, lessons__isnull=True).exists()
    assert not Topic.objects.filter(unit__grade_subject__grade=grade, exercises__isnull=True).exists()

    counts = (
        Subject.objects.count(), GradeSubject.objects.count(), Unit.objects.count(), Curriculum.objects.count(),
        KnowledgeObject.objects.count(), Skill.objects.count(), Topic.objects.count(), Lesson.objects.count(),
        Example.objects.count(), Exercise.objects.count(), ExerciseChoice.objects.count(),
    )
    call_command("seed_education")
    assert counts == (
        Subject.objects.count(), GradeSubject.objects.count(), Unit.objects.count(), Curriculum.objects.count(),
        KnowledgeObject.objects.count(), Skill.objects.count(), Topic.objects.count(), Lesson.objects.count(),
        Example.objects.count(), Exercise.objects.count(), ExerciseChoice.objects.count(),
    )


@pytest.mark.django_db
def test_seeded_subject_endpoint_exposes_content_count():
    call_command("seed_education")
    parent = get_user_model().objects.create_user(username="seed-parent", password="password123")
    level = EducationLevel.objects.get(slug="ensino-fundamental-i")
    grade = Grade.objects.get(education_level=level, slug="1-ano")
    child = Child.objects.create(parent=parent, name="Lia", education_level=level, grade=grade)
    client = APIClient()
    client.force_authenticate(parent)

    response = client.get(f"/api/education/children/{child.id}/subjects/")

    assert response.status_code == 200
    assert len(response.data) == 7
    assert all(item["subject"]["slug"] != "ingles" for item in response.data)
    assert [item["subject"]["name"] for item in response.data] == [
        "Língua Portuguesa", "Matemática", "Ciências", "História", "Geografia", "Arte", "Educação Física",
    ]
    math = next(item for item in response.data if item["subject"]["slug"] == "matematica")
    assert math["content_count"] == 17


@pytest.mark.django_db
def test_child_subject_endpoint_includes_subject_without_published_content():
    parent = get_user_model().objects.create_user(username="empty-grade-parent", password="password123")
    level = EducationLevel.objects.create(name="Nivel de teste", slug="nivel-vazio", order=99)
    grade = Grade.objects.create(education_level=level, name="Serie de teste", slug="serie-vazia", order=1)
    subject = Subject.objects.create(name="Materia disponivel", slug="materia-disponivel", active=True)
    link = GradeSubject.objects.create(grade=grade, subject=subject, active=True)
    child = Child.objects.create(parent=parent, name="Filho", education_level=level, grade=grade)
    client = APIClient()
    client.force_authenticate(parent)

    response = client.get(f"/api/education/children/{child.id}/subjects/")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["id"] == link.id
    assert response.data[0]["subject"]["id"] == subject.id
    assert response.data[0]["content_count"] == 0


@pytest.mark.django_db
def test_every_published_topic_has_complete_teaching_material():
    call_command("seed_education")
    incomplete = {
        topic.id: missing_content_fields(topic)
        for topic in Topic.objects.filter(status="published").prefetch_related(
            "lessons__structured_examples", "exercises__choices"
        )
        if missing_content_fields(topic)
    }
    assert incomplete == {}


@pytest.mark.django_db
def test_exercise_list_never_exposes_correct_choice_to_staff(curriculum):
    staff = get_user_model().objects.create_user(username="curriculum-admin", password="password123", is_staff=True)
    client = APIClient()
    client.force_authenticate(staff)

    response = client.get(f'/api/education/topics/{curriculum["topic"].id}/exercises/')

    assert response.status_code == 200
    assert "is_correct" not in response.data[0]["choices"][0]
    assert "explanation" not in response.data[0]


@pytest.mark.django_db
def test_draft_curriculum_is_hidden_from_family_users(curriculum, education_client):
    curriculum["topic"].status = "draft"
    curriculum["topic"].save(update_fields=("status",))

    assert education_client.get(f'/api/education/topics/{curriculum["topic"].id}/').status_code == 404
    assert education_client.get(f'/api/education/topics/{curriculum["topic"].id}/lessons/').status_code == 404


@pytest.mark.django_db
def test_validate_education_reports_incomplete_grades(capsys):
    call_command("validate_education")
    output = capsys.readouterr().out
    assert "COBERTURA EDUCACIONAL" in output
    assert "Série sem matérias publicáveis" in output
