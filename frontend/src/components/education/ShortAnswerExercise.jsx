import React, { useState } from "react";
import { educationApi } from "../../services/education";
import ExerciseFeedback from "./ExerciseFeedback";
import RevealAnswer from "./RevealAnswer";

export default function ShortAnswerExercise({ exercise, onAnswered }) {
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event) => { event.preventDefault(); if (!answer.trim()) return; setLoading(true); setError(""); try { const response = await educationApi.submitExerciseAnswer(exercise.id, answer.trim()); setResult(response.data); onAnswered?.(); } catch { setError("Não foi possível enviar sua resposta."); } finally { setLoading(false); } };
  return <form className="exercise-card card" onSubmit={submit}><label className="short-answer"><strong>{exercise.statement}</strong><textarea rows="3" value={answer} disabled={loading || Boolean(result)} onChange={(event) => setAnswer(event.target.value)} placeholder="Digite sua resposta" /></label>{error && <p className="form-error">{error}</p>}<ExerciseFeedback result={result} />{!result && <div className="exercise-actions"><button type="submit" disabled={!answer.trim() || loading}>{loading ? "Enviando..." : "Responder"}</button><RevealAnswer exercise={exercise} /></div>}</form>;
}
