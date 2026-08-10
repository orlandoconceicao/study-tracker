import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { educationApi } from "../../services/education";
import MultipleChoiceExercise from "./MultipleChoiceExercise";
import ShortAnswerExercise from "./ShortAnswerExercise";
import TrueFalseExercise from "./TrueFalseExercise";

vi.mock("../../services/education", () => ({ educationApi: { submitExerciseAnswer: vi.fn() } }));

describe("education exercises", () => {
  beforeEach(() => educationApi.submitExerciseAnswer.mockResolvedValue({ data: { correct: true, correct_answer: true, explanation: "Muito bem." } }));

  it("submits a multiple choice id and reveals feedback only afterwards", async () => {
    const exercise = { id: 1, statement: "Quanto é 2 + 2?", choices: [{ id: 10, text: "4" }, { id: 11, text: "5" }] };
    render(<MultipleChoiceExercise exercise={exercise} />);
    expect(screen.queryByText("Muito bem.")).not.toBeInTheDocument();
    fireEvent.click(screen.getByLabelText("4")); fireEvent.click(screen.getByRole("button", { name: "Responder" }));
    await waitFor(() => expect(educationApi.submitExerciseAnswer).toHaveBeenCalledWith(1, 10));
    expect(await screen.findByText("Resposta correta")).toBeInTheDocument();
  });

  it("submits true or false as a boolean", async () => {
    render(<TrueFalseExercise exercise={{ id: 2, statement: "O céu é azul?" }} />);
    fireEvent.click(screen.getByLabelText("Verdadeiro")); fireEvent.click(screen.getByRole("button", { name: "Responder" }));
    await waitFor(() => expect(educationApi.submitExerciseAnswer).toHaveBeenCalledWith(2, true));
  });

  it("submits a trimmed short answer", async () => {
    render(<ShortAnswerExercise exercise={{ id: 3, statement: "Responda" }} />);
    fireEvent.change(screen.getByPlaceholderText("Digite sua resposta"), { target: { value: "  texto  " } }); fireEvent.click(screen.getByRole("button", { name: "Responder" }));
    await waitFor(() => expect(educationApi.submitExerciseAnswer).toHaveBeenCalledWith(3, "texto"));
  });
});
