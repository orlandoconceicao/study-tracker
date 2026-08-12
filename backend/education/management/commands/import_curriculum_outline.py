import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from education.models import Curriculum, EducationLevel, Grade, GradeSubject, Subject, Topic, Unit


HEADER = re.compile(r"^(\d+)º ano\s*[—-]\s*Ensino (Fundamental|Médio)$", re.IGNORECASE)
SUBJECT_ALIASES = {"português": "portugues", "língua portuguesa": "portugues", "arte": "artes"}


class Command(BaseCommand):
    help = "Importa uma lista textual de matérias e conteúdos, sem inventar aulas ou exercícios."

    def add_arguments(self, parser):
        parser.add_argument("file", help="Arquivo UTF-8 com cabeçalhos de série e linhas Matéria: conteúdo; conteúdo.")

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["file"])
        if not path.is_file():
            raise CommandError(f"Arquivo não encontrado: {path}")
        text = path.read_text(encoding="utf-8-sig")
        curriculum = Curriculum.objects.filter(active=True).order_by("id").first()
        if not curriculum:
            raise CommandError("Cadastre um currículo ativo antes da importação.")

        current_grade = None
        totals = {"subjects": 0, "topics": 0}
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            header = HEADER.match(line)
            if header:
                year = int(header.group(1))
                level_slug = "ensino-medio" if header.group(2).lower() == "médio" else ("ensino-fundamental-i" if year <= 5 else "ensino-fundamental-ii")
                level = EducationLevel.objects.filter(slug=level_slug).first()
                grade_order = year - 5 if level_slug == "ensino-fundamental-ii" else year
                current_grade = Grade.objects.filter(education_level=level, order=grade_order).first()
                if not current_grade:
                    raise CommandError(f"Série não cadastrada: {line}")
                continue
            if not current_grade or ":" not in line:
                continue

            subject_name, raw_topics = (part.strip() for part in line.split(":", 1))
            subject_slug = SUBJECT_ALIASES.get(subject_name.casefold(), slugify(subject_name))
            subject, _ = Subject.objects.update_or_create(
                slug=subject_slug,
                defaults={"name": "Língua Portuguesa" if subject_slug == "portugues" else subject_name, "active": True},
            )
            link, created = GradeSubject.objects.get_or_create(
                grade=current_grade, subject=subject,
                defaults={"curriculum": curriculum, "active": True, "order": current_grade.grade_subjects.count() + 1},
            )
            if not link.active:
                link.active = True
                link.save(update_fields=("active",))
            totals["subjects"] += int(created)
            unit, _ = Unit.objects.get_or_create(
                grade_subject=link, title=f"Conteúdos de {subject.name}",
                defaults={"description": f"Conteúdos de {subject.name} para {current_grade.name}."},
            )
            for order, title in enumerate((item.strip().rstrip(".") for item in raw_topics.split(";")), start=1):
                if not title:
                    continue
                topic_slug = slugify(title)
                candidates = Topic.objects.filter(unit__grade_subject=link, slug=topic_slug).order_by("id")
                topic = candidates.exclude(unit=unit).first() or candidates.filter(unit=unit).first()
                created = topic is None
                if created:
                    topic = Topic.objects.create(unit=unit, slug=topic_slug, title=title[0].upper() + title[1:], description=f"Estudo de {title}.", order=order, status="draft")
                else:
                    # Uma lista curricular não contém material suficiente para
                    # promover um tópico a publicado.
                    for duplicate in candidates.exclude(pk=topic.pk):
                        if not duplicate.progress.exists() and not duplicate.lessons.filter(progress__isnull=False).exists() and not duplicate.exercises.filter(attempts__isnull=False).exists():
                            duplicate.delete()
                totals["topics"] += int(created)

        self.stdout.write(self.style.SUCCESS(
            f"Lista curricular importada: {totals['subjects']} vínculos de matérias e {totals['topics']} conteúdos novos."
        ))
