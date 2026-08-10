import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import EducationState from "../../components/education/EducationState";
import { collection, educationApi } from "../../services/education";

export default function SupportPage() {
  const [children, setChildren] = useState([]);
  const [childId, setChildId] = useState(localStorage.getItem("study_active_child") || "");
  const [subjects, setSubjects] = useState([]);
  const [subjectId, setSubjectId] = useState("");
  const [units, setUnits] = useState([]);
  const [topics, setTopics] = useState([]);
  const [topicId, setTopicId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true); setError("");
    educationApi.getChildren().then((response) => {
      const available = collection(response).filter((child) => child.active && child.grade);
      setChildren(available);
      const selected = available.find((child) => String(child.id) === String(childId)) || available[0];
      if (selected) { setChildId(String(selected.id)); localStorage.setItem("study_active_child", selected.id); }
    }).catch(() => setError("Não foi possível carregar seus filhos.")).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!childId) { setSubjects([]); return; }
    setLoading(true); setError(""); setSubjectId(""); setTopicId(""); setUnits([]); setTopics([]);
    localStorage.setItem("study_active_child", childId);
    educationApi.getChildSubjects(childId).then((response) => setSubjects(collection(response)))
      .catch(() => setError("Não foi possível carregar as matérias deste filho."))
      .finally(() => setLoading(false));
  }, [childId]);

  const child = children.find((item) => String(item.id) === String(childId));
  const selectedSubject = subjects.find((item) => String(item.id) === String(subjectId));
  useEffect(() => {
    if (!selectedSubject || !child) { setUnits([]); setTopics([]); setTopicId(""); return; }
    setLoading(true); setError(""); setTopicId("");
    Promise.all([educationApi.getUnits(selectedSubject.subject.id, child.grade), educationApi.getTopics()])
      .then(([unitResponse, topicResponse]) => {
        const availableUnits = collection(unitResponse); const ids = new Set(availableUnits.map((unit) => unit.id));
        setUnits(availableUnits); setTopics(collection(topicResponse).filter((topic) => ids.has(topic.unit)));
      }).catch(() => setError("Não foi possível carregar os conteúdos desta matéria."))
      .finally(() => setLoading(false));
  }, [selectedSubject?.id, child?.id]);

  const groupedTopics = useMemo(() => units.map((unit) => ({ ...unit, topics: topics.filter((topic) => topic.unit === unit.id) })), [units, topics]);
  return <section className="page-content teaching-page"><header className="page-hero"><div><span className="eyebrow">AULA DE APOIO</span><h1>Ensinar</h1><p>Escolha livremente o conteúdo que deseja ensinar ao seu filho.</p></div></header>
    <EducationState loading={loading} error={error} loadingText="Preparando conteúdos...">
      {!children.length ? <div className="empty-state card"><h3>Cadastre um filho primeiro.</h3><p>A aula de apoio é organizada conforme a série atual.</p><Link className="button" to="/settings">Adicionar filho</Link></div> : <section className="card support-picker">
        <div className="support-picker-fields"><label>Filho<select value={childId} onChange={(event) => setChildId(event.target.value)}>{children.map((item) => <option key={item.id} value={item.id}>{item.name} — {item.grade_name}</option>)}</select></label><label>Matéria<select value={subjectId} onChange={(event) => setSubjectId(event.target.value)}><option value="">Selecionar matéria</option>{subjects.map((item) => <option key={item.id} value={item.id}>{item.subject.name}</option>)}</select></label><label>Conteúdo<select value={topicId} disabled={!subjectId} onChange={(event) => setTopicId(event.target.value)}><option value="">Selecionar conteúdo</option>{groupedTopics.map((unit) => <optgroup key={unit.id} label={unit.title}>{unit.topics.map((topic) => <option key={topic.id} value={topic.id}>{topic.title}</option>)}</optgroup>)}</select></label></div>
        {subjectId && !topics.length && <p className="muted">Esta matéria ainda não possui conteúdos cadastrados para a série.</p>}
        <div className="settings-actions"><Link aria-disabled={!topicId} className={`button${topicId ? "" : " disabled-link"}`} to={topicId ? `/support/${topicId}` : "#"} state={{ child, subject: selectedSubject?.subject }}>Ensinar</Link></div>
      </section>}
    </EducationState>
  </section>;
}
