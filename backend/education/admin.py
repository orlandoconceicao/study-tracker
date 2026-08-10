from django.contrib import admin

from .models import (Assignment, AssignmentExercise, Classroom, ClassroomActivity, ClassroomMembership, DiagnosticAssessment,
                     DiagnosticResponse, EducationLevel, EducationProfile, Exercise, ExerciseAttempt, ExerciseChoice, Grade,
                     GradeSubject, Lesson, LessonProgress, StudentAssignment,
                     StudentAssignmentResponse, Subject, Topic, TopicProgress, Unit)


class ExerciseChoiceInline(admin.TabularInline):
    model = ExerciseChoice
    extra = 1


@admin.register(EducationLevel)
class EducationLevelAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    search_fields = ("name",)
    ordering = ("order", "name")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ("name", "education_level", "order")
    search_fields = ("name", "education_level__name")
    list_filter = ("education_level",)
    ordering = ("education_level__order", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "active", "order")
    search_fields = ("name", "description")
    list_filter = ("active",)
    ordering = ("order", "name")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(GradeSubject)
class GradeSubjectAdmin(admin.ModelAdmin):
    list_display = ("grade", "subject", "order")
    search_fields = ("grade__name", "subject__name")
    list_filter = ("grade__education_level", "grade", "subject")
    ordering = ("grade__order", "order")


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("title", "grade_subject", "order")
    search_fields = ("title", "description", "grade_subject__subject__name")
    list_filter = ("grade_subject__grade", "grade_subject__subject")
    ordering = ("grade_subject", "order")


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("title", "unit", "difficulty", "estimated_minutes", "order")
    search_fields = ("title", "description", "unit__title")
    list_filter = ("difficulty", "unit__grade_subject__grade", "unit__grade_subject__subject")
    ordering = ("unit", "order")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "topic", "estimated_minutes", "order")
    search_fields = ("title", "introduction", "explanation", "topic__title")
    list_filter = ("topic__unit__grade_subject__grade", "topic__unit__grade_subject__subject")
    ordering = ("topic", "order")


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("short_statement", "topic", "exercise_type", "difficulty", "order")
    search_fields = ("statement", "explanation", "topic__title")
    list_filter = ("exercise_type", "difficulty", "topic__unit__grade_subject__subject")
    ordering = ("topic", "order")
    inlines = (ExerciseChoiceInline,)

    @admin.display(description="Enunciado")
    def short_statement(self, obj):
        return str(obj)


@admin.register(ExerciseChoice)
class ExerciseChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "exercise", "is_correct", "order")
    search_fields = ("text", "exercise__statement")
    list_filter = ("is_correct",)
    ordering = ("exercise", "order")


@admin.register(ExerciseAttempt)
class ExerciseAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "exercise", "is_correct", "attempted_at")
    search_fields = ("user__username", "exercise__statement")
    list_filter = ("is_correct", "attempted_at")
    ordering = ("-attempted_at",)
    readonly_fields = ("user", "exercise", "answer", "is_correct", "attempted_at")


@admin.register(TopicProgress)
class TopicProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "completion_percentage", "completed", "last_accessed_at")
    search_fields = ("user__username", "topic__title")
    list_filter = ("completed",)
    ordering = ("-last_accessed_at",)


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "completed", "completed_at")
    search_fields = ("user__username", "lesson__title")
    list_filter = ("completed",)


class ClassroomMembershipInline(admin.TabularInline):
    model = ClassroomMembership
    extra = 0


class ClassroomActivityInline(admin.TabularInline):
    model = ClassroomActivity
    extra = 0


@admin.register(EducationProfile)
class EducationProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "created_at")
    search_fields = ("user__username", "user__email")
    list_filter = ("role",)


@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ("name", "teacher", "grade", "code", "active", "created_at")
    search_fields = ("name", "teacher__username", "code")
    list_filter = ("active", "grade", "created_at")
    ordering = ("-created_at",)
    readonly_fields = ("code", "created_at")
    inlines = (ClassroomMembershipInline, ClassroomActivityInline)


@admin.register(ClassroomMembership)
class ClassroomMembershipAdmin(admin.ModelAdmin):
    list_display = ("classroom", "student", "joined_at")
    search_fields = ("classroom__name", "student__username", "student__email")


@admin.register(ClassroomActivity)
class ClassroomActivityAdmin(admin.ModelAdmin):
    list_display = ("title", "classroom", "due_at", "created_at")
    search_fields = ("title", "classroom__name")
    list_filter = ("classroom", "due_at")


class DiagnosticResponseInline(admin.TabularInline):
    model = DiagnosticResponse
    extra = 0
    readonly_fields = ("exercise", "order", "answer", "is_correct", "answered_at")


@admin.register(DiagnosticAssessment)
class DiagnosticAssessmentAdmin(admin.ModelAdmin):
    list_display = ("user", "topic", "score", "percentage", "level", "started_at", "completed_at")
    search_fields = ("user__username", "topic__title")
    list_filter = ("level", "completed_at")
    readonly_fields = ("started_at", "completed_at", "score", "percentage", "level")
    inlines = (DiagnosticResponseInline,)


@admin.register(DiagnosticResponse)
class DiagnosticResponseAdmin(admin.ModelAdmin):
    list_display = ("assessment", "exercise", "order", "is_correct", "answered_at")
    list_filter = ("is_correct", "answered_at")
    readonly_fields = ("assessment", "exercise", "order", "answer", "is_correct", "answered_at")


class AssignmentExerciseInline(admin.TabularInline):
    model = AssignmentExercise
    extra = 1


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "teacher", "classroom", "available_from", "due_date", "created_at")
    search_fields = ("title", "teacher__username", "classroom__name")
    list_filter = ("classroom", "available_from", "due_date")
    inlines = (AssignmentExerciseInline,)


class StudentAssignmentResponseInline(admin.TabularInline):
    model = StudentAssignmentResponse
    extra = 0
    readonly_fields = ("exercise", "answer", "is_correct", "answered_at")


@admin.register(StudentAssignment)
class StudentAssignmentAdmin(admin.ModelAdmin):
    list_display = ("assignment", "student", "score", "percentage", "started_at", "submitted_at")
    search_fields = ("assignment__title", "student__username")
    list_filter = ("submitted_at", "assignment__classroom")
    readonly_fields = ("score", "percentage", "started_at", "submitted_at")
    inlines = (StudentAssignmentResponseInline,)


@admin.register(AssignmentExercise)
class AssignmentExerciseAdmin(admin.ModelAdmin):
    list_display = ("assignment", "exercise", "order")


@admin.register(StudentAssignmentResponse)
class StudentAssignmentResponseAdmin(admin.ModelAdmin):
    list_display = ("student_assignment", "exercise", "is_correct", "answered_at")
    readonly_fields = ("student_assignment", "exercise", "answer", "is_correct", "answered_at")
