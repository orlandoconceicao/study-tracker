import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import DiagnosticQuestion from "./DiagnosticQuestion";

describe("DiagnosticQuestion", () => {
  it("collects an existing multiple-choice option without answer metadata", () => {
    const onChange = vi.fn();
    const question = { exercise: { id: 1, statement: "Questão", exercise_type: "multiple_choice", choices: [{ id: 2, text: "Alternativa" }] } };
    render(<DiagnosticQuestion question={question} value={null} onChange={onChange} />);
    expect(question.exercise.choices[0]).not.toHaveProperty("is_correct");
    fireEvent.click(screen.getByLabelText("Alternativa"));
    expect(onChange).toHaveBeenCalledWith(2);
  });

  it("collects boolean and short answers", () => {
    const booleanChange = vi.fn();
    const { rerender } = render(<DiagnosticQuestion question={{ exercise: { id: 2, statement: "Verdade?", exercise_type: "true_false" } }} value={null} onChange={booleanChange} />);
    fireEvent.click(screen.getByLabelText("Falso"));
    expect(booleanChange).toHaveBeenCalledWith(false);
    const textChange = vi.fn();
    rerender(<DiagnosticQuestion question={{ exercise: { id: 3, statement: "Explique", exercise_type: "short_answer" } }} value="" onChange={textChange} />);
    fireEvent.change(screen.getByPlaceholderText("Digite sua resposta"), { target: { value: "Minha resposta" } });
    expect(textChange).toHaveBeenCalledWith("Minha resposta");
  });
});
