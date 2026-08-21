from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import (Assignment, AssignmentExercise, DiagnosticAssessment, DiagnosticResponse,
                     Exercise, ExerciseAttempt, LessonProgress, StudentAssignment,
                     StudentAssignmentResponse, TopicProgress)


def _normalized(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip().casefold()


def correct_answer_for(exercise):
    correct_choices = list(exercise.choices.filter(is_correct=True))
    if exercise.exercise_type == Exercise.Type.MULTIPLE_CHOICE:
        return [choice.id for choice in correct_choices]
    if exercise.exercise_type == Exercise.Type.TRUE_FALSE:
        if not correct_choices:
            return None
        value = _normalized(correct_choices[0].text)
        return value in {"true", "verdadeiro", "1"}
    return [choice.text for choice in correct_choices]


def check_answer(exercise, answer):
    correct_choices = list(exercise.choices.filter(is_correct=True))
    if not correct_choices:
        raise ValidationError({"answer": "Este exercício ainda não possui resposta correta cadastrada."})
    if exercise.exercise_type == Exercise.Type.MULTIPLE_CHOICE:
        supplied = answer if isinstance(answer, list) else [answer]
        try:
            supplied_ids = {int(value) for value in supplied}
        except (TypeError, ValueError):
            raise ValidationError({"answer": "Informe o id da alternativa ou uma lista de ids."})
        return supplied_ids == {choice.id for choice in correct_choices}
    if exercise.exercise_type == Exercise.Type.TRUE_FALSE:
        truthy = {"true", "verdadeiro", "1", "sim"}
        falsy = {"false", "falso", "0", "não", "nao"}
        supplied = _normalized(answer)
        expected = _normalized(correct_choices[0].text)
        if supplied not in truthy | falsy:
            raise ValidationError({"answer": "Informe verdadeiro ou falso."})
        return (supplied in truthy) == (expected in truthy)
    accepted = {_normalized(choice.text) for choice in correct_choices}
    return _normalized(answer) in accepted


@transaction.atomic
def record_attempt(user, exercise, answer):
    is_correct = check_answer(exercise, answer)
    attempt = ExerciseAttempt.objects.create(user=user, exercise=exercise, answer=answer, is_correct=is_correct)
    update_topic_progress(user, exercise.topic)
    return attempt, correct_answer_for(exercise)


@transaction.atomic
def complete_lesson(user, lesson):
    progress, _ = LessonProgress.objects.get_or_create(user=user, lesson=lesson)
    if not progress.completed:
        progress.completed = True
        progress.completed_at = timezone.now()
        progress.save(update_fields=("completed", "completed_at"))
    update_topic_progress(user, lesson.topic)
    return progress


def update_topic_progress(user, topic):
    lesson_ids = topic.lessons.values_list("id", flat=True)
    exercise_ids = topic.exercises.values_list("id", flat=True)
    lesson_total = topic.lessons.count()
    exercise_total = topic.exercises.count()
    lessons_done = LessonProgress.objects.filter(user=user, lesson_id__in=lesson_ids, completed=True).count()
    attempted = ExerciseAttempt.objects.filter(user=user, exercise_id__in=exercise_ids).values("exercise_id").distinct().count()
    correct = ExerciseAttempt.objects.filter(user=user, exercise_id__in=exercise_ids, is_correct=True).values("exercise_id").distinct().count()
    possible = lesson_total + (exercise_total * 2)
    earned = lessons_done + attempted + correct
    percentage = Decimal("100.00") if possible == 0 else (Decimal(earned * 100) / Decimal(possible)).quantize(Decimal("0.01"))
    completed = percentage == Decimal("100.00")
    progress, _ = TopicProgress.objects.get_or_create(user=user, topic=topic)
    progress.completion_percentage = percentage
    progress.completed = completed
    progress.completed_at = progress.completed_at or timezone.now() if completed else None
    progress.save(update_fields=("completion_percentage", "completed", "completed_at", "last_accessed_at"))
    return progress


@transaction.atomic
def start_diagnostic(user, topic):
    assessment = DiagnosticAssessment.objects.create(user=user, topic=topic)
    exercises = list(topic.exercises.filter(choices__is_correct=True).distinct().order_by("order", "difficulty", "id")[:10])
    if len(exercises) < 5:
        assessment.delete()
        raise ValidationError({"detail": "Este conteúdo precisa de pelo menos 5 exercícios com gabarito para o diagnóstico."})
    DiagnosticResponse.objects.bulk_create([
        DiagnosticResponse(assessment=assessment, exercise=exercise, order=index)
        for index, exercise in enumerate(exercises, start=1)
    ])
    return assessment


@transaction.atomic
def answer_diagnostic(user, assessment, exercise_id, answer):
    if assessment.user_id != user.id:
        raise ValidationError({"detail": "Avaliação não encontrada."})
    if assessment.completed_at:
        raise ValidationError({"detail": "Esta avaliação já foi finalizada."})
    response = assessment.responses.select_for_update().select_related("exercise").filter(exercise_id=exercise_id).first()
    if not response:
        raise ValidationError({"exercise": "A questão não pertence a esta avaliação."})
    if response.answered_at:
        raise ValidationError({"exercise": "Esta questão já foi respondida."})
    response.answer = answer
    response.is_correct = check_answer(response.exercise, answer)
    response.answered_at = timezone.now()
    response.save(update_fields=("answer", "is_correct", "answered_at"))
    return response


@transaction.atomic
def finish_diagnostic(user, assessment):
    if assessment.user_id != user.id:
        raise ValidationError({"detail": "Avaliação não encontrada."})
    if assessment.completed_at:
        return assessment
    responses = assessment.responses.all()
    total = responses.count()
    answered = responses.filter(answered_at__isnull=False).count()
    if answered != total:
        raise ValidationError({"detail": "Responda todas as questões antes de finalizar."})
    score = responses.filter(is_correct=True).count()
    percentage = (Decimal(score * 100) / Decimal(total)).quantize(Decimal("0.01"))
    if percentage < 50:
        level = DiagnosticAssessment.Level.BEGINNER
    elif percentage < 80:
        level = DiagnosticAssessment.Level.INTERMEDIATE
    else:
        level = DiagnosticAssessment.Level.ADVANCED
    assessment.score = score
    assessment.percentage = percentage
    assessment.level = level
    assessment.completed_at = timezone.now()
    assessment.save(update_fields=("score", "percentage", "level", "completed_at"))
    return assessment


def diagnostic_result(assessment):
    responses = assessment.responses.select_related("exercise__lesson").all()
    grouped = {}
    for response in responses:
        label = response.exercise.lesson.title if response.exercise.lesson else assessment.topic.title
        grouped.setdefault(label, []).append(response.is_correct)
    strengths = [label for label, answers in grouped.items() if answers and all(answers)]
    review = [label for label, answers in grouped.items() if not all(answers)]
    recommended = None
    if review:
        recommended = assessment.topic.lessons.filter(title=review[0]).first()
    if not recommended:
        recommended = assessment.topic.lessons.order_by("order", "id").first()
    return {
        "id": assessment.id,
        "topic": assessment.topic_id,
        "score": assessment.score,
        "total_questions": responses.count(),
        "percentage": assessment.percentage,
        "level": assessment.level,
        "level_display": assessment.get_level_display(),
        "strengths": strengths,
        "review": review,
        "recommendation": ({"lesson_id": recommended.id, "lesson_title": recommended.title, "message": f'Começar pela aula "{recommended.title}".'} if recommended else {"lesson_id": None, "lesson_title": None, "message": "Começar pelo primeiro conteúdo disponível."}),
    }


@transaction.atomic
def create_assignment(teacher, validated_data, exercise_ids):
    classroom = validated_data.get("classroom")
    if classroom and classroom.teacher_id != teacher.id:
        raise ValidationError({"classroom": "Você só pode criar atividades para suas próprias turmas."})
    exercises = list(Exercise.objects.filter(id__in=exercise_ids).select_related("topic__unit__grade_subject"))
    if len(exercises) != len(set(exercise_ids)):
        raise ValidationError({"exercises": "Uma ou mais questões não foram encontradas."})
    if not exercises:
        raise ValidationError({"exercises": "Selecione pelo menos uma questão."})
    if classroom and any(exercise.topic.unit.grade_subject.grade_id != classroom.grade_id for exercise in exercises):
        raise ValidationError({"exercises": "Todas as questões devem pertencer à série da turma."})
    assignment = Assignment.objects.create(teacher=teacher, **validated_data)
    AssignmentExercise.objects.bulk_create([
        AssignmentExercise(assignment=assignment, exercise=exercise, order=index)
        for index, exercise in enumerate(exercises, start=1)
    ])
    return assignment


@transaction.atomic
def start_student_assignment(student, assignment):
    now = timezone.now()
    if not assignment.classroom_id or not assignment.classroom.memberships.filter(student=student).exists():
        raise ValidationError({"detail": "Você não participa da turma desta atividade."})
    if assignment.available_from and assignment.available_from > now:
        raise ValidationError({"detail": "Esta atividade ainda não está disponível."})
    submission, created = StudentAssignment.objects.get_or_create(assignment=assignment, student=student)
    if created:
        StudentAssignmentResponse.objects.bulk_create([
            StudentAssignmentResponse(student_assignment=submission, exercise=item.exercise)
            for item in assignment.assignment_exercises.select_related("exercise")
        ])
    return submission


@transaction.atomic
def answer_student_assignment(student, submission, exercise_id, answer):
    if submission.student_id != student.id or submission.submitted_at:
        raise ValidationError({"detail": "Esta entrega não pode ser alterada."})
    response = submission.responses.select_for_update().select_related("exercise").filter(exercise_id=exercise_id).first()
    if not response:
        raise ValidationError({"exercise": "A questão não pertence a esta atividade."})
    response.answer = answer
    response.is_correct = check_answer(response.exercise, answer)
    response.answered_at = timezone.now()
    response.save(update_fields=("answer", "is_correct", "answered_at"))
    return response


@transaction.atomic
def submit_student_assignment(student, submission):
    if submission.student_id != student.id:
        raise ValidationError({"detail": "Entrega não encontrada."})
    if submission.submitted_at:
        return submission
    total = submission.responses.count()
    if submission.responses.filter(answered_at__isnull=True).exists():
        raise ValidationError({"detail": "Responda todas as questões antes de entregar."})
    score = submission.responses.filter(is_correct=True).count()
    submission.score = score
    submission.percentage = (Decimal(score * 100) / Decimal(total)).quantize(Decimal("0.01")) if total else Decimal("0")
    submission.submitted_at = timezone.now()
    submission.save(update_fields=("score", "percentage", "submitted_at"))
    return submission
