from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.core.exceptions import ValidationError
import secrets
import string


class OrderedModel(models.Model):
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True


class EducationLevel(OrderedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)

    class Meta:
        ordering = ("order", "name")

    def __str__(self):
        return self.name


class Grade(OrderedModel):
    education_level = models.ForeignKey(EducationLevel, on_delete=models.CASCADE, related_name="grades")
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140)

    class Meta:
        ordering = ("education_level__order", "order", "name")
        constraints = [models.UniqueConstraint(fields=("education_level", "slug"), name="unique_grade_slug_per_level")]

    def __str__(self):
        return f"{self.name} — {self.education_level}"


class Subject(OrderedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("order", "name")

    def __str__(self):
        return self.name


class GradeSubject(OrderedModel):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="grade_subjects")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="grade_subjects")

    class Meta:
        ordering = ("grade__order", "order", "subject__name")
        constraints = [models.UniqueConstraint(fields=("grade", "subject"), name="unique_subject_per_grade")]

    def __str__(self):
        return f"{self.grade} — {self.subject}"


class Unit(OrderedModel):
    grade_subject = models.ForeignKey(GradeSubject, on_delete=models.CASCADE, related_name="units")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("order", "title")

    def __str__(self):
        return self.title


class Difficulty(models.TextChoices):
    EASY = "easy", "Fácil"
    MEDIUM = "medium", "Médio"
    HARD = "hard", "Difícil"


class Topic(OrderedModel):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="topics")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220)
    description = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    estimated_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "title")
        constraints = [models.UniqueConstraint(fields=("unit", "slug"), name="unique_topic_slug_per_unit")]

    def __str__(self):
        return self.title


class Lesson(OrderedModel):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    introduction = models.TextField(blank=True)
    explanation = models.TextField()
    examples = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    estimated_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("order", "title")

    def __str__(self):
        return self.title


class Exercise(OrderedModel):
    class Type(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Múltipla escolha"
        TRUE_FALSE = "true_false", "Verdadeiro ou falso"
        SHORT_ANSWER = "short_answer", "Resposta curta"

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="exercises")
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, related_name="exercises", blank=True, null=True)
    statement = models.TextField()
    exercise_type = models.CharField(max_length=20, choices=Type.choices)
    difficulty = models.CharField(max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ("order", "id")

    def __str__(self):
        return self.statement[:80]


class ExerciseChoice(OrderedModel):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="choices")
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ("order", "id")

    def __str__(self):
        return self.text[:80]


class ExerciseAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="exercise_attempts")
    child = models.ForeignKey("Child", on_delete=models.CASCADE, related_name="exercise_attempts", blank=True, null=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="attempts")
    answer = models.JSONField()
    is_correct = models.BooleanField()
    attempted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-attempted_at",)
        indexes = [models.Index(fields=("user", "child", "exercise", "attempted_at"))]


class TopicProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topic_progress")
    child = models.ForeignKey("Child", on_delete=models.CASCADE, related_name="topic_progress", blank=True, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="progress")
    completed = models.BooleanField(default=False)
    completion_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    completed_at = models.DateTimeField(blank=True, null=True)
    last_accessed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-last_accessed_at",)
        constraints = [
            models.UniqueConstraint(fields=("user", "topic"), condition=models.Q(child__isnull=True), name="unique_topic_progress_per_user"),
            models.UniqueConstraint(fields=("user", "child", "topic"), condition=models.Q(child__isnull=False), name="unique_topic_progress_per_user_child"),
        ]


class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress")
    child = models.ForeignKey("Child", on_delete=models.CASCADE, related_name="lesson_progress", blank=True, null=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("user", "lesson"), condition=models.Q(child__isnull=True), name="unique_lesson_progress_per_user"),
            models.UniqueConstraint(fields=("user", "child", "lesson"), condition=models.Q(child__isnull=False), name="unique_lesson_progress_per_user_child"),
        ]


