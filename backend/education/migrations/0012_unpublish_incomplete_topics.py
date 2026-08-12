from django.db import migrations


def unpublish_incomplete_topics(apps, schema_editor):
    Topic = apps.get_model("education", "Topic")
    for topic in Topic.objects.filter(status="published").prefetch_related("lessons__structured_examples", "exercises__choices"):
        lesson = topic.lessons.filter(status="published").order_by("order").first()
        incomplete = not lesson
        if lesson:
            incomplete = any(not (getattr(lesson, field, "") or "").strip() for field in ("introduction", "importance", "explanation", "parent_guidance", "summary"))
            incomplete = incomplete or (not lesson.structured_examples.exists() and not (lesson.examples or "").strip())
            exercises = topic.exercises.filter(status="published")
            incomplete = incomplete or not exercises.exists() or exercises.filter(explanation="").exists()
            incomplete = incomplete or any(not exercise.choices.filter(is_correct=True).exists() for exercise in exercises)
        if incomplete:
            topic.status = "draft"
            topic.save(update_fields=("status",))


class Migration(migrations.Migration):
    dependencies = [("education", "0011_link_existing_subjects_to_all_grades")]
    operations = [migrations.RunPython(unpublish_incomplete_topics, migrations.RunPython.noop)]
