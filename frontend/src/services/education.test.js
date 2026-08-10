import { beforeEach, describe, expect, it, vi } from "vitest";
import api from "./api";
import { educationApi } from "./education";

vi.mock("./api", () => ({ default: { get: vi.fn(), post: vi.fn() } }));

describe("educationApi", () => {
  beforeEach(() => vi.clearAllMocks());

  it("uses the shared API client for curriculum and progress", () => {
    educationApi.getLevels(); educationApi.getGrades(); educationApi.getGradeSubjects(3);
    educationApi.getUnits(8, 3); educationApi.getTopic(5); educationApi.getTopicLessons(5);
    educationApi.getLesson(7); educationApi.getTopicExercises(5); educationApi.getEducationProgress();
    educationApi.completeLesson(7); educationApi.submitExerciseAnswer(9, "resposta");
    educationApi.getQuestions({ difficulty: "hard" });
    educationApi.createAssignment({ title: "Lista", exercise_ids: [9] });
    educationApi.startAssignment(4);
    educationApi.answerAssignment(6, 9, "resposta");
    educationApi.submitAssignment(6);
    educationApi.getReviewQueue(); educationApi.getErrorNotebook();
    educationApi.getRecommendations({ classroom: 2, student: 3 }); educationApi.getLessonPlan(5, 2);
    expect(api.get).toHaveBeenCalledWith("/education/levels/");
    expect(api.get).toHaveBeenCalledWith("/education/grades/3/subjects/");
    expect(api.get).toHaveBeenCalledWith("/education/subjects/8/units/", { params: { grade: 3 } });
    expect(api.get).toHaveBeenCalledWith("/education/topics/5/exercises/");
    expect(api.get).toHaveBeenCalledWith("/education/progress/", { params: { child: undefined } });
    expect(api.post).toHaveBeenCalledWith("/education/lessons/7/complete/", { child: undefined });
    expect(api.post).toHaveBeenCalledWith("/education/exercises/9/answer/", { answer: "resposta", child: undefined });
    expect(api.get).toHaveBeenCalledWith("/education/questions/", { params: { difficulty: "hard" } });
    expect(api.post).toHaveBeenCalledWith("/education/assignments/", { title: "Lista", exercise_ids: [9] });
    expect(api.post).toHaveBeenCalledWith("/education/student-assignments/6/answer/", { exercise: 9, answer: "resposta" });
    expect(api.get).toHaveBeenCalledWith("/education/review/", { params: { child: undefined } });
    expect(api.get).toHaveBeenCalledWith("/education/review/errors/", { params: { child: undefined } });
    expect(api.get).toHaveBeenCalledWith("/education/recommendations/", { params: { classroom: 2, student: 3, child: undefined } });
    expect(api.get).toHaveBeenCalledWith("/education/recommendations/lesson-plan/", { params: { topic: 5, classroom: 2, child: undefined } });
  });
});
