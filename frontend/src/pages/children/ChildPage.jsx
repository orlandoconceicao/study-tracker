import React, { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import EducationState from "../../components/education/EducationState";
import { collection, educationApi } from "../../services/education";
import { studiesApi } from "../../services/studies";

export default function ChildPage() {
  const { id } = useParams();
  const [data, setData] = useState({ child: null, subjects: [], progress: null, studies: [] });
  const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [child, subjects, progress, studies] = await Promise.all([
        educationApi.getChild(id), educationApi.getChildSubjects(id), educationApi.getChildProgress(id), studiesApi.list({ child: id }),
      ]);
      setData({ child: child.data, subjects: collection(subjects), progress: progress.data, studies: collection(studies) });
      localStorage.setItem("study_active_child", id);
    } catch { setError("Não foi possível acessar este filho."); }
    finally { setLoading(false); }
  }, [id]);
  useEffect(() => { load(); }, [load]);
  const { child, subjects, progress, studies } = data;
  return <section className="page-content classes-page"><Link className="back-link" to="/children">← Voltar para meus filhos</Link><EducationState loading={loading} error={error} loadingText="Carregando acompanhamento..." onRetry={load}>{child && progress && <>
    <header className="classroom-hero card"><div><span className="eyebrow">{child.education_level_name}</span><h1>{child.name}</h1><p>{child.grade_name}</p></div><Link className="button" to="/learn">Iniciar aula de apoio</Link></header>
    <div className="progress-metrics child-progress"><div><strong>{progress.topics_started}</strong><span>Conteúdos estudados</span></div><div><strong>{progress.lessons_completed}</strong><span>Aulas realizadas</span></div><div><strong>{progress.exercises_attempted}</strong><span>Exercícios feitos</span></div><div><strong>{progress.exercises_correct}</strong><span>Acertos</span></div><div><strong>{progress.exercises_attempted - progress.exercises_correct}</strong><span>Erros</span></div></div>
    <section className="class-section card"><div className="section-heading"><div><span className="eyebrow">ESCOLARIDADE</span><h2>Matérias de {child.name}</h2></div></div>{subjects.length ? <div className="class-subjects">{subjects.map((item) => <Link key={item.id} to={`/learn/subject/${item.id}`} state={{ gradeSubject: item, grade: { id: child.grade, name: child.grade_name } }}>{item.subject.name}<span>→</span></Link>)}</div> : <p className="muted">Nenhuma matéria cadastrada para esta série.</p>}</section>
    <section className="class-section card"><span className="eyebrow">EXERCÍCIOS</span><h2>Acertos e dificuldades recentes</h2>{progress.recent_attempts.length ? <div className="activity-list">{progress.recent_attempts.map((attempt, index) => <article key={`${attempt.attempted_at}-${index}`}><div><strong>{attempt.exercise}</strong><small>{new Date(attempt.attempted_at).toLocaleString("pt-BR")}</small></div><span className={attempt.correct ? "status-pill" : "priority-pill high"}>{attempt.correct ? "Acertou" : "Errou"}</span></article>)}</div> : <p className="muted">Ainda não há exercícios realizados para este filho.</p>}</section>
    <section className="class-section card"><div className="section-heading"><div><span className="eyebrow">ESTUDOS</span><h2>Histórico de estudos</h2></div><Link className="button" to="/studies/new">Registrar estudo</Link></div>{studies.length ? <div className="studies-list">{studies.map((study) => <article className="study-record" key={study.id}><div className="study-mark">{study.subject.slice(0, 1).toUpperCase()}</div><div className="study-record-content"><h3>{study.subject}</h3><p>{new Date(`${study.date}T12:00`).toLocaleDateString("pt-BR")} · {study.duration_minutes} minutos</p>{study.notes && <p className="study-notes">{study.notes}</p>}</div></article>)}</div> : <p className="muted">Nenhuma sessão de estudo registrada para este filho.</p>}</section>
  </>}</EducationState></section>;
}
