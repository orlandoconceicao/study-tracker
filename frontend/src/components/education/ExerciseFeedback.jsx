import React from "react";

const answerText = (answer) => Array.isArray(answer) ? answer.join(", ") : typeof answer === "boolean" ? (answer ? "Verdadeiro" : "Falso") : String(answer ?? "");

export default function ExerciseFeedback({ result }) {
  if (!result) return null;
  return <div className={`exercise-feedback ${result.correct ? "correct" : "incorrect"}`} role="status"><strong>{result.correct ? "Resposta correta" : "Resposta incorreta"}</strong>{!result.correct && <p>Resposta correta: {answerText(result.correct_answer)}</p>}{result.explanation && <p>{result.explanation}</p>}</div>;
}
