import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useLocation, useParams } from "react-router-dom";
import Breadcrumb from "../../components/education/Breadcrumb";
import EducationState from "../../components/education/EducationState";
import UnitSection from "../../components/education/UnitSection";
import { collection, educationApi } from "../../services/education";

export default function SubjectPage() {
  const { gradeSubjectId } = useParams();
  const location = useLocation();
  const [link, setLink] = useState(location.state?.gradeSubject);
  const [grade, setGrade] = useState(location.state?.grade);
  const [units, setUnits] = useState([]);
  const [topics, setTopics] = useState([]);
  const [progress, setProgress] = useState([]);
  const [query, setQuery] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [unitFilter, setUnitFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      let selectedLink = location.state?.gradeSubject;
      let selectedGrade = location.state?.grade;
      if (!selectedLink) {
        const grades = collection(await educationApi.getGrades());
        const responses = await Promise.all(grades.map((item) => educationApi.getGradeSubjects(item.id)));
        grades.some((item, index) => {
          const found = collection(responses[index]).find((candidate) => String(candidate.id) === gradeSubjectId);
          if (!found) return false;
          selectedLink = found;
          selectedGrade = item;
          return true;
        });
      }
      if (!selectedLink) throw new Error("missing");
      const [unitResponse, topicResponse, progressResponse] = await Promise.all([
        educationApi.getUnits(selectedLink.subject.id, selectedGrade.id),
        educationApi.getTopics({ grade_subject: selectedLink.id }),
        educationApi.getEducationProgress({ grade_subject: selectedLink.id }),
      ]);
      setLink(selectedLink);
      setGrade(selectedGrade);
      setUnits(collection(unitResponse));
      setTopics(collection(topicResponse));
      setProgress(collection(progressResponse));
    } catch {
      setError("Não foi possível carregar este conteúdo.");
    } finally {
      setLoading(false);
    }
  }, [gradeSubjectId, location.state]);

  useEffect(() => { load(); }, [load]);

  const filteredTopics = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("pt-BR");
    return topics.filter((topic) => {
      const matchesText = !normalized || `${topic.title} ${topic.description || ""}`.toLocaleLowerCase("pt-BR").includes(normalized);
      const matchesDifficulty = !difficulty || topic.difficulty === difficulty;
      const matchesUnit = !unitFilter || String(topic.unit) === unitFilter;
      return matchesText && matchesDifficulty && matchesUnit;
    });
  }, [topics, query, difficulty, unitFilter]);

  const progressByTopic = Object.fromEntries(progress.map((item) => [item.topic, item]));
  const context = { gradeSubject: link, grade };

  return <section className="page-content education-page">
    <Breadcrumb items={[{ label: grade?.name, to: grade && `/learn/grade/${grade.id}`, state: { grade } }, { label: link?.subject.name }]} />
    <header className="page-hero"><div><span className="eyebrow">{grade?.name || "MATÉRIA"}</span><h1>{link?.subject.name || "Unidades"}</h1><p>{link?.subject.description || "Explore as unidades e escolha um conteúdo para estudar."}</p></div></header>
    <EducationState loading={loading} error={error} loadingText="Carregando unidades..." onRetry={load}>
      {units.length ? <>
        <div className="card education-filters" role="search">
          <label>Pesquisar conteúdo<input type="search" placeholder="Pesquisar conteúdo..." value={query} onChange={(event) => setQuery(event.target.value)} /></label>
          <label>Unidade<select value={unitFilter} onChange={(event) => setUnitFilter(event.target.value)}><option value="">Todas</option>{units.map((unit) => <option key={unit.id} value={unit.id}>{unit.title}</option>)}</select></label>
          <label>Dificuldade<select value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option value="">Todas</option><option value="easy">Fácil</option><option value="medium">Médio</option><option value="hard">Desafio</option></select></label>
        </div>
        {filteredTopics.length ? <div className="unit-stack">{units.filter((unit) => !unitFilter || String(unit.id) === unitFilter).map((unit) => {
          const unitTopics = filteredTopics.filter((topic) => topic.unit === unit.id);
          return unitTopics.length ? <UnitSection key={unit.id} unit={unit} topics={unitTopics} progressByTopic={progressByTopic} context={{ ...context, unit }} /> : null;
        })}</div> : <div className="empty-state card"><h3>Nenhum conteúdo encontrado.</h3><p>Tente outro termo ou remova os filtros.</p></div>}
      </> : <div className="empty-state card"><h3>Nenhum conteúdo disponível para esta matéria.</h3></div>}
    </EducationState>
  </section>;
}
