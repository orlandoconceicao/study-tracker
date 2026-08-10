import React, { useCallback, useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import Breadcrumb from "../../components/education/Breadcrumb";
import EducationCard from "../../components/education/EducationCard";
import EducationState from "../../components/education/EducationState";
import { collection, educationApi } from "../../services/education";

export default function LevelPage() {
  const { levelId } = useParams(); const location = useLocation(); const [level, setLevel] = useState(location.state?.level); const [grades, setGrades] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = useCallback(() => { setLoading(true); setError(""); Promise.all([educationApi.getLevels(), educationApi.getGrades()]).then(([levelsResponse, gradesResponse]) => { const selected = collection(levelsResponse).find((item) => String(item.id) === levelId); setLevel(selected); setGrades(collection(gradesResponse).filter((grade) => String(grade.education_level) === levelId)); if (!selected) setError("Não foi possível encontrar este nível de ensino."); }).catch(() => setError("Não foi possível carregar as séries.")).finally(() => setLoading(false)); }, [levelId]);
  useEffect(load, [load]);
  return <section className="page-content education-page"><Breadcrumb items={[{ label: level?.name }]} /><header className="page-hero"><div><span className="eyebrow">{level?.name || "NÍVEL DE ENSINO"}</span><h1>Escolha sua série</h1><p>Selecione a série para ver as matérias disponíveis.</p></div></header><EducationState loading={loading} error={error} loadingText="Carregando séries..." onRetry={load}>{grades.length ? <div className="education-grid grade-grid">{grades.map((grade) => <EducationCard key={grade.id} title={grade.name} to={`/learn/grade/${grade.id}`} state={{ grade, level }} action="Ver matérias" />)}</div> : <div className="empty-state card"><h3>Nenhuma série cadastrada para este nível.</h3></div>}</EducationState></section>;
}
