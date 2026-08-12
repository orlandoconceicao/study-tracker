from django.core.management.base import BaseCommand, CommandError

from education.content_quality import missing_content_fields
from education.models import Grade, GradeSubject, Topic, Unit


class Command(BaseCommand):
    help = "Audita integralmente os conteúdos publicados e lista os campos pedagógicos ausentes."

    def add_arguments(self, parser):
        parser.add_argument("--unpublish-incomplete", action="store_true")

    def handle(self, *args, **options):
        topics = Topic.objects.select_related("unit__grade_subject__grade__education_level", "unit__grade_subject__subject").prefetch_related("lessons__structured_examples", "exercises__choices")
        incomplete = []
        for topic in topics:
            missing = missing_content_fields(topic)
            if missing:
                incomplete.append((topic, missing))
                if options["unpublish_incomplete"] and topic.status == "published":
                    topic.status = "draft"
                    topic.save(update_fields=("status",))
        total = topics.count()
        complete = total - len(incomplete)
        self.stdout.write("=== AUDITORIA EDUCACIONAL ===")
        self.stdout.write(f"Séries: {Grade.objects.count()}")
        self.stdout.write(f"Matérias por série: {GradeSubject.objects.filter(active=True).count()}")
        self.stdout.write(f"Unidades: {Unit.objects.count()}")
        self.stdout.write(f"Conteúdos: {total}")
        self.stdout.write(f"Aulas completas: {complete}")
        self.stdout.write(f"Incompletos: {len(incomplete)}")
        self.stdout.write(f"Cobertura: {(complete / total * 100) if total else 100:.2f}%")
        for topic, missing in incomplete:
            link = topic.unit.grade_subject
            self.stdout.write(f"[INCOMPLETO] {link.grade.education_level.name} / {link.grade.name} / {link.subject.name} / {topic.unit.title} / {topic.title} — Faltando: {', '.join(missing)}")
        published_incomplete = [(topic, fields) for topic, fields in incomplete if topic.status == "published"]
        if published_incomplete and not options["unpublish_incomplete"]:
            raise CommandError(f"Há {len(published_incomplete)} conteúdos incompletos publicados.")
