import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from education.models import (Curriculum, EducationLevel, Example, Exercise,
                              ExerciseChoice, Grade, GradeSubject,
                              KnowledgeObject, Lesson, Skill, Subject, Topic,
                              Unit)


BNCC_URL = "https://basenacionalcomum.mec.gov.br/abase/"


class Command(BaseCommand):
    help = "Popula a base curricular educacional de forma idempotente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--grade", dest="grade", help="Importa apenas uma série. Use, por exemplo, fundamental-ii:7-ano ou ensino-medio:1-ano.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        root = Path(__file__).resolve().parents[2] / "seed_data"
        files = sorted(root.rglob("*.json"), key=lambda path: (path.name != "curriculum.json", str(path)))
        if not files:
            raise CommandError("Nenhum arquivo de currículo encontrado.")
        totals = {key: 0 for key in ("subjects", "units", "objects", "skills", "topics", "lessons", "examples", "exercises")}
        imported_files = 0
        for path in files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if options.get("grade") and not self._matches_grade(data, options["grade"]):
                    continue
                self._seed_file(data, totals)
                imported_files += 1
            except (KeyError, TypeError, ValueError) as error:
                raise CommandError(f"Arquivo curricular inválido: {path}: {error}") from error
        if not imported_files:
            raise CommandError(f"Nenhum arquivo encontrado para a série: {options.get('grade')}")
        links = GradeSubject.objects.filter(curriculum__active=True)
        units = Unit.objects.filter(grade_subject__in=links)
        topics = Topic.objects.filter(unit__in=units)
        lessons = Lesson.objects.filter(topic__in=topics)
        exercises = Exercise.objects.filter(topic__in=topics)
        self.stdout.write(self.style.SUCCESS(
            "Currículo atualizado: "
            f"{links.values('subject_id').distinct().count()} matérias, {units.count()} unidades, "
            f"{KnowledgeObject.objects.filter(unit__in=units).count()} objetos, "
            f"{Skill.objects.filter(curriculum__active=True).count()} habilidades, "
            f"{topics.count()} conteúdos, {lessons.count()} aulas, "
            f"{Example.objects.filter(lesson__in=lessons).count()} exemplos e {exercises.count()} exercícios."
        ))

    @staticmethod
    def _matches_grade(data, selector):
        normalized = selector.strip().lower()
        level_slug = data["level"]["slug"].lower()
        grade_slug = data["grade"]["slug"].lower()
        if ":" in normalized:
            requested_level, requested_grade = normalized.split(":", 1)
            requested_level = {
                "fundamental-i": "ensino-fundamental-i",
                "fundamental-ii": "ensino-fundamental-ii",
                "medio": "ensino-medio",
            }.get(requested_level, requested_level)
            return requested_level == level_slug and requested_grade == grade_slug
        return normalized in {grade_slug, grade_slug.split("-")[0]}

    def _seed_file(self, data, totals):
        curriculum_data = data.get("curriculum", {})
        curriculum, _ = Curriculum.objects.update_or_create(
            name=curriculum_data.get("name", "BNCC"),
            version=curriculum_data.get("version", "2018"),
            region=curriculum_data.get("region", "Brasil"),
            defaults={
                "source": curriculum_data.get("source", "Ministério da Educação — Base Nacional Comum Curricular"),
                "source_url": curriculum_data.get("source_url", BNCC_URL),
                "active": curriculum_data.get("active", True),
            },
        )
        level, _ = EducationLevel.objects.update_or_create(
            slug=data["level"]["slug"],
            defaults={"name": data["level"]["name"], "order": data["level"].get("order", 0)},
        )
        grade, _ = Grade.objects.update_or_create(
            education_level=level,
            slug=data["grade"]["slug"],
            defaults={"name": data["grade"]["name"], "order": data["grade"].get("order", 0)},
        )
        for subject_order, item in enumerate(data["subjects"], start=1):
            subject, _ = Subject.objects.update_or_create(
                slug=item["slug"],
                defaults={"name": item["name"], "description": item.get("description", ""), "icon": item.get("icon", ""), "order": item.get("order", subject_order), "active": True},
            )
            link, _ = GradeSubject.objects.update_or_create(
                grade=grade, subject=subject,
                defaults={"order": item.get("order", subject_order), "curriculum": curriculum, "active": item.get("active", True)},
            )
            totals["subjects"] += 1
            units = item.get("units") or [{"name": item.get("unit", "Conteúdos"), "description": item.get("description", ""), "topics": item["topics"]}]
            for unit_order, unit_data in enumerate(units, start=1):
                unit, _ = Unit.objects.update_or_create(
                    grade_subject=link, title=unit_data["name"],
                    defaults={"description": unit_data.get("description", ""), "order": unit_order},
                )
                totals["units"] += 1
                self._seed_unit(unit, unit_data, curriculum, grade, subject, totals)
            for title in item.get("remove_empty_units", []):
                Unit.objects.filter(grade_subject=link, title=title, topics__isnull=True).delete()
        if data.get("inactive_subjects"):
            GradeSubject.objects.filter(grade=grade, subject__slug__in=data["inactive_subjects"]).update(active=False)

    def _seed_unit(self, unit, unit_data, curriculum, grade, subject, totals):
        objects = {}
        for object_order, object_data in enumerate(unit_data.get("knowledge_objects", []), start=1):
            values = object_data if isinstance(object_data, dict) else {"name": object_data}
            obj, _ = KnowledgeObject.objects.update_or_create(
                unit=unit, name=values["name"],
                defaults={"curriculum": curriculum, "description": values.get("description", ""), "source_url": values.get("source_url", curriculum.source_url), "order": object_order},
            )
            objects[obj.name] = obj
            totals["objects"] += 1
        skills = {}
        for skill_order, skill_data in enumerate(unit_data.get("skills", []), start=1):
            skill, _ = Skill.objects.update_or_create(
                curriculum=curriculum, code=skill_data["code"],
                defaults={"grade": grade, "subject": subject, "description": skill_data["description"], "source_url": skill_data.get("source_url", curriculum.source_url), "order": skill_order},
            )
            skills[skill.code] = skill
            totals["skills"] += 1
        for topic_order, topic_data in enumerate(unit_data["topics"], start=1):
            topic_slug = topic_data.get("slug") or slugify(topic_data["title"])
            candidates = Topic.objects.filter(unit__grade_subject=unit.grade_subject, slug=topic_slug).order_by("id")
            target = candidates.filter(unit=unit).first()
            topic = target or candidates.first()
            if topic and "title" not in topic_data:
                if not target:
                    topic.unit = unit
                topic.order = topic_order
                topic.status = topic_data.get("status", topic.status)
                topic.save(update_fields=("unit", "order", "status"))
                for duplicate in candidates.exclude(pk=topic.pk):
                    if (not duplicate.progress.exists() and not duplicate.lessons.filter(progress__isnull=False).exists()
                            and not duplicate.exercises.filter(attempts__isnull=False).exists()):
                        duplicate.delete()
            elif topic:
                topic.title = topic_data["title"]
                topic.description = topic_data["description"]
                topic.difficulty = topic_data.get("difficulty", "easy")
                topic.estimated_minutes = topic_data.get("estimated_minutes", 15)
                topic.status = topic_data.get("status", "published")
                topic.order = topic_order
                topic.save(update_fields=("title", "description", "difficulty", "estimated_minutes", "status", "order"))
            else:
                topic = Topic.objects.create(
                    unit=unit, slug=topic_slug, title=topic_data["title"], description=topic_data["description"],
                    difficulty=topic_data.get("difficulty", "easy"), estimated_minutes=topic_data.get("estimated_minutes", 15), status=topic_data.get("status", "published"), order=topic_order,
                )
            totals["topics"] += 1
            topic.knowledge_objects.set([objects[name] for name in topic_data.get("knowledge_objects", []) if name in objects])
            topic.skills.set([skills[code] for code in topic_data.get("skills", []) if code in skills])
            if "lesson" not in topic_data and "teaching" not in topic_data:
                continue
            if "lesson" in topic_data:
                lesson_data = topic_data["lesson"]
            else:
                teaching = topic_data["teaching"]
                lesson_data = {
                    "introduction": teaching.get("objective", topic.description),
                    "importance": teaching.get("importance", topic.description),
                    "explanation": teaching["explanation"],
                    "parent_guidance": teaching.get("parent_guidance", "Converse com a criança, use exemplos próximos da rotina e peça que ela explique o que observou."),
                    "examples": "\n\n".join(teaching.get("examples", [])),
                    "joint_activity": teaching.get("joint_activity", "Observem uma situação parecida em casa e registrem juntos o que descobriram."),
                    "common_mistakes": teaching.get("common_mistakes", "Evite dar a resposta imediatamente; retome a pergunta com um exemplo mais concreto."),
                    "parent_tip": teaching.get("parent_tip", "Peça um novo exemplo criado pela própria criança para verificar a compreensão."),
                    "summary": teaching["summary"],
                }
                topic_data["exercises"] = [{
                    "statement": check["statement"], "type": "multiple_choice", "difficulty": check.get("difficulty", "easy"),
                    "explanation": check["explanation"],
                    "choices": [{"text": check["answer"], "correct": True}] + [{"text": wrong} for wrong in check.get("wrong", [])],
                } for check in topic_data.get("checks", [])]
            lesson, _ = Lesson.objects.update_or_create(
                topic=topic, order=1,
                defaults={
                    "title": lesson_data.get("title", topic.title), "introduction": lesson_data["introduction"],
                    "importance": lesson_data.get("importance", topic.description), "explanation": lesson_data["explanation"],
                    "parent_guidance": lesson_data.get("parent_guidance", "Use objetos e situações do cotidiano. Faça perguntas curtas e dê tempo para a criança explicar com as próprias palavras."),
                    "examples": lesson_data.get("examples", ""),
                    "joint_activity": lesson_data.get("joint_activity", "Escolham um exemplo parecido em casa e resolvam juntos, falando cada passo."),
                    "common_mistakes": lesson_data.get("common_mistakes", "Observe se a criança pulou alguma etapa ou respondeu antes de compreender a pergunta."),
                    "parent_tip": lesson_data.get("parent_tip", "Peça à criança que explique o que fez. Explicar com as próprias palavras é um bom sinal de compreensão."),
                    "summary": lesson_data["summary"], "estimated_minutes": topic.estimated_minutes, "status": lesson_data.get("status", topic.status),
                },
            )
            totals["lessons"] += 1
            lesson.structured_examples.all().delete()
            examples = lesson_data.get("structured_examples") or [
                {"title": f"Exemplo {index}", "problem": text}
                for index, text in enumerate(filter(None, lesson_data.get("examples", "").split("\n\n")), start=1)
            ]
            for example_order, example in enumerate(examples, start=1):
                Example.objects.create(
                    lesson=lesson, title=example.get("title", f"Exemplo {example_order}"), problem=example["problem"],
                    steps=example.get("steps", ""), answer=example.get("answer", ""), explanation=example.get("explanation", ""), order=example_order,
                )
                totals["examples"] += 1
            for exercise_order, exercise_data in enumerate(topic_data["exercises"], start=1):
                exercise, _ = Exercise.objects.update_or_create(
                    topic=topic, order=exercise_order,
                    defaults={"lesson": lesson, "statement": exercise_data["statement"], "exercise_type": exercise_data["type"], "difficulty": exercise_data.get("difficulty", "easy"), "explanation": exercise_data["explanation"], "status": exercise_data.get("status", topic.status)},
                )
                exercise.choices.all().delete()
                for choice_order, choice in enumerate(exercise_data["choices"], start=1):
                    ExerciseChoice.objects.create(exercise=exercise, text=choice["text"], is_correct=choice.get("correct", False), order=choice_order)
                totals["exercises"] += 1