class EducationProfile(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Aluno"
        TEACHER = "teacher", "Professor"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="education_profile")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} — {self.get_role_display()}"


class Child(models.Model):
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="children")
    name = models.CharField(max_length=150)
    birth_date = models.DateField(blank=True, null=True)
    education_level = models.ForeignKey(EducationLevel, on_delete=models.PROTECT, related_name="children", blank=True, null=True)
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name="children", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ("name", "id")
        indexes = [models.Index(fields=("parent", "active"))]

    def clean(self):
        if self.grade_id and self.education_level_id and self.grade.education_level_id != self.education_level_id:
            raise ValidationError("A série deve pertencer ao nível de ensino informado.")

    def __str__(self):
        return self.name


def classroom_code():
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        if not Classroom.objects.filter(code=code).exists():
            return code


class Classroom(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="taught_classrooms")
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    grade = models.ForeignKey(Grade, on_delete=models.PROTECT, related_name="classrooms")
    code = models.CharField(max_length=6, unique=True, default=classroom_code, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True, db_index=True)
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, through="ClassroomMembership", related_name="classrooms")

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name


class ClassroomMembership(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="memberships")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="classroom_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("joined_at",)
        constraints = [models.UniqueConstraint(fields=("classroom", "student"), name="unique_student_per_classroom")]


class ClassroomActivity(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="activities")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="classroom_activities", blank=True, null=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="classroom_activities", blank=True, null=True)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="classroom_activities", blank=True, null=True)
    due_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def clean(self):
        references = [self.topic_id, self.lesson_id, self.exercise_id]
        if sum(value is not None for value in references) != 1:
            raise ValidationError("A atividade deve referenciar exatamente um conteúdo, aula ou exercício.")

    def __str__(self):
        return self.title


class DiagnosticAssessment(models.Model):
    class Level(models.TextChoices):
        BEGINNER = "beginner", "Iniciante"
        INTERMEDIATE = "intermediate", "Intermediário"
        ADVANCED = "advanced", "Avançado"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="diagnostic_assessments")
    child = models.ForeignKey(Child, on_delete=models.CASCADE, related_name="diagnostic_assessments", blank=True, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="diagnostic_assessments")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    score = models.PositiveSmallIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    level = models.CharField(max_length=20, choices=Level.choices, blank=True)

    class Meta:
        ordering = ("-started_at",)


class DiagnosticResponse(models.Model):
    assessment = models.ForeignKey(DiagnosticAssessment, on_delete=models.CASCADE, related_name="responses")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="diagnostic_responses")
    order = models.PositiveSmallIntegerField()
    answer = models.JSONField(blank=True, null=True)
    is_correct = models.BooleanField(blank=True, null=True)
    answered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ("order",)
        constraints = [models.UniqueConstraint(fields=("assessment", "exercise"), name="unique_exercise_per_diagnostic")]


class Assignment(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assignments_created")
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name="assignments", blank=True, null=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    available_from = models.DateTimeField(blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    exercises = models.ManyToManyField(Exercise, through="AssignmentExercise", related_name="assignments")

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title


class AssignmentExercise(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="assignment_exercises")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="assignment_exercises")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order", "id")
        constraints = [models.UniqueConstraint(fields=("assignment", "exercise"), name="unique_exercise_per_assignment")]


class StudentAssignment(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="student_assignments")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_assignments")
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(blank=True, null=True)
    score = models.PositiveIntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    class Meta:
        ordering = ("-started_at",)
        constraints = [models.UniqueConstraint(fields=("assignment", "student"), name="unique_submission_per_student_assignment")]


class StudentAssignmentResponse(models.Model):
    student_assignment = models.ForeignKey(StudentAssignment, on_delete=models.CASCADE, related_name="responses")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="assignment_responses")
    answer = models.JSONField(blank=True, null=True)
    is_correct = models.BooleanField(blank=True, null=True)
    answered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("student_assignment", "exercise"), name="unique_response_per_assignment_exercise")]
