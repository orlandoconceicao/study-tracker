from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Max, Q
from django.utils import timezone

from .models import ExerciseAttempt, TopicProgress


def error_notebook(user, child=None):
    attempts = (
        ExerciseAttempt.objects.filter(user=user, child=child, is_correct=False)
        .values(
            "exercise_id",
            "exercise__statement",
            "exercise__exercise_type",
            "exercise__difficulty",
            "exercise__topic_id",
            "exercise__topic__title",
            "exercise__topic__unit__grade_subject__subject_id",
            "exercise__topic__unit__grade_subject__subject__name",
        )
        .annotate(error_count=Count("id"), last_attempt=Max("attempted_at"))
        .order_by("exercise__topic__unit__grade_subject__subject__name", "exercise__topic__title", "-error_count")
    )
    return [
        {
            "exercise": row["exercise_id"],
            "statement": row["exercise__statement"],
            "exercise_type": row["exercise__exercise_type"],
            "difficulty": row["exercise__difficulty"],
            "topic": row["exercise__topic_id"],
            "topic_title": row["exercise__topic__title"],
            "subject": row["exercise__topic__unit__grade_subject__subject_id"],
            "subject_name": row["exercise__topic__unit__grade_subject__subject__name"],
            "error_count": row["error_count"],
            "last_attempt": row["last_attempt"],
        }
        for row in attempts
    ]


def review_queue(user, now=None, child=None):
    now = now or timezone.now()
    topic_stats = (
        ExerciseAttempt.objects.filter(user=user, child=child)
        .values(
            "exercise__topic_id",
            "exercise__topic__title",
            "exercise__topic__unit__grade_subject__subject_id",
            "exercise__topic__unit__grade_subject__subject__name",
        )
        .annotate(
            attempts=Count("id"),
            correct=Count("id", filter=Q(is_correct=True)),
            errors=Count("id", filter=Q(is_correct=False)),
            last_attempt=Max("attempted_at"),
        )
        .filter(errors__gt=0)
    )
    progress_by_topic = {
        item.topic_id: item.completion_percentage
        for item in TopicProgress.objects.filter(user=user, child=child, topic_id__in=[row["exercise__topic_id"] for row in topic_stats])
    }
    queue = []
    for row in topic_stats:
        attempts = row["attempts"]
        accuracy = Decimal(row["correct"] * 100) / Decimal(attempts)
        progress = Decimal(progress_by_topic.get(row["exercise__topic_id"], 0))
        days_since = max(0, (now - row["last_attempt"]).days)
        score = min(row["errors"] * 10, 40) + ((Decimal(100) - accuracy) * Decimal("0.35")) + Decimal(min(days_since, 30)) + ((Decimal(100) - progress) * Decimal("0.15"))
        score = score.quantize(Decimal("0.01"))
        priority = "high" if score >= 60 else "medium" if score >= 30 else "low"
        reasons = []
        if row["errors"] >= 3:
            reasons.append(f'{row["errors"]} respostas incorretas')
        if accuracy < 60:
            reasons.append("baixo percentual de acerto")
        if days_since >= 7:
            reasons.append(f"última prática há {days_since} dias")
        if progress < 100:
            reasons.append("conteúdo ainda não concluído")
        queue.append({
            "topic": row["exercise__topic_id"],
            "topic_title": row["exercise__topic__title"],
            "subject": row["exercise__topic__unit__grade_subject__subject_id"],
            "subject_name": row["exercise__topic__unit__grade_subject__subject__name"],
            "attempts": attempts,
            "correct": row["correct"],
            "errors": row["errors"],
            "accuracy_percentage": accuracy.quantize(Decimal("0.01")),
            "completion_percentage": progress,
            "last_attempt": row["last_attempt"],
            "days_since_last_review": days_since,
            "priority_score": score,
            "priority": priority,
            "reason": ", ".join(reasons) or "reforço preventivo",
        })
    return sorted(queue, key=lambda item: (-item["priority_score"], -item["errors"], item["topic_title"]))
