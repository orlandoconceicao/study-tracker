import React, { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import Breadcrumb from "../../components/education/Breadcrumb";
import EducationState from "../../components/education/EducationState";
import LessonItem from "../../components/education/LessonItem";
import MultipleChoiceExercise from "../../components/education/MultipleChoiceExercise";
import ProgressBar from "../../components/education/ProgressBar";
import ShortAnswerExercise from "../../components/education/ShortAnswerExercise";
import TrueFalseExercise from "../../components/education/TrueFalseExercise";
import { collection, educationApi } from "../../services/education";

const exerciseComponents = { multiple_choice: MultipleChoiceExercise, true_false: TrueFalseExercise, short_answer: ShortAnswerExercise };
const difficultyLabels = { easy: "Fácil", medium: "Médio", hard: "Difícil" };
const completedLessons = () => { try { return JSON.parse(sessionStorage.getItem("education_completed_lessons") || "[]"); } catch { return []; } };

export default function TopicPage() {
  const { topicId } = useParams(); const location = useLocation(); const context = location.state || {};
  const [topic, setTopic] = useState(null); const [lessons, setLessons] = useState([]); const [exercises, setExercises] = useState([]);
  const [progress, setProgress] = useState(null); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const refreshProgress = useCallback(() => educationApi.getTopicProgress(topicId).then((response) => setProgress(collection(response).find((item) => String(item.topic) === topicId) || null)).catch(() => {}), [topicId]);
  const load = useCallback(() => { setLoading(true); setError(""); Promise.all([educationApi.getTopic(topicId), educationApi.getTopicLessons(topicId), educationApi.getTopicExercises(topicId), educationApi.getTopicProgress(topicId)]).then(([topicResponse, lessonResponse, exerciseResponse, progressResponse]) => { setTopic(topicResponse.data); setLessons(collection(lessonResponse)); setExercises(collection(exerciseResponse)); setProgress(collection(progressResponse).find((item) => String(item.topic) === topicId) || null); }).catch(() => setError("Não foi possível carregar este conteúdo.")).finally(() => setLoading(false)); }, [topicId]);
  useEffect(load, [load]);
  const lessonContext = { ...context, topic, lessons }; const completed = completedLessons();
  return <section className="page-content education-page"><Breadcrumb items={[{ label: context.grade?.name, to: context.grade && `/learn/grade/${context.grade.id}`, state: { grade: context.grade } }, { label: context.gradeSubject?.subject.name, to: context.gradeSubject && `/learn/subject/${context.gradeSubject.id}`, state: context }, { label: topic?.title }]} /><EducationState loading={loading} error={error} loadingText="Carregando conteúdo..." onRetry={load}>{topic && <>
    <header className="topic-hero card"><span className="eyebrow">{context.unit?.title || "CONTEÚDO"}</span><h1>{topic.title}</h1>{topic.description && <p>{topic.description}</p>}<div className="topic-meta"><span className={`difficulty ${topic.difficulty}`}>{difficultyLabels[topic.difficulty] || topic.difficulty}</span>{topic.estimated_minutes > 0 && <span>{topic.estimated_minutes} min</span>}</div><ProgressBar value={progress?.completion_percentage} /><div className="topic-actions"><Link className="button" to={`/support/${topic.id}`} state={context}>Ensinar</Link><Link className="button secondary-button" to={`/learn/topic/${topic.id}/diagnostic`} state={{ ...context, topic }}>Diagnóstico opcional</Link></div></header>
    <section className="education-section"><div className="section-heading"><div><span className="eyebrow">APRENDA</span><h2>Aulas</h2></div></div>{lessons.length ? <ol className="lesson-list card">{lessons.map((lesson, index) => <LessonItem key={lesson.id} lesson={lesson} index={index} completed={completed.includes(lesson.id)} context={lessonContext} />)}</ol> : <div className="empty-state card"><h3>Nenhuma aula disponível para este conteúdo.</h3></div>}</section>
    <section className="education-section"><div className="section-heading"><div><span className="eyebrow">PRATIQUE</span><h2>Exercícios</h2></div></div>{exercises.length ? <div className="exercise-list">{exercises.map((exercise) => { const Component = exerciseComponents[exercise.exercise_type]; return Component ? <Component key={exercise.id} exercise={exercise} onAnswered={refreshProgress} /> : null; })}</div> : <div className="empty-state card"><h3>Nenhum exercício disponível neste momento.</h3></div>}</section>
  </>}</EducationState></section>;
}
