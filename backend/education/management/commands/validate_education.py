from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q

from education.models import Exercise, Grade, GradeSubject, Topic


EXPECTED_SUBJECTS = {
    "ensino-fundamental-i": {"portugues", "matematica", "ciencias", "historia", "geografia", "artes", "educacao-fisica"},
    "ensino-fundamental-ii": {"portugues", "matematica", "ciencias", "historia", "geografia", "artes", "educacao-fisica", "ingles"},
    "ensino-medio": {"portugues", "matematica", "historia", "geografia", "artes", "educacao-fisica", "ingles", "biologia", "fisica", "quimica", "filosofia", "sociologia"},
}


class Command(BaseCommand):
    help = "Valida integridade editorial e exibe a cobertura curricular de todas as séries."

    def add_arguments(self, parser):
        parser.add_argument("--strict", action="store_true", help="Retorna erro quando houver qualquer pendência.")

    def handle(self, *args, **options):
        total_errors = 0
        self.stdout.write(self.style.MIGRATE_HEADING("COBERTURA EDUCACIONAL"))
        for level in self._levels():
            self.stdout.write(self.style.HTTP_INFO(f"\n{level.name}"))
            for grade in level.grades.all():
                errors, stats = self._validate_grade(grade)
                total_errors += len(errors)
                label = "OK" if not errors else f"INCOMPLETO — {len(errors)} pendência(s)"
                color = self.style.SUCCESS if not errors else self.style.WARNING
                self.stdout.write(color(
                    f"{grade.name}: {label} | {stats['subjects']} matérias, {stats['units']} unidades, "
                    f"{stats['topics']} tópicos, {stats['lessons']} aulas, {stats['exercises']} exercícios | cobertura {stats['coverage']}%"
                ))
                for error in errors:
                    self.stdout.write(f"  - {error}")
        summary = f"Validação concluída com {total_errors} pendência(s)."
        if total_errors and options["strict"]:
            raise CommandError(summary)
        self.stdout.write((self.style.WARNING if total_errors else self.style.SUCCESS)(summary))

    @staticmethod
    def _levels():
        from education.models import EducationLevel
        return EducationLevel.objects.prefetch_related("grades").all()

    def _validate_grade(self, grade):
        errors = []
        links = GradeSubject.objects.filter(grade=grade, active=True, subject__active=True).select_related("subject", "curriculum")
        if not links.exists():
            return ["Série sem matérias publicáveis."], {"subjects": 0, "units": 0, "topics": 0, "lessons": 0, "exercises": 0, "coverage": 0}
        present_subjects = set(links.values_list("subject__slug", flat=True))
        missing_subjects = EXPECTED_SUBJECTS.get(grade.education_level.slug, set()) - present_subjects
        if missing_subjects:
            errors.append(f"Componentes curriculares ausentes: {', '.join(sorted(missing_subjects))}.")
        for link in links:
            prefix = link.subject.name
            topics = Topic.objects.filter(unit__grade_subject=link, status="published").prefetch_related("skills", "lessons__structured_examples", "exercises__choices")
            if not link.curriculum_id or not link.curriculum.source_url:
                errors.append(f"{prefix}: referência curricular ausente.")
            if not topics.exists():
                errors.append(f"{prefix}: matéria sem tópico publicado.")
                continue
            duplicate_slugs = topics.values("slug").annotate(total=Count("id")).filter(total__gt=1)
            if duplicate_slugs.exists():
                errors.append(f"{prefix}: tópico duplicado.")
            for topic in topics:
                topic_label = f"{prefix} / {topic.title}"
                if not topic.skills.exists():
                    errors.append(f"{topic_label}: habilidade curricular ausente.")
                lessons = topic.lessons.filter(status="published")
                exercises = topic.exercises.filter(status="published")
                if not lessons.exists():
                    errors.append(f"{topic_label}: aula publicada ausente.")
                elif not lessons.filter(structured_examples__isnull=False).exists():
                    errors.append(f"{topic_label}: exemplo estruturado ausente.")
                if not exercises.exists():
                    errors.append(f"{topic_label}: exercícios publicados ausentes.")
                elif exercises.count() < 5:
                    errors.append(f"{topic_label}: possui {exercises.count()} exercícios; mínimo editorial esperado: 5.")
                for exercise in exercises:
                    if exercise.lesson_id and exercise.lesson.topic_id != topic.id:
                        errors.append(f"{topic_label}: exercício ligado a aula de outro tópico.")
                    if not exercise.choices.filter(is_correct=True).exists():
                        errors.append(f"{topic_label}: exercício sem resposta correta.")
                    if exercise.exercise_type == Exercise.Type.MULTIPLE_CHOICE and exercise.choices.count() < 2:
                        errors.append(f"{topic_label}: múltipla escolha sem alternativas suficientes.")
        topic_filter = Q(unit__grade_subject__grade=grade, status="published", unit__grade_subject__active=True)
        stats = {
            "subjects": links.filter(units__topics__status="published").distinct().count(),
            "units": grade.grade_subjects.filter(active=True).values("units").filter(units__topics__status="published").distinct().count(),
            "topics": Topic.objects.filter(topic_filter).count(),
            "lessons": sum(topic.lessons.filter(status="published").count() for topic in Topic.objects.filter(topic_filter)),
            "exercises": sum(topic.exercises.filter(status="published").count() for topic in Topic.objects.filter(topic_filter)),
        }
        checks = max(1, links.count() * 2 + stats["topics"] * 4)
        stats["coverage"] = max(0, round((checks - len(errors)) * 100 / checks))
        return errors, stats
