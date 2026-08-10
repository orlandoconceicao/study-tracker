import React, { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import EducationState from "../../components/education/EducationState";
import { educationApi } from "../../services/education";

export default function SupportLessonPage() {
  const { topicId } = useParams();
  const location = useLocation();
  const [plan, setPlan] = useState(null);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [finished, setFinished] = useState(false);

  const load = () => {
    setLoading(true); setError("");
    educationApi.getLessonPlan(topicId)
      .then((response) => setPlan(response.data))
      .catch((requestError) => setError(requestError.response?.data?.detail || "Não foi possível preparar a aula de apoio."))
      .finally(() => setLoading(false));
  };
  useEffect(load, [topicId]);

  const finish = async () => {
    if (!plan?.lesson) return;
    setSaving(true); setActionError("");
    try { await educationApi.completeLesson(plan.lesson); setFinished(true); }
    catch { setActionError("Não foi possível finalizar a aula."); }
    finally { setSaving(false); }
  };

  const current = plan?.steps[step];
  return <section className="page-content support-lesson-page">
    <Link className="back-link" to="/support">← Escolher outro conteúdo</Link>
    <EducationState loading={loading} error={error} loadingText="Montando aula de apoio..." onRetry={load}>
      {plan && <>
        <header className="page-hero"><div><span className="eyebrow">AULA DE APOIO</span><h1>{plan.topic_title}</h1><p>{location.state?.child?.name ? `Ensinando ${location.state.child.name}` : "Roteiro para o responsável conduzir a aula."}</p></div><span className="status-pill">{step + 1} de {plan.steps.length}</span></header>
        {!plan.sufficient_material && <div className="settings-info support-warning" role="status"><p>Este conteúdo ainda não possui material suficiente para uma aula de apoio.</p></div>}
        <article className="card support-step"><span className="lesson-block-number">{step + 1}</span><div><span className="eyebrow">ETAPA</span><h2>{current.title}</h2>{current.content && <p>{current.content}</p>}{current.exercise && <p className="support-exercise">{current.exercise}</p>}{current.exercises?.map((exercise) => <p className="support-exercise" key={exercise.id}>{exercise.statement}</p>)}{!current.available && <p className="muted">Não há material cadastrado para esta etapa.</p>}</div></article>
        {actionError && <p className="form-error" role="alert">{actionError}</p>}
        {finished ? <div className="success-message" role="status">Aula finalizada e registrada para este filho.</div> : <nav className="support-navigation"><button type="button" className="secondary-button" disabled={step === 0} onClick={() => setStep((value) => value - 1)}>Anterior</button>{step < plan.steps.length - 1 ? <button type="button" onClick={() => setStep((value) => value + 1)}>Próximo</button> : <button type="button" disabled={!plan.lesson || saving} onClick={finish}>{saving ? "Finalizando..." : "Finalizar aula"}</button>}<Link className="button secondary-button" to={`/learn/topic/${topicId}`} state={location.state}>Ir para exercícios</Link></nav>}
      </>}
    </EducationState>
  </section>;
}
