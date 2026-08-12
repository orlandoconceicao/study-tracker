from django.db import migrations


def link_subjects_to_grades(apps, schema_editor):
    Curriculum = apps.get_model("education", "Curriculum")
    Grade = apps.get_model("education", "Grade")
    GradeSubject = apps.get_model("education", "GradeSubject")
    Subject = apps.get_model("education", "Subject")

    curriculum = Curriculum.objects.filter(active=True).order_by("id").first()
    subjects = list(Subject.objects.filter(active=True).order_by("order", "name"))
    for grade in Grade.objects.all():
        if grade.grade_subjects.exists():
            continue
        for order, subject in enumerate(subjects, start=1):
            GradeSubject.objects.get_or_create(
                grade=grade,
                subject=subject,
                defaults={"curriculum": curriculum, "order": order, "active": True},
            )


class Migration(migrations.Migration):
    dependencies = [("education", "0010_exercise_status_lesson_status_topic_status")]

    operations = [migrations.RunPython(link_subjects_to_grades, migrations.RunPython.noop)]
