import React from "react";
import { Link } from "react-router-dom";

export default function LessonItem({ lesson, index, completed, context }) {
  return <li className="lesson-item"><span className="lesson-number">{index + 1}</span><div><h3>{lesson.title}</h3><p>{lesson.estimated_minutes ? `${lesson.estimated_minutes} min` : "Tempo não informado"}{completed && <span className="completed-mark"> · ✓ Concluída</span>}</p></div><Link className="button secondary-button" to={`/learn/lesson/${lesson.id}`} state={context}>{completed ? "Continuar" : "Começar aula"}</Link></li>;
}
