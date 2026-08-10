from datetime import datetime
from decimal import Decimal

from django.utils import timezone

from .models import (DiagnosticAssessment, ExerciseAttempt, LessonProgress,
                     StudentAssignmentResponse, Topic, TopicProgress)


def _latest(*values):
    available = [value for value in values if value]
    return max(available) if available else None


def recommendations_for_user(user, topic_queryset=None, limit=5, now=None, child=None):
    now = now or timezone.now()
    topic_ids = set(ExerciseAttempt.objects.filter(user=user, child=child).values_list("exercise__topic_id", flat=True))
    topic_ids.update(TopicProgress.objects.filter(user=user, child=child).values_list("topic_id", flat=True))
    topic_ids.update(DiagnosticAssessment.objects.filter(user=user, child=child).values_list("topic_id", flat=True))
    topic_ids.update(StudentAssignmentResponse.objects.filter(student_assignment__student=user, student_assignment__submitted_at__isnull=False).values_list("exercise__topic_id", flat=True))
    for grade_id in user.classrooms.values_list("grade_id", flat=True):
        topic_ids.update(Topic.objects.filter(unit__grade_subject__grade_id=grade_id).values_list("id", flat=True))
    topics = (topic_queryset or Topic.objects.all()).filter(id__in=topic_ids).select_related("unit__grade_subject__subject")
    results = []
    for topic in topics:
        attempts = list(ExerciseAttempt.objects.filter(user=user, child=child, exercise__topic=topic).order_by("-attempted_at")[:6])
        assignment_answers = list(StudentAssignmentResponse.objects.filter(student_assignment__student=user, student_assignment__submitted_at__isnull=False, exercise__topic=topic).order_by("-answered_at")[:6])
        recent = sorted(attempts + assignment_answers, key=lambda item: item.attempted_at if hasattr(item, "attempted_at") else item.answered_at, reverse=True)[:6]
        errors = sum(not item.is_correct for item in recent)
        accuracy = round(((len(recent) - errors) * 100 / len(recent))) if recent else None
        progress = TopicProgress.objects.filter(user=user, child=child, topic=topic).first()
        completion = Decimal(progress.completion_percentage) if progress else Decimal(0)
        diagnostic = DiagnosticAssessment.objects.filter(user=user, child=child, topic=topic, completed_at__isnull=False).order_by("-completed_at").first()
        diagnostic_percentage = Decimal(diagnostic.percentage) if diagnostic else None
        lesson_review = LessonProgress.objects.filter(user=user, child=child, lesson__topic=topic, completed=True).order_by("-completed_at").first()
        last_attempt = max([item.attempted_at if hasattr(item, "attempted_at") else item.answered_at for item in recent], default=None)
        last_studied = _latest(last_attempt, progress.last_accessed_at if progress else None, diagnostic.completed_at if diagnostic else None, lesson_review.completed_at if lesson_review else None)
        days_since = (now - last_studied).days if last_studied else 30
        score = Decimal(0)
        if accuracy is not None:
            score += Decimal(100 - accuracy) * Decimal("0.40")
            score += Decimal(min(errors * 6, 30))
        if diagnostic_percentage is not None:
            score += (Decimal(100) - diagnostic_percentage) * Decimal("0.20")
        score += (Decimal(100) - completion) * Decimal("0.15")
        score += Decimal(min(max(days_since, 0), 20))
        score = score.quantize(Decimal("0.01"))
        priority = "high" if score >= 60 else "medium" if score >= 30 else "low"
        if errors:
            reason = f"Você errou {errors} das últimas {len(recent)} questões deste conteúdo."
        elif diagnostic_percentage is not None and diagnostic_percentage < 60:
            reason = f"Seu diagnóstico foi de {round(diagnostic_percentage)}%."
        elif completion < 100:
            reason = f"Conteúdo {round(completion)}% concluído."
        else:
            reason = f"Último estudo há {days_since} dias."
        action = "review" if errors or (accuracy is not None and accuracy < 70) else "continue" if completion < 100 else "practice"
        results.append({
            "topic": topic.id,
            "topic_title": topic.title,
            "subject": topic.unit.grade_subject.subject_id,
            "subject_name": topic.unit.grade_subject.subject.name,
            "priority": priority,
            "priority_score": score,
            "reason": reason,
            "accuracy": accuracy,
            "recent_errors": errors,
            "recent_questions": len(recent),
            "diagnostic_percentage": diagnostic_percentage,
            "completion_percentage": completion,
            "days_since_last_study": days_since,
            "recommended_action": action,
        })
    return sorted(results, key=lambda item: (-item["priority_score"], item["topic_title"]))[:limit]


def lesson_plan_for_topic(topic):
    lessons = list(topic.lessons.order_by("order", "id"))
    exercises = list(topic.exercises.select_related("lesson").prefetch_related("choices").order_by("order", "id"))
    primary = lessons[0] if lessons else None
    guided = exercises[0] if exercises else None
    independent = exercises[1:6]
    steps = [
        {"key": "objective", "title": "O que ensinar", "content": primary.introduction if primary and primary.introduction else None},
        {"key": "explanation", "title": "Explicação", "content": primary.explanation if primary else None},
        {"key": "how_to_explain", "title": "Como explicar para seu filho", "content": primary.examples if primary and primary.examples else None},
        {"key": "example", "title": "Exemplo", "content": guided.explanation if guided and guided.explanation else None},
        {"key": "guided", "title": "Faça junto", "exercise": guided.statement if guided else None, "exercise_id": guided.id if guided else None},
        {"key": "independent", "title": "Agora deixe ele tentar", "exercises": [{"id": item.id, "statement": item.statement} for item in independent]},
        {"key": "correction", "title": "Correção", "content": guided.explanation if guided and guided.explanation else None},
        {"key": "summary", "title": "Resumo", "content": lessons[-1].summary if lessons and lessons[-1].summary else None},
    ]
    for step in steps:
        has_material = bool(step.get("content") or step.get("exercise") or step.get("exercises"))
        step["available"] = has_material
        if not has_material:
            step["message"] = "Não há material cadastrado para esta etapa."
    return {"topic": topic.id, "topic_title": topic.title, "lesson": primary.id if primary else None, "steps": steps, "sufficient_material": all(step["available"] for step in steps)}
