import React, { useCallback, useEffect, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import Breadcrumb from "../../components/education/Breadcrumb";
import EducationState from "../../components/education/EducationState";
import SubjectCard from "../../components/education/SubjectCard";
import { collection, educationApi } from "../../services/education";

export default function GradePage() {
  const { gradeId } = useParams(); const location = useLocation(); const [grade, setGrade] = useState(location.state?.grade); const [level, setLevel] = useState(location.state?.level); const [subjects, setSubjects] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState("");
  const load = useCallback(() => { setLoading(true); setError(""); Promise.all([educationApi.getGrades(), educationApi.getLevels(), educationApi.getGradeSubjects(gradeId)]).then(([gradeResponse, levelResponse, subjectResponse]) => { const selectedGrade = collection(gradeResponse).find((item) => String(item.id) === gradeId); const selectedLevel = collection(levelResponse).find((item) => item.id === selectedGrade?.education_level); setGrade(selectedGrade); setLevel(selectedLevel); setSubjects(collection(subjectResponse)); if (!selectedGrade) setError("Não foi possível encontrar esta série."); }).catch(() => setError("Não foi possível carregar as matérias.")).finally(() => setLoading(false)); }, [gradeId]); useEffect(load, [load]);
  return <section className="page-content education-page"><Breadcrumb items={[{ label: level?.name, to: level && `/learn/level/${level.id}`, state: { level } }, { label: grade?.name }]} /><header className="page-hero"><div><span className="eyebrow">{grade?.name || "SÉRIE"}</span><h1>Matérias</h1><p>Escolha uma matéria para acessar suas unidades e conteúdos.</p></div></header><EducationState loading={loading} error={error} loadingText="Carregando matérias..." onRetry={load}>{subjects.length ? <div className="education-grid">{subjects.map((link) => <SubjectCard key={link.id} link={link} grade={grade} />)}</div> : <div className="empty-state card"><h3>Nenhuma matéria cadastrada para esta série.</h3></div>}</EducationState></section>;
}
