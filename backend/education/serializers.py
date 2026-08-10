from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (Assignment, AssignmentExercise, Child, Classroom, ClassroomActivity, ClassroomMembership, DiagnosticAssessment,
                     DiagnosticResponse, EducationLevel, EducationProfile, Exercise, ExerciseAttempt, ExerciseChoice, Grade,
                     GradeSubject, Lesson, LessonProgress, StudentAssignment, StudentAssignmentResponse,
                     Subject, Topic, TopicProgress, Unit)


class EducationLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationLevel
        fields = ("id", "name", "slug", "order")


class GradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grade
        fields = ("id", "education_level", "name", "slug", "order")


class ChildSerializer(serializers.ModelSerializer):
    education_level_name = serializers.CharField(source="education_level.name", read_only=True)
    grade_name = serializers.CharField(source="grade.name", read_only=True)

    class Meta:
        model = Child
        fields = ("id", "name", "birth_date", "education_level", "education_level_name", "grade", "grade_name", "created_at", "active")
        read_only_fields = ("id", "created_at", "education_level_name", "grade_name")

    def validate(self, attrs):
        level = attrs.get("education_level", getattr(self.instance, "education_level", None))
        grade = attrs.get("grade", getattr(self.instance, "grade", None))
        if bool(level) != bool(grade):
            raise serializers.ValidationError({"grade": "Informe o nível de ensino e a série/ano."})
        if level and grade and grade.education_level_id != level.id:
            raise serializers.ValidationError({"grade": "A série deve pertencer ao nível de ensino selecionado."})
        return attrs


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ("id", "name", "slug", "description", "icon", "order", "active")


class GradeSubjectSerializer(serializers.ModelSerializer):
    subject = SubjectSerializer(read_only=True)

    class Meta:
        model = GradeSubject
        fields = ("id", "grade", "subject", "order")


class UnitSerializer(serializers.ModelSerializer):
    subject_id = serializers.IntegerField(source="grade_subject.subject_id", read_only=True)
    grade_id = serializers.IntegerField(source="grade_subject.grade_id", read_only=True)

    class Meta:
        model = Unit
        fields = ("id", "grade_subject", "grade_id", "subject_id", "title", "description", "order")


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ("id", "unit", "title", "slug", "description", "order", "difficulty", "estimated_minutes")


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ("id", "topic", "title", "introduction", "explanation", "examples", "summary", "order", "estimated_minutes")


class PublicExerciseChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseChoice
        fields = ("id", "text", "order")


class StaffExerciseChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseChoice
        fields = ("id", "text", "is_correct", "order")


class ExerciseSerializer(serializers.ModelSerializer):
    choices = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        fields = ("id", "topic", "lesson", "statement", "exercise_type", "difficulty", "explanation", "order", "choices")

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if not request or not request.user.is_staff:
            fields.pop("explanation", None)
        return fields

    @extend_schema_field(PublicExerciseChoiceSerializer(many=True))
    def get_choices(self, obj):
        request = self.context.get("request")
        serializer = StaffExerciseChoiceSerializer if request and request.user.is_staff else PublicExerciseChoiceSerializer
        return serializer(obj.choices.all(), many=True).data

    def validate(self, attrs):
        topic = attrs.get("topic", getattr(self.instance, "topic", None))
        lesson = attrs.get("lesson", getattr(self.instance, "lesson", None))
        if lesson and topic and lesson.topic_id != topic.id:
            raise serializers.ValidationError({"lesson": "A aula deve pertencer ao mesmo conteúdo do exercício."})
        return attrs


class ExerciseAnswerSerializer(serializers.Serializer):
    answer = serializers.JSONField()


class TopicProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = TopicProgress
        fields = ("id", "topic", "completed", "completion_percentage", "completed_at", "last_accessed_at")


class LessonProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonProgress
        fields = ("id", "lesson", "completed", "completed_at")


class ExerciseAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExerciseAttempt
        fields = ("id", "exercise", "answer", "is_correct", "attempted_at")


class EducationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationProfile
        fields = ("role", "created_at")
        read_only_fields = ("created_at",)

    def validate_role(self, value):
        if self.instance and self.instance.role == EducationProfile.Role.TEACHER and value != self.instance.role and self.instance.user.taught_classrooms.exists():
            raise serializers.ValidationError("Não é possível mudar para aluno enquanto houver turmas criadas.")
        return value


class ClassroomStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationProfile._meta.get_field("user").remote_field.model
        fields = ("id", "username", "email")


class ClassroomActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomActivity
        fields = ("id", "classroom", "title", "description", "topic", "lesson", "exercise", "due_at", "created_at")
        read_only_fields = ("classroom", "created_at")

    def validate(self, attrs):
        references = [attrs.get("topic"), attrs.get("lesson"), attrs.get("exercise")]
        if sum(value is not None for value in references) != 1:
            raise serializers.ValidationError("Informe exatamente um conteúdo, aula ou exercício.")
        classroom = self.context.get("classroom")
        target = next(value for value in references if value is not None)
        topic = target if isinstance(target, Topic) else target.topic
        if classroom and topic.unit.grade_subject.grade_id != classroom.grade_id:
            raise serializers.ValidationError("O conteúdo deve pertencer à série da turma.")
        return attrs


class ClassroomSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.username", read_only=True)
    grade_name = serializers.CharField(source="grade.name", read_only=True)
    student_count = serializers.SerializerMethodField()
    students = serializers.SerializerMethodField()
    activities = ClassroomActivitySerializer(many=True, read_only=True)

    class Meta:
        model = Classroom
        fields = ("id", "teacher", "teacher_name", "name", "description", "grade", "grade_name", "code", "created_at", "active", "student_count", "students", "activities")
        read_only_fields = ("teacher", "code", "created_at", "student_count", "students", "activities")

    @extend_schema_field(ClassroomStudentSerializer(many=True))
    def get_students(self, obj):
        request = self.context.get("request")
        if not request or request.user.id != obj.teacher_id:
            return []
        return ClassroomStudentSerializer(obj.students.all(), many=True).data

    @extend_schema_field(serializers.IntegerField())
    def get_student_count(self, obj):
        return getattr(obj, "student_count", obj.memberships.count())


class JoinClassroomSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)

    def validate_code(self, value):
        return value.strip().upper()


class DiagnosticExerciseSerializer(serializers.ModelSerializer):
    choices = PublicExerciseChoiceSerializer(many=True, read_only=True)

    class Meta:
        model = Exercise
        fields = ("id", "statement", "exercise_type", "difficulty", "order", "choices")


class DiagnosticQuestionSerializer(serializers.ModelSerializer):
    exercise = DiagnosticExerciseSerializer(read_only=True)
    answered = serializers.SerializerMethodField()

    class Meta:
        model = DiagnosticResponse
        fields = ("order", "exercise", "answered")

    @extend_schema_field(serializers.BooleanField())
    def get_answered(self, obj):
        return obj.answered_at is not None


class DiagnosticAssessmentSerializer(serializers.ModelSerializer):
    questions = DiagnosticQuestionSerializer(source="responses", many=True, read_only=True)
    total_questions = serializers.IntegerField(source="responses.count", read_only=True)

    class Meta:
        model = DiagnosticAssessment
        fields = ("id", "topic", "started_at", "completed_at", "score", "percentage", "level", "total_questions", "questions")
        read_only_fields = fields


class DiagnosticAnswerSerializer(serializers.Serializer):
    exercise = serializers.IntegerField()
    answer = serializers.JSONField()


class QuestionBankExerciseSerializer(DiagnosticExerciseSerializer):
    topic_title = serializers.CharField(source="topic.title", read_only=True)
    unit_id = serializers.IntegerField(source="topic.unit_id", read_only=True)
    unit_title = serializers.CharField(source="topic.unit.title", read_only=True)
    grade_id = serializers.IntegerField(source="topic.unit.grade_subject.grade_id", read_only=True)
    grade_name = serializers.CharField(source="topic.unit.grade_subject.grade.name", read_only=True)
    education_level_id = serializers.IntegerField(source="topic.unit.grade_subject.grade.education_level_id", read_only=True)
    education_level_name = serializers.CharField(source="topic.unit.grade_subject.grade.education_level.name", read_only=True)
    subject_id = serializers.IntegerField(source="topic.unit.grade_subject.subject_id", read_only=True)
    subject_name = serializers.CharField(source="topic.unit.grade_subject.subject.name", read_only=True)

    class Meta(DiagnosticExerciseSerializer.Meta):
        fields = DiagnosticExerciseSerializer.Meta.fields + ("topic", "topic_title", "unit_id", "unit_title", "grade_id", "grade_name", "education_level_id", "education_level_name", "subject_id", "subject_name")


