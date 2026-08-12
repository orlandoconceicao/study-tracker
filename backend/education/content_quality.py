REQUIRED_LESSON_FIELDS = ("introduction", "importance", "explanation", "parent_guidance", "summary")


def missing_content_fields(topic):
    missing = []
    lesson = topic.lessons.filter(status="published").order_by("order").first()
    if not lesson:
        return ["lesson", "introduction", "context", "explanation", "examples", "exercises", "answers", "review"]
    labels = {"importance": "context", "summary": "review"}
    for field in REQUIRED_LESSON_FIELDS:
        if not (getattr(lesson, field, "") or "").strip():
            missing.append(labels.get(field, field))
    if not lesson.structured_examples.exists() and not (lesson.examples or "").strip():
        missing.append("examples")
    exercises = topic.exercises.filter(status="published")
    if not exercises.exists():
        missing.append("exercises")
    elif exercises.filter(explanation="").exists() or any(not exercise.choices.filter(is_correct=True).exists() for exercise in exercises):
        missing.append("answers/explanations")
    return missing
