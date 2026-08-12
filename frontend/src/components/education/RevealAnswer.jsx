import React, { useState } from "react";
import { educationApi } from "../../services/education";

const answerText = (answer) => Array.isArray(answer) ? answer.join(", ") : typeof answer === "boolean" ? (answer ? "Verdadeiro" : "Falso") : String(answer ?? "");

export default function RevealAnswer({ exercise }) {
  const [result, setResult] = useState(null); const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  const reveal = async () => { setLoading(true); setError(""); try { const response = await educationApi.revealExerciseAnswer(exercise.id); setResult(response.data); } catch { setError("Não foi possível mostrar a resposta."); } finally { setLoading(false); } };
  if (result) return <div className="exercise-reveal" role="status"><strong>Resposta: {answerText(result.correct_answer)}</strong>{result.explanation && <p>{result.explanation}</p>}</div>;
  return <><button type="button" className="secondary-button" disabled={loading} onClick={reveal}>{loading ? "Carregando..." : "Mostrar resposta"}</button>{error && <p className="form-error">{error}</p>}</>;
}
