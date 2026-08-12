import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import Breadcrumb from "../../components/education/Breadcrumb";
import EducationState from "../../components/education/EducationState";
import MultipleChoiceExercise from "../../components/education/MultipleChoiceExercise";
import ShortAnswerExercise from "../../components/education/ShortAnswerExercise";
import TrueFalseExercise from "../../components/education/TrueFalseExercise";
import { collection, educationApi } from "../../services/education";

const exerciseComponents = { multiple_choice: MultipleChoiceExercise, true_false: TrueFalseExercise, short_answer: ShortAnswerExercise };
const difficultyLabels = { easy: "Fácil", medium: "Médio", hard: "Difícil" };
const paragraphs = (value) => (value || "").split(/\n\s*\n/).map((item) => item.trim()).filter(Boolean);

export default function TopicPage() {
  const { topicId } = useParams(); const location = useLocation(); const context = location.state || {};
  const [topic, setTopic] = useState(null); const [lessons, setLessons] = useState([]); const [exercises, setExercises] = useState([]); const [allTopics, setAllTopics] = useState([]);
  const [summary, setSummary] = useState(null); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const refreshProgress = useCallback(() => educationApi.getTopicSummary(topicId).then((response) => setSummary(response.data)).catch(() => {}), [topicId]);
  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const topicResponse = await educationApi.getTopic(topicId);
      const [lessonResponse, exerciseResponse, topicsResponse] = await Promise.all([educationApi.getTopicLessons(topicId), educationApi.getTopicExercises(topicId), educationApi.getTopics({ unit: topicResponse.data.unit })]);
      setTopic(topicResponse.data); setLessons(collection(lessonResponse)); setExercises(collection(exerciseResponse)); setAllTopics(collection(topicsResponse));
      try { setSummary((await educationApi.getTopicSummary(topicId)).data); } catch { setSummary(null); }
    } catch { setError("Não foi possível carregar este conteúdo."); }
    finally { setLoading(false); }
  }, [topicId]);
  useEffect(() => { load(); }, [load]);
  const siblings = useMemo(() => allTopics.filter((item) => item.unit === topic?.unit), [allTopics, topic]);
  const index = siblings.findIndex((item) => String(item.id) === String(topicId)); const previous = index > 0 ? siblings[index - 1] : null; const next = index >= 0 && index < siblings.length - 1 ? siblings[index + 1] : null;
  const subjectName = context.gradeSubject?.subject.name || topic?.subject_name; const gradeName = context.grade?.name || topic?.grade_name; const gradeSubjectId = context.gradeSubject?.id || topic?.grade_subject;
  return <section className="page-content topic-reading-page"><Breadcrumb items={[{ label: subjectName, to: gradeSubjectId && `/learn/subject/${gradeSubjectId}`, state: context }, { label: topic?.title }]} /><EducationState loading={loading} error={error} loadingText="Carregando conteúdo..." onRetry={load}>{topic && <>
    <header className="card topic-landing-hero"><span className="eyebrow">CONTEÚDO</span><h1>{topic.title}</h1><p>{subjectName} · {gradeName}</p><div className="topic-meta"><span className={`difficulty ${topic.difficulty}`}>{difficultyLabels[topic.difficulty]}</span>{topic.estimated_minutes > 0 && <span>{topic.estimated_minutes} min</span>}</div><div className="topic-actions"><Link className="button" to={`/support/${topic.id}`} state={context}>Ensinar em aula de apoio</Link><Link className="button secondary-button" to={`/learn/topic/${topic.id}/diagnostic`} state={{ ...context, topic }}>Diagnóstico opcional</Link></div></header>
    {summary && <section className="topic-summary card"><div><strong>{summary.exercises_attempted} de {summary.total_exercises}</strong><span>Exercícios realizados</span></div><div><strong>{summary.correct}</strong><span>Acertos</span></div><div><strong>{summary.errors}</strong><span>Erros</span></div><div><strong>{summary.accuracy_percentage}%</strong><span>Aproveitamento</span></div></section>}
    <section className="education-section reading-section"><div className="section-heading"><div><span className="eyebrow">EXPLICAÇÃO DIDÁTICA</span><h2>Aprenda o conteúdo</h2></div></div>{lessons.length ? <div className="lesson-reading-stack">{lessons.map((lesson) => <article className="card lesson-reading" key={lesson.id}><h2>{lesson.title}</h2>{lesson.introduction && <section><h3>O que vamos aprender?</h3><p>{lesson.introduction}</p></section>}{lesson.importance && <section><h3>Por que isso é importante?</h3><p>{lesson.importance}</p></section>}<section><h3>Explicação passo a passo</h3><p>{lesson.explanation}</p></section>{lesson.parent_guidance && <section><h3>Como explicar para seu filho</h3><p>{lesson.parent_guidance}</p></section>}{lesson.structured_examples?.length ? lesson.structured_examples.map((example) => <section className="worked-example" key={example.id}><span className="eyebrow">{example.title}</span><p>{example.problem}</p>{example.steps && <p>{example.steps}</p>}{example.answer && <p><strong>Resposta:</strong> {example.answer}</p>}{example.explanation && <p>{example.explanation}</p>}</section>) : paragraphs(lesson.examples).map((example, exampleIndex) => <section className="worked-example" key={`${lesson.id}-${exampleIndex}`}><span className="eyebrow">EXEMPLO {exampleIndex + 1}</span><p>{example}</p></section>)}{lesson.joint_activity && <section><h3>Façam juntos</h3><p>{lesson.joint_activity}</p></section>}{lesson.common_mistakes && <section><h3>Erros comuns</h3><p>{lesson.common_mistakes}</p></section>}{lesson.parent_tip && <section><h3>Dica para o responsável</h3><p>{lesson.parent_tip}</p></section>}{lesson.summary && <section><h3>Resumo</h3><p>{lesson.summary}</p></section>}</article>)}</div> : <div className="empty-state card"><h3>Este conteúdo ainda não possui explicação cadastrada.</h3></div>}</section>
    <section className="education-section reading-section"><div className="section-heading"><div><span className="eyebrow">PRATIQUE</span><h2>Exercícios</h2></div></div>{exercises.length ? <div className="exercise-list">{exercises.map((exercise, exerciseIndex) => { const Component = exerciseComponents[exercise.exercise_type]; return Component ? <div key={exercise.id}><span className="eyebrow exercise-number">QUESTÃO {exerciseIndex + 1}</span><Component exercise={exercise} onAnswered={refreshProgress} /></div> : null; })}</div> : <div className="empty-state card"><h3>Nenhum exercício disponível neste momento.</h3></div>}</section>
    <nav className="topic-footer-nav" aria-label="Conteúdos da matéria">{previous ? <Link className="button secondary-button" to={`/learn/topic/${previous.id}`} state={context}>← Conteúdo anterior</Link> : <span />}<Link to={`/learn/subject/${gradeSubjectId}`} state={context}>Voltar para {subjectName}</Link>{next ? <Link className="button" to={`/learn/topic/${next.id}`} state={context}>Próximo conteúdo →</Link> : <span />}</nav>
  </>}</EducationState></section>;
}
