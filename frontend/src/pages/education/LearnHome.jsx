import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import EducationState from "../../components/education/EducationState";
import SubjectCard from "../../components/education/SubjectCard";
import { collection, educationApi } from "../../services/education";

const emptyForm = { name: "", education_level: "", grade: "" };

export default function LearnHome() {
  const [children, setChildren] = useState([]); const [levels, setLevels] = useState([]); const [grades, setGrades] = useState([]); const [subjects, setSubjects] = useState([]);
  const [selectedId, setSelectedId] = useState(""); const [form, setForm] = useState(emptyForm); const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false); const [error, setError] = useState(""); const [formError, setFormError] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const selected = useMemo(() => children.find((child) => String(child.id) === String(selectedId)), [children, selectedId]);
  const availableGrades = useMemo(() => grades.filter((grade) => String(grade.education_level) === String(form.education_level)), [grades, form.education_level]);

  const load = useCallback(async (preferredId) => {
    setLoading(true); setError("");
    try {
      const [childResponse, levelResponse, gradeResponse] = await Promise.all([educationApi.getChildren(), educationApi.getLevels(), educationApi.getGrades()]);
      const childList = collection(childResponse).filter((child) => child.active); const levelList = collection(levelResponse); const gradeList = collection(gradeResponse);
      const stored = preferredId || localStorage.getItem("study_active_child");
      const current = childList.find((child) => String(child.id) === String(stored)) || childList[0];
      setChildren(childList); setLevels(levelList); setGrades(gradeList); setSelectedId(current ? String(current.id) : "");
      if (current) {
        localStorage.setItem("study_active_child", current.id);
        setForm({ name: current.name, education_level: current.education_level || "", grade: current.grade || "" });
        setSubjects(current.education_level && current.grade ? collection(await educationApi.getChildSubjects(current.id)) : []);
      } else { setForm(emptyForm); setSubjects([]); }
    } catch { setError("Não foi possível carregar a área de aprendizado."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);

  const changeChild = (id) => { localStorage.setItem("study_active_child", id); setSelectedId(id); load(id); };
  const save = async (event) => {
    event.preventDefault(); setSaving(true); setFormError("");
    const payload = { name: form.name.trim(), education_level: Number(form.education_level), grade: Number(form.grade), active: true };
    try {
      const response = selected ? await educationApi.updateChild(selected.id, payload) : await educationApi.createChild(payload);
      localStorage.setItem("study_active_child", response.data.id); await load(response.data.id);
    } catch (requestError) { setFormError(requestError.response?.data?.grade?.[0] || "Não foi possível salvar o perfil escolar."); }
    finally { setSaving(false); }
  };

  const incomplete = selected && (!selected.education_level || !selected.grade);
  return <section className="page-content education-page"><EducationState loading={loading} error={error} loadingText="Preparando a área de aprendizado..." onRetry={load}>
    {!children.length ? <><header className="page-hero"><div><span className="eyebrow">APRENDER</span><h1>Antes de começar</h1><p>Cadastre seu filho para organizarmos as matérias e conteúdos de acordo com a etapa escolar.</p></div></header>{showCreate ? <SchoolForm form={form} setForm={setForm} levels={levels} grades={availableGrades} onSubmit={save} saving={saving} error={formError} submitLabel="Cadastrar filho" /> : <div className="empty-state card learn-start"><h3>Uma experiência de aprendizado para cada etapa escolar</h3><p>Você poderá acompanhar matérias, conteúdos, exercícios e progresso.</p><button onClick={() => setShowCreate(true)}>Cadastrar filho</button></div>}</>
    : incomplete ? <><header className="page-hero"><div><span className="eyebrow">APRENDER</span><h1>Complete o perfil escolar</h1><p>Para organizar os estudos de {selected.name}, informe a etapa escolar atual.</p></div></header><SchoolForm form={form} setForm={setForm} levels={levels} grades={availableGrades} onSubmit={save} saving={saving} error={formError} submitLabel="Salvar e continuar" hideName /></>
    : <><header className="page-hero learn-heading"><div><span className="eyebrow">APRENDER</span><h1>Matérias de {selected.name}</h1><p>Conteúdos organizados para {selected.grade_name}.</p></div>{children.length > 1 && <label className="support-child-select">Estudando com:<select value={selectedId} onChange={(event) => changeChild(event.target.value)}>{children.map((child) => <option key={child.id} value={child.id}>{child.name} — {child.grade_name || "Perfil incompleto"}</option>)}</select></label>}</header>{subjects.length ? <div className="education-grid">{subjects.map((item) => <SubjectCard key={item.id} link={item} grade={{ id: selected.grade, name: selected.grade_name }} />)}</div> : <div className="empty-state card"><h3>Nenhuma matéria cadastrada para esta série.</h3><p>Confira o currículo ou atualize a escolaridade do filho.</p><Link className="button secondary-button" to="/children">Gerenciar filhos</Link></div>}</>}
  </EducationState></section>;
}

function SchoolForm({ form, setForm, levels, grades, onSubmit, saving, error, submitLabel, hideName = false }) {
  return <form className="card learn-onboarding" onSubmit={onSubmit}>{!hideName && <label>Nome do filho<input required maxLength="150" value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} /></label>}<label>Nível de escolaridade<select required value={form.education_level} onChange={(event) => setForm({ ...form, education_level: event.target.value, grade: "" })}><option value="">Selecionar</option>{levels.map((level) => <option key={level.id} value={level.id}>{level.name}</option>)}</select></label><label>Série/Ano<select required disabled={!form.education_level} value={form.grade} onChange={(event) => setForm({ ...form, grade: event.target.value })}><option value="">Selecionar</option>{grades.map((grade) => <option key={grade.id} value={grade.id}>{grade.name}</option>)}</select></label>{error && <p className="auth-error">{error}</p>}<div className="settings-actions"><button disabled={saving}>{saving ? "Salvando..." : submitLabel}</button></div></form>;
}
