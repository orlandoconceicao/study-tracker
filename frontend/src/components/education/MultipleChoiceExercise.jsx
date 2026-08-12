import React, { useState } from "react";
import { educationApi } from "../../services/education";
import ExerciseFeedback from "./ExerciseFeedback";
import RevealAnswer from "./RevealAnswer";

export default function MultipleChoiceExercise({ exercise, onAnswered }) {
  const [answer, setAnswer] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const submit = async (event) => { event.preventDefault(); if (!answer) return; setLoading(true); setError(""); try { const response = await educationApi.submitExerciseAnswer(exercise.id, Number(answer)); const ids = Array.isArray(response.data.correct_answer) ? response.data.correct_answer : [response.data.correct_answer]; setResult({ ...response.data, correct_answer: exercise.choices.filter((choice) => ids.includes(choice.id)).map((choice) => choice.text) }); onAnswered?.(); } catch { setError("Não foi possível enviar sua resposta."); } finally { setLoading(false); } };
  return <form className="exercise-card card" onSubmit={submit}><fieldset disabled={loading || Boolean(result)}><legend>{exercise.statement}</legend><div className="choice-list">{exercise.choices.map((choice) => <label key={choice.id}><input type="radio" name={`exercise-${exercise.id}`} value={choice.id} checked={String(answer) === String(choice.id)} onChange={(event) => setAnswer(event.target.value)} /><span>{choice.text}</span></label>)}</div></fieldset>{error && <p className="form-error">{error}</p>}<ExerciseFeedback result={result} />{!result && <div className="exercise-actions"><button type="submit" disabled={!answer || loading}>{loading ? "Enviando..." : "Responder"}</button><RevealAnswer exercise={exercise} /></div>}</form>;
}
