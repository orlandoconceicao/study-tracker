import React, { useState } from "react";
import { educationApi } from "../../services/education";
import ExerciseFeedback from "./ExerciseFeedback";

export default function TrueFalseExercise({ exercise, onAnswered }) {
  const [answer, setAnswer] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event) => { event.preventDefault(); if (answer === null) return; setLoading(true); setError(""); try { const response = await educationApi.submitExerciseAnswer(exercise.id, answer); setResult(response.data); onAnswered?.(); } catch { setError("Não foi possível enviar sua resposta."); } finally { setLoading(false); } };
  return <form className="exercise-card card" onSubmit={submit}><fieldset disabled={loading || Boolean(result)}><legend>{exercise.statement}</legend><div className="boolean-choices"><label><input type="radio" name={`exercise-${exercise.id}`} checked={answer === true} onChange={() => setAnswer(true)} /> Verdadeiro</label><label><input type="radio" name={`exercise-${exercise.id}`} checked={answer === false} onChange={() => setAnswer(false)} /> Falso</label></div></fieldset>{error && <p className="form-error">{error}</p>}<ExerciseFeedback result={result} />{!result && <button type="submit" disabled={answer === null || loading}>{loading ? "Enviando..." : "Responder"}</button>}</form>;
}
