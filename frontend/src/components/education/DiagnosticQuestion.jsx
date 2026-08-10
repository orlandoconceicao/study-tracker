import React from "react";

export default function DiagnosticQuestion({ question, value, onChange, disabled }) {
  const exercise = question.exercise;
  if (exercise.exercise_type === "multiple_choice") return <fieldset className="diagnostic-question" disabled={disabled}><legend>{exercise.statement}</legend><div className="choice-list">{exercise.choices.map((choice) => <label key={choice.id}><input type="radio" name={`diagnostic-${exercise.id}`} checked={String(value) === String(choice.id)} onChange={() => onChange(choice.id)} /><span>{choice.text}</span></label>)}</div></fieldset>;
  if (exercise.exercise_type === "true_false") return <fieldset className="diagnostic-question" disabled={disabled}><legend>{exercise.statement}</legend><div className="boolean-choices"><label><input type="radio" name={`diagnostic-${exercise.id}`} checked={value === true} onChange={() => onChange(true)} /> Verdadeiro</label><label><input type="radio" name={`diagnostic-${exercise.id}`} checked={value === false} onChange={() => onChange(false)} /> Falso</label></div></fieldset>;
  return <label className="diagnostic-question short-answer"><strong>{exercise.statement}</strong><textarea rows="4" disabled={disabled} value={value || ""} onChange={(event) => onChange(event.target.value)} placeholder="Digite sua resposta" /></label>;
}