class AssignmentSerializer(serializers.ModelSerializer):
    exercise_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    question_count = serializers.IntegerField(source="assignment_exercises.count", read_only=True)
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)

    class Meta:
        model = Assignment
        fields = ("id", "teacher", "classroom", "classroom_name", "title", "description", "available_from", "due_date", "created_at", "exercise_ids", "question_count")
        read_only_fields = ("teacher", "created_at")

    def create(self, validated_data):
        exercise_ids = validated_data.pop("exercise_ids", [])
        from .services import create_assignment
        return create_assignment(self.context["request"].user, validated_data, exercise_ids)


class AssignmentQuestionSerializer(serializers.ModelSerializer):
    exercise = DiagnosticExerciseSerializer(read_only=True)

    class Meta:
        model = AssignmentExercise
        fields = ("order", "exercise")


class StudentAssignmentResponseSerializer(serializers.ModelSerializer):
    exercise = DiagnosticExerciseSerializer(read_only=True)
    answered = serializers.SerializerMethodField()

    class Meta:
        model = StudentAssignmentResponse
        fields = ("exercise", "answer", "answered", "is_correct")

    def get_fields(self):
        fields = super().get_fields()
        if not self.context.get("submitted", False):
            fields.pop("is_correct", None)
        return fields

    @extend_schema_field(serializers.BooleanField())
    def get_answered(self, obj):
        return obj.answered_at is not None


class StudentAssignmentSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="assignment.title", read_only=True)
    description = serializers.CharField(source="assignment.description", read_only=True)
    due_date = serializers.DateTimeField(source="assignment.due_date", read_only=True)
    classroom_name = serializers.CharField(source="assignment.classroom.name", read_only=True)
    total_questions = serializers.IntegerField(source="responses.count", read_only=True)
    correct = serializers.SerializerMethodField()
    errors = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()
    responses = serializers.SerializerMethodField()

    class Meta:
        model = StudentAssignment
        fields = ("id", "assignment", "title", "description", "classroom_name", "due_date", "started_at", "submitted_at", "score", "percentage", "total_questions", "correct", "errors", "duration_seconds", "responses")

    @extend_schema_field(serializers.IntegerField())
    def get_correct(self, obj):
        return obj.score if obj.submitted_at else 0

    @extend_schema_field(serializers.IntegerField())
    def get_errors(self, obj):
        return obj.responses.count() - obj.score if obj.submitted_at else 0

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_duration_seconds(self, obj):
        return int((obj.submitted_at - obj.started_at).total_seconds()) if obj.submitted_at else None

    @extend_schema_field(StudentAssignmentResponseSerializer(many=True))
    def get_responses(self, obj):
        return StudentAssignmentResponseSerializer(obj.responses.select_related("exercise").prefetch_related("exercise__choices"), many=True, context={"submitted": bool(obj.submitted_at)}).data


class AssignmentAnswerSerializer(serializers.Serializer):
    exercise = serializers.IntegerField()
    answer = serializers.JSONField()


class ErrorNotebookSerializer(serializers.Serializer):
    exercise = serializers.IntegerField()
    statement = serializers.CharField()
    exercise_type = serializers.CharField()
    difficulty = serializers.CharField()
    topic = serializers.IntegerField()
    topic_title = serializers.CharField()
    subject = serializers.IntegerField()
    subject_name = serializers.CharField()
    error_count = serializers.IntegerField()
    last_attempt = serializers.DateTimeField()


class ReviewQueueSerializer(serializers.Serializer):
    topic = serializers.IntegerField()
    topic_title = serializers.CharField()
    subject = serializers.IntegerField()
    subject_name = serializers.CharField()
    attempts = serializers.IntegerField()
    correct = serializers.IntegerField()
    errors = serializers.IntegerField()
    accuracy_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    last_attempt = serializers.DateTimeField()
    days_since_last_review = serializers.IntegerField()
    priority_score = serializers.DecimalField(max_digits=6, decimal_places=2)
    priority = serializers.ChoiceField(choices=("high", "medium", "low"))
    reason = serializers.CharField()


class RecommendationSerializer(serializers.Serializer):
    topic = serializers.IntegerField()
    topic_title = serializers.CharField()
    subject = serializers.IntegerField()
    subject_name = serializers.CharField()
    priority = serializers.ChoiceField(choices=("high", "medium", "low"))
    priority_score = serializers.DecimalField(max_digits=6, decimal_places=2)
    reason = serializers.CharField()
    accuracy = serializers.IntegerField(allow_null=True)
    recent_errors = serializers.IntegerField()
    recent_questions = serializers.IntegerField()
    diagnostic_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    completion_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    days_since_last_study = serializers.IntegerField()
    recommended_action = serializers.ChoiceField(choices=("review", "continue", "practice"))
