import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import EducationState from "../../components/education/EducationState";
import { collection, educationApi } from "../../services/education";

const types = { multiple_choice: "Múltipla escolha", true_false: "Verdadeiro ou falso", short_answer: "Resposta curta" };

export default function ErrorNotebookPage() {
  const [errors, setErrors] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = useCallback(() => { setLoading(true); setError(""); educationApi.getErrorNotebook().then((response) => setErrors(collection(response))).catch(() => setError("Não foi possível carregar seu caderno de erros.")).finally(() => setLoading(false)); }, []); useEffect(load, [load]);
  return <section className="page-content review-page"><header className="page-hero"><div><span className="eyebrow">REVISÃO</span><h1>Caderno de erros</h1><p>Refaça questões e acompanhe os pontos que merecem mais atenção.</p></div><Link className="button secondary-button" to="/review">Fila de revisão</Link></header><EducationState loading={loading} error={error} loadingText="Carregando seu caderno de erros..." onRetry={load}>{errors.length ? <div className="error-notebook">{errors.map((item) => <article className="error-card card" key={item.exercise}><div className="error-card-heading"><div><span className="eyebrow">{item.subject_name}</span><h2>{item.topic_title}</h2></div><strong>{item.error_count} {item.error_count === 1 ? "erro" : "erros"}</strong></div><p className="error-statement">{item.statement}</p><div className="error-meta"><span>{types[item.exercise_type] || item.exercise_type}</span><span>Última tentativa: {new Date(item.last_attempt).toLocaleDateString("pt-BR")}</span></div><Link className="button" to={`/learn/topic/${item.topic}`}>Revisar</Link></article>)}</div> : <div className="empty-state card"><h3>Seu caderno de erros está vazio.</h3><p>Quando uma questão precisar de revisão, ela aparecerá aqui.</p></div>}</EducationState></section>;
}
