import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import EducationState from "../../components/education/EducationState";
import ProgressBar from "../../components/education/ProgressBar";
import { collection, educationApi } from "../../services/education";

const priorities = { high: "Prioridade alta", medium: "Prioridade média", low: "Prioridade baixa" };

export default function ReviewPage() {
  const [items, setItems] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = useCallback(() => { setLoading(true); setError(""); educationApi.getReviewQueue().then((response) => setItems(collection(response))).catch(() => setError("Não foi possível carregar sua fila de revisão.")).finally(() => setLoading(false)); }, []); useEffect(load, [load]);
  return <section className="page-content review-page"><header className="page-hero"><div><span className="eyebrow">REVISÃO</span><h1>Conteúdos para revisar hoje</h1><p>Prioridades calculadas a partir do seu desempenho e progresso.</p></div><Link className="button secondary-button" to="/review/errors">Ver caderno de erros</Link></header><EducationState loading={loading} error={error} loadingText="Preparando sua revisão..." onRetry={load}>{items.length ? <div className="review-grid">{items.map((item) => <article className="review-card card" key={item.topic}><div><span className={`priority-pill ${item.priority}`}>{priorities[item.priority]}</span><span className="eyebrow">{item.subject_name}</span><h2>{item.topic_title}</h2><p>{item.reason}</p></div><div className="review-performance"><span>{item.correct} acertos em {item.attempts} tentativas</span><ProgressBar value={item.accuracy_percentage} label="Desempenho" /></div><Link className="button" to={`/learn/topic/${item.topic}`}>Revisar</Link></article>)}</div> : <div className="empty-state card"><h3>Nenhuma revisão pendente.</h3><p>Continue estudando; seus erros futuros aparecerão aqui como oportunidades de aprendizado.</p><Link className="button" to="/learn">Continuar estudando</Link></div>}</EducationState></section>;
}
