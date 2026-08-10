import React from "react";
import { Link } from "react-router-dom";
import ProgressBar from "./ProgressBar";

const difficultyLabels = { easy: "Fácil", medium: "Médio", hard: "Difícil" };

export default function TopicItem({ topic, progress, context }) {
  return <li className="topic-item"><div className="topic-copy"><Link to={`/learn/topic/${topic.id}`} state={context}>{topic.title}</Link><div className="topic-meta"><span className={`difficulty ${topic.difficulty}`}>{difficultyLabels[topic.difficulty] || topic.difficulty}</span>{topic.estimated_minutes > 0 && <span>{topic.estimated_minutes} min</span>}{progress?.completed && <span className="completed-mark">✓ Concluído</span>}</div><ProgressBar value={progress?.completion_percentage} /></div><Link className="topic-arrow" aria-label={`Abrir ${topic.title}`} to={`/learn/topic/${topic.id}`} state={context}>→</Link></li>;
}
