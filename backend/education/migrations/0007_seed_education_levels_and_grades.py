from django.db import migrations


CURRICULUM = (
    ("Ensino Fundamental I", "ensino-fundamental-i", ("1º ano", "2º ano", "3º ano", "4º ano", "5º ano")),
    ("Ensino Fundamental II", "ensino-fundamental-ii", ("6º ano", "7º ano", "8º ano", "9º ano")),
    ("Ensino Médio", "ensino-medio", ("1º ano", "2º ano", "3º ano")),
)


def seed_curriculum(apps, schema_editor):
    EducationLevel = apps.get_model("education", "EducationLevel")
    Grade = apps.get_model("education", "Grade")
    for level_order, (name, slug, grades) in enumerate(CURRICULUM, start=1):
        level, _ = EducationLevel.objects.get_or_create(
            slug=slug,
            defaults={"name": name, "order": level_order},
        )
        for grade_order, grade_name in enumerate(grades, start=1):
            Grade.objects.get_or_create(
                education_level=level,
                slug=f"{grade_order}-ano",
                defaults={"name": grade_name, "order": grade_order},
            )


class Migration(migrations.Migration):
    dependencies = [("education", "0006_alter_child_education_level_alter_child_grade")]
    operations = [migrations.RunPython(seed_curriculum, migrations.RunPython.noop)]
